"""
音频录音器
支持实时录音和 VAD 集成
优化版本：降低延迟，提升响应速度
"""
import pyaudio
import wave
import threading
import queue
import time
from pathlib import Path
from typing import Optional, Callable, List
from logger_config import get_logger

logger = get_logger(__name__)


class AudioRecorder:
    """
    音频录音器 - 支持实时录音和 VAD
    
    特性：
    - ✅ 实时录音（低延迟）
    - ✅ 自动检测语音结束（VAD 集成）
    - ✅ 线程安全
    - ✅ 资源自动清理
    - ✅ 支持回调函数（实时处理）
    
    优化：
    - 使用小缓冲区（30ms）降低延迟
    - 后台线程录音，不阻塞主线程
    - 队列通信，解耦录音和处理
    """
    
    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        chunk_size: int = 480,  # 30ms @ 16kHz
        format: int = pyaudio.paInt16
    ):
        """
        初始化录音器
        
        Args:
            sample_rate: 采样率（推荐 16000）
            channels: 声道数（1=单声道，推荐）
            chunk_size: 每次读取的帧数（30ms 平衡延迟和稳定性）
            format: 音频格式（int16）
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.format = format
        self.bytes_per_frame = 2  # int16 = 2 bytes
        
        # PyAudio 实例
        try:
            self.audio = pyaudio.PyAudio()
        except Exception as e:
            logger.error(f"❌ PyAudio 初始化失败: {e}")
            raise RuntimeError(
                "PyAudio 初始化失败。请确保已安装：\n"
                "  macOS: brew install portaudio && pip install pyaudio\n"
                "  Linux: sudo apt-get install portaudio19-dev && pip install pyaudio"
            )
        
        self.stream: Optional[pyaudio.Stream] = None
        self.is_recording = False
        
        # 音频队列（线程安全）
        self.audio_queue = queue.Queue(maxsize=100)  # 限制大小防止内存爆炸
        self.record_thread: Optional[threading.Thread] = None
        
        # 统计
        self.total_frames_recorded = 0
        
        logger.info(f"✅ 录音器初始化成功")
        logger.info(f"   采样率: {sample_rate} Hz")
        logger.info(f"   声道: {channels}")
        logger.info(f"   帧大小: {chunk_size} ({chunk_size / sample_rate * 1000:.0f}ms)")
    
    def start_recording(
        self,
        callback: Optional[Callable[[bytes], None]] = None
    ):
        """
        开始录音（后台线程）
        
        Args:
            callback: 音频数据回调函数（每帧调用一次）
        """
        if self.is_recording:
            logger.warning("⚠️  录音已在进行中")
            return
        
        self.is_recording = True
        self.total_frames_recorded = 0
        
        # 清空队列
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break
        
        # 打开音频流
        try:
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                stream_callback=None  # 不使用回调，使用阻塞读取
            )
        except Exception as e:
            logger.error(f"❌ 打开音频流失败: {e}")
            self.is_recording = False
            raise
        
        logger.info("🎤 开始录音...")
        
        # 启动录音线程
        self.record_thread = threading.Thread(
            target=self._record_loop,
            args=(callback,),
            daemon=True
        )
        self.record_thread.start()
    
    def _record_loop(self, callback: Optional[Callable[[bytes], None]]):
        """录音循环（内部方法，在后台线程运行）"""
        frame_count = 0
        
        try:
            while self.is_recording and self.stream:
                try:
                    # 读取音频数据（阻塞）
                    data = self.stream.read(
                        self.chunk_size,
                        exception_on_overflow=False
                    )
                    
                    frame_count += 1
                    self.total_frames_recorded += 1
                    
                    # 放入队列
                    try:
                        self.audio_queue.put(data, block=False)
                    except queue.Full:
                        logger.warning("⚠️  音频队列已满，丢弃帧")
                    
                    # 调用回调函数
                    if callback:
                        callback(data)
                
                except OSError as e:
                    if self.is_recording:
                        logger.error(f"❌ 录音错误: {e}")
                    break
        
        finally:
            logger.debug(f"录音线程结束，共录制 {frame_count} 帧")
    
    def stop_recording(self) -> bytes:
        """
        停止录音
        
        Returns:
            录制的完整音频数据
        """
        if not self.is_recording:
            logger.warning("⚠️  录音未在进行中")
            return b''
        
        self.is_recording = False
        
        # 等待线程结束
        if self.record_thread and self.record_thread.is_alive():
            self.record_thread.join(timeout=2)
        
        # 关闭音频流
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception as e:
                logger.error(f"关闭音频流错误: {e}")
            finally:
                self.stream = None
        
        # 收集所有音频数据
        audio_frames = []
        while not self.audio_queue.empty():
            try:
                audio_frames.append(self.audio_queue.get_nowait())
            except queue.Empty:
                break
        
        audio_data = b''.join(audio_frames)
        
        duration = len(audio_data) / (self.sample_rate * self.bytes_per_frame * self.channels)
        
        logger.info(f"🔇 录音停止")
        logger.info(f"   时长: {duration:.2f} 秒")
        logger.info(f"   大小: {len(audio_data) / 1024:.1f} KB")
        
        return audio_data
    
    def record_until_silence(
        self,
        vad_processor,
        max_duration: float = 30.0,
        save_path: Optional[str] = None
    ) -> bytes:
        """
        录音直到检测到静音
        
        Args:
            vad_processor: VAD 处理器
            max_duration: 最大录音时长（秒）
            save_path: 保存路径（可选）
        
        Returns:
            录制的音频数据
        """
        audio_frames = []
        silence_frames = 0
        speech_detected = False
        start_time = time.time()
        
        self.start_recording()
        
        logger.info("🎤 正在监听...（请说话）")
        
        try:
            while self.is_recording:
                # 检查超时
                if time.time() - start_time > max_duration:
                    logger.warning(f"⚠️  达到最大录音时长 {max_duration}秒，停止录音")
                    break
                
                # 获取音频帧
                try:
                    frame = self.audio_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                
                # VAD 检测
                is_speech = vad_processor.is_speech(frame)
                
                if is_speech:
                    # 检测到语音
                    if not speech_detected:
                        speech_detected = True
                        logger.info("✅ 检测到语音")
                    
                    audio_frames.append(frame)
                    silence_frames = 0
                
                else:
                    # 静音帧
                    if speech_detected:
                        # 已开始录音，记录静音
                        audio_frames.append(frame)
                        silence_frames += 1
                        
                        # 检查是否达到静音阈值
                        if silence_frames >= vad_processor.num_silence_frames:
                            logger.info("🔇 检测到持续静音，停止录音")
                            break
        
        except KeyboardInterrupt:
            logger.info("⚠️  用户中断录音")
        
        finally:
            audio_data = self.stop_recording()
        
        # 保存文件
        if save_path and audio_data:
            self.save_wav(audio_data, save_path)
        
        return audio_data
    
    def save_wav(
        self,
        audio_data: bytes,
        filename: str
    ):
        """
        保存为 WAV 文件
        
        Args:
            audio_data: 音频数据
            filename: 文件名
        """
        try:
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.audio.get_sample_size(self.format))
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_data)
            
            file_size = Path(filename).stat().st_size
            logger.info(f"💾 已保存: {filename} ({file_size / 1024:.1f}KB)")
        
        except Exception as e:
            logger.error(f"❌ 保存失败: {e}")
    
    def get_audio_frame(self, timeout: float = 1.0) -> Optional[bytes]:
        """
        获取单个音频帧（非阻塞）
        
        Args:
            timeout: 超时时间（秒）
        
        Returns:
            音频帧数据，或 None（超时）
        """
        try:
            return self.audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def get_all_frames(self) -> List[bytes]:
        """
        获取队列中的所有音频帧
        
        Returns:
            音频帧列表
        """
        frames = []
        while not self.audio_queue.empty():
            try:
                frames.append(self.audio_queue.get_nowait())
            except queue.Empty:
                break
        return frames
    
    def __del__(self):
        """清理资源"""
        if self.is_recording:
            self.stop_recording()
        
        if self.stream:
            try:
                self.stream.close()
            except:
                pass
        
        if hasattr(self, 'audio') and self.audio:
            try:
                self.audio.terminate()
            except:
                pass


def test_recorder():
    """测试录音器"""
    from vad_processor import VADProcessor
    
    print("=" * 80)
    print("🎤 音频录音器测试")
    print("=" * 80)
    print()
    
    # 初始化
    vad = VADProcessor(
        sample_rate=16000,
        energy_threshold=300.0,
        silence_duration_ms=900
    )
    
    recorder = AudioRecorder(
        sample_rate=16000,
        channels=1
    )
    
    # 录音
    print("请说话...（静音 0.9 秒后自动停止）\n")
    
    audio_data = recorder.record_until_silence(
        vad_processor=vad,
        max_duration=30.0,
        save_path="temp_audio/test_recording.wav"
    )
    
    duration = len(audio_data) / (16000 * 2)
    print(f"\n✅ 录音完成: {duration:.2f}秒, {len(audio_data)/1024:.1f}KB")
    
    # VAD 统计
    stats = vad.get_stats()
    print(f"\nVAD 统计:")
    print(f"  能量阈值: {stats['current_threshold']:.1f}")
    print(f"  噪音能量: {stats['noise_energy']:.1f}")
    print(f"  平均能量: {stats['avg_energy']:.1f}")


if __name__ == "__main__":
    test_recorder()


