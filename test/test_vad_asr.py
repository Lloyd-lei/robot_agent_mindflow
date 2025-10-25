#!/usr/bin/env python3
"""
VAD + ASR 独立测试程序
用于调教 VAD 参数和测试 ASR 准确性
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pyaudio
import numpy as np
import wave
import time
from datetime import datetime
from colorama import Fore, Style, init
from asr_interface import OpenAIASR
import config

init(autoreset=True)


class SimpleVAD:
    """简化的 VAD（基于能量检测）"""
    
    def __init__(
        self,
        energy_threshold: float = 1100.0,
        silence_duration_ms: int = 900,
        frame_duration_ms: int = 30,
        sample_rate: int = 16000
    ):
        self.energy_threshold = energy_threshold
        self.silence_duration_ms = silence_duration_ms
        self.frame_duration_ms = frame_duration_ms
        self.sample_rate = sample_rate
        
        # 计算需要多少帧才算静音
        self.num_silence_frames = int(silence_duration_ms / frame_duration_ms)
        
        print(f"{Fore.GREEN}✅ VAD 初始化:")
        print(f"   - 能量阈值: {energy_threshold}")
        print(f"   - 静音判定: {silence_duration_ms}ms ({self.num_silence_frames}帧)")
        print(f"   - 采样率: {sample_rate}Hz\n")
    
    def is_speech(self, audio_data: bytes) -> tuple[bool, float]:
        """
        判断是否为语音
        
        Returns:
            (is_speech, energy): 是否为语音，能量值
        """
        samples = np.frombuffer(audio_data, dtype=np.int16)
        energy = np.sqrt(np.mean(samples.astype(np.float32) ** 2))
        
        is_speech = energy > self.energy_threshold
        
        return is_speech, energy


class VoiceRecorder:
    """语音录音器（带 VAD）"""
    
    def __init__(
        self,
        vad: SimpleVAD,
        sample_rate: int = 16000,
        channels: int = 1,
        chunk_size: int = 480  # 30ms @ 16kHz
    ):
        self.vad = vad
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        
        self.audio = pyaudio.PyAudio()
        self.stream = None
    
    def record_until_silence(self, max_duration: float = 30.0) -> tuple[bytes, dict]:
        """
        录音直到检测到静音
        
        Returns:
            (audio_data, stats): 音频数据和统计信息
        """
        print(f"{Fore.YELLOW}🎤 正在监听...（请说话，说完后保持安静{self.vad.silence_duration_ms}ms）\n")
        
        # 打开音频流
        try:
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
        except Exception as e:
            print(f"{Fore.RED}❌ 无法打开音频流: {e}")
            return b'', {}
        
        audio_frames = []
        silence_frames = 0
        speech_started = False
        start_time = time.time()
        
        max_energy = 0
        min_energy = float('inf')
        energies = []
        
        try:
            while True:
                # 检查超时
                if time.time() - start_time > max_duration:
                    print(f"\n{Fore.YELLOW}⏰ 达到最大录音时长 {max_duration}秒")
                    break
                
                # 读取音频帧
                try:
                    frame = self.stream.read(self.chunk_size, exception_on_overflow=False)
                except Exception as e:
                    print(f"\n{Fore.RED}❌ 读取音频失败: {e}")
                    break
                
                # VAD 检测
                is_speech, energy = self.vad.is_speech(frame)
                
                energies.append(energy)
                max_energy = max(max_energy, energy)
                min_energy = min(min_energy, energy)
                
                # 显示能量条
                bar_length = int(min(energy / 50, 50))
                bar = "█" * bar_length
                
                if is_speech:
                    color = Fore.GREEN
                    status = "🗣️ 检测到语音"
                else:
                    color = Fore.YELLOW
                    status = "🔇 静音"
                
                print(f"\r{color}能量: {energy:7.1f} |{bar:<50}| {status}", end='', flush=True)
                
                # 状态机
                if not speech_started:
                    # 等待语音开始
                    if is_speech:
                        speech_started = True
                        audio_frames.append(frame)
                        silence_frames = 0
                        print(f"\n{Fore.GREEN}✅ 开始录音...\n")
                else:
                    # 已开始录音
                    audio_frames.append(frame)
                    
                    if is_speech:
                        silence_frames = 0
                    else:
                        silence_frames += 1
                        
                        # 检测到足够长的静音
                        if silence_frames >= self.vad.num_silence_frames:
                            print(f"\n{Fore.GREEN}✅ 检测到静音，停止录音")
                            break
        
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}⚠️  用户中断")
        
        finally:
            # 关闭音频流
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
        
        # 合并音频数据
        audio_data = b''.join(audio_frames)
        duration = len(audio_data) / (self.sample_rate * 2)  # 2 bytes per sample
        
        # 统计信息
        stats = {
            'duration': duration,
            'frames': len(audio_frames),
            'min_energy': min_energy,
            'max_energy': max_energy,
            'avg_energy': np.mean(energies) if energies else 0,
            'speech_started': speech_started
        }
        
        print(f"\n{Fore.CYAN}📊 录音统计:")
        print(f"   - 时长: {duration:.2f}秒")
        print(f"   - 帧数: {len(audio_frames)}")
        print(f"   - 能量范围: {min_energy:.1f} - {max_energy:.1f}")
        print(f"   - 平均能量: {stats['avg_energy']:.1f}\n")
        
        return audio_data, stats
    
    def save_wav(self, audio_data: bytes, filename: str):
        """保存为 WAV 文件"""
        try:
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_data)
            
            print(f"{Fore.GREEN}💾 已保存: {filename}\n")
        except Exception as e:
            print(f"{Fore.RED}❌ 保存失败: {e}\n")
    
    def cleanup(self):
        """清理资源"""
        if self.stream:
            self.stream.close()
        
        if self.audio:
            self.audio.terminate()
        
        print(f"{Fore.GREEN}✅ 录音器资源已释放\n")


def test_vad_asr():
    """测试 VAD + ASR"""
    print("\n" + "=" * 80)
    print(Fore.CYAN + Style.BRIGHT + "🎤 VAD + ASR 测试程序")
    print("=" * 80 + "\n")
    
    # 配置参数
    print(f"{Fore.CYAN}📊 当前配置：")
    print(f"   - 能量阈值: {Fore.WHITE}1100.0 (AirPods Pro)")
    print(f"   - 静音判定: {Fore.WHITE}900ms")
    print(f"   - 采样率: {Fore.WHITE}16000 Hz")
    print(f"   - ASR: {Fore.WHITE}OpenAI Whisper-1\n")
    
    # 初始化 VAD
    vad = SimpleVAD(
        energy_threshold=1100.0,  # AirPods Pro
        silence_duration_ms=900,
        sample_rate=16000
    )
    
    # 初始化录音器
    recorder = VoiceRecorder(vad, sample_rate=16000)
    
    # 初始化 ASR
    print(f"{Fore.CYAN}⏳ 初始化 ASR...")
    asr = OpenAIASR(
        api_key=config.OPENAI_API_KEY,
        model="whisper-1"
    )
    print(f"{Fore.GREEN}✅ ASR 初始化完成\n")
    
    # 创建临时目录
    temp_dir = Path("temp_audio")
    temp_dir.mkdir(exist_ok=True)
    
    round_num = 0
    
    try:
        while True:
            round_num += 1
            print(f"\n{Fore.MAGENTA}{'='*80}")
            print(f"{Fore.MAGENTA}🔄 测试轮次 {round_num}")
            print(f"{Fore.MAGENTA}{'='*80}\n")
            
            # 1. 录音（带 VAD）
            audio_data, stats = recorder.record_until_silence(max_duration=30.0)
            
            if not audio_data or not stats.get('speech_started'):
                print(f"{Fore.RED}⚠️  未检测到有效语音\n")
                
                # 询问是否继续
                choice = input(f"{Fore.YELLOW}继续测试？(y/n/adjust): {Style.RESET_ALL}").strip().lower()
                
                if choice == 'n':
                    break
                elif choice == 'adjust':
                    # 调整阈值
                    new_threshold = input(f"{Fore.YELLOW}新的能量阈值（当前{vad.energy_threshold}）: {Style.RESET_ALL}").strip()
                    try:
                        vad.energy_threshold = float(new_threshold)
                        print(f"{Fore.GREEN}✅ 阈值已更新: {vad.energy_threshold}\n")
                    except ValueError:
                        print(f"{Fore.RED}❌ 无效的数值\n")
                
                continue
            
            # 2. 保存音频（可选）
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_file = temp_dir / f"recording_{timestamp}.wav"
            recorder.save_wav(audio_data, str(audio_file))
            
            # 3. ASR 识别
            print(f"{Fore.CYAN}🔄 正在识别...\n")
            
            asr_start = time.time()
            result = asr.transcribe(str(audio_file))
            asr_time = time.time() - asr_start
            
            # 4. 显示结果
            print(f"{Fore.GREEN}{'='*80}")
            print(f"{Fore.GREEN}📝 识别结果")
            print(f"{Fore.GREEN}{'='*80}\n")
            
            if result.text:
                print(f"{Fore.CYAN}文本: {Fore.WHITE}{result.text}")
                print(f"{Fore.CYAN}语言: {Fore.WHITE}{result.language}")
                print(f"{Fore.CYAN}ASR 耗时: {Fore.WHITE}{asr_time:.2f}秒")
                
                # 计算处理速度
                speed_ratio = result.duration / asr_time if asr_time > 0 else 0
                print(f"{Fore.CYAN}处理速度: {Fore.GREEN}{speed_ratio:.1f}x 实时")
                
                # 计算成本 (Whisper: $0.006/分钟)
                cost = result.duration / 60 * 0.006
                print(f"{Fore.CYAN}成本: {Fore.WHITE}${cost:.4f} (约 ¥{cost * 7:.4f})")
            else:
                print(f"{Fore.RED}❌ ASR 识别失败")
                if hasattr(result, 'error'):
                    print(f"{Fore.RED}   错误: {result.error}")
            
            print(f"\n{Fore.GREEN}{'='*80}\n")
            
            # 询问是否继续
            choice = input(f"{Fore.YELLOW}继续测试？(y/n/adjust): {Style.RESET_ALL}").strip().lower()
            
            if choice == 'n':
                break
            elif choice == 'adjust':
                # 调整阈值
                print(f"\n{Fore.CYAN}当前参数:")
                print(f"   - 能量阈值: {vad.energy_threshold}")
                print(f"   - 静音判定: {vad.silence_duration_ms}ms")
                
                new_threshold = input(f"{Fore.YELLOW}新的能量阈值（直接回车跳过）: {Style.RESET_ALL}").strip()
                if new_threshold:
                    try:
                        vad.energy_threshold = float(new_threshold)
                        print(f"{Fore.GREEN}✅ 阈值已更新: {vad.energy_threshold}")
                    except ValueError:
                        print(f"{Fore.RED}❌ 无效的数值")
                
                new_silence = input(f"{Fore.YELLOW}新的静音时长（ms，直接回车跳过）: {Style.RESET_ALL}").strip()
                if new_silence:
                    try:
                        vad.silence_duration_ms = int(new_silence)
                        vad.num_silence_frames = int(vad.silence_duration_ms / vad.frame_duration_ms)
                        print(f"{Fore.GREEN}✅ 静音时长已更新: {vad.silence_duration_ms}ms")
                    except ValueError:
                        print(f"{Fore.RED}❌ 无效的数值")
                
                print()
    
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}⚠️  测试中断\n")
    
    finally:
        # 清理资源
        print(f"{Fore.CYAN}🧹 清理资源...\n")
        recorder.cleanup()
        
        print(f"{Fore.GREEN}{'='*80}")
        print(f"{Fore.GREEN}📊 测试总结")
        print(f"{Fore.GREEN}{'='*80}\n")
        print(f"{Fore.CYAN}测试轮次: {Fore.WHITE}{round_num}")
        print(f"{Fore.CYAN}临时文件: {Fore.WHITE}{temp_dir}/")
        print(f"\n{Fore.GREEN}✅ 测试完成\n")


if __name__ == "__main__":
    test_vad_asr()

