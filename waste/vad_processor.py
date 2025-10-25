"""
VAD（语音活动检测）处理器
基于简单的能量检测实现（无需外部依赖）
优化版本：降低延迟，提升响应速度
"""
import numpy as np
import collections
import struct
from typing import Generator, Optional, Tuple
from logger_config import get_logger

logger = get_logger(__name__)


class VADProcessor:
    """
    VAD 处理器 - 检测语音活动，去除静音
    
    特性：
    - ✅ 零依赖（基于能量检测）
    - ✅ 实时检测语音开始/结束
    - ✅ 低延迟（<100ms）
    - ✅ 自适应阈值
    - ✅ 去除静音（节省 ASR 成本）
    
    原理：
    1. 计算音频帧的能量（振幅）
    2. 与阈值比较判断是否为语音
    3. 使用滑动窗口平滑判断
    4. 检测持续静音判定语音结束
    """
    
    def __init__(
        self,
        sample_rate: int = 16000,
        frame_duration_ms: int = 30,
        energy_threshold: float = 300.0,
        silence_duration_ms: int = 900,
        pre_speech_padding_ms: int = 300,
        post_speech_padding_ms: int = 300,
        auto_adjust_threshold: bool = True
    ):
        """
        初始化 VAD
        
        Args:
            sample_rate: 采样率
            frame_duration_ms: 帧长度（毫秒）
            energy_threshold: 能量阈值（自动调整时作为初始值）
            silence_duration_ms: 静音持续多久判定为结束
            pre_speech_padding_ms: 语音开始前的填充时长
            post_speech_padding_ms: 语音结束后的填充时长
            auto_adjust_threshold: 是否自动调整阈值
        """
        self.sample_rate = sample_rate
        self.frame_duration_ms = frame_duration_ms
        self.energy_threshold = energy_threshold
        self.silence_duration_ms = silence_duration_ms
        self.pre_speech_padding_ms = pre_speech_padding_ms
        self.post_speech_padding_ms = post_speech_padding_ms
        self.auto_adjust_threshold = auto_adjust_threshold
        
        # 计算帧参数
        self.frame_size = int(sample_rate * frame_duration_ms / 1000)
        self.frame_bytes = self.frame_size * 2  # 2 bytes per sample (int16)
        
        # 计算填充和静音帧数
        self.num_pre_padding_frames = int(pre_speech_padding_ms / frame_duration_ms)
        self.num_post_padding_frames = int(post_speech_padding_ms / frame_duration_ms)
        self.num_silence_frames = int(silence_duration_ms / frame_duration_ms)
        
        # 自适应阈值相关
        self.energy_history = collections.deque(maxlen=50)  # 保留最近50帧的能量
        self.noise_energy = energy_threshold  # 估计的噪音能量
        
        logger.info(f"✅ VAD 初始化成功")
        logger.info(f"   采样率: {sample_rate} Hz")
        logger.info(f"   帧长度: {frame_duration_ms} ms")
        logger.info(f"   能量阈值: {energy_threshold:.1f}")
        logger.info(f"   静音判定: {silence_duration_ms} ms")
        logger.info(f"   自适应阈值: {'开启' if auto_adjust_threshold else '关闭'}")
    
    def calculate_energy(self, frame: bytes) -> float:
        """
        计算音频帧的能量
        
        Args:
            frame: 音频帧数据（int16）
        
        Returns:
            能量值
        """
        if len(frame) != self.frame_bytes:
            return 0.0
        
        # 解析为 int16 数组
        samples = np.frombuffer(frame, dtype=np.int16)
        
        # 计算 RMS 能量
        energy = np.sqrt(np.mean(samples.astype(np.float32) ** 2))
        
        return float(energy)
    
    def is_speech(self, frame: bytes) -> bool:
        """
        判断单帧是否为语音
        
        Args:
            frame: 音频帧
        
        Returns:
            True=语音, False=静音
        """
        energy = self.calculate_energy(frame)
        
        # 记录能量历史（用于自适应阈值）
        self.energy_history.append(energy)
        
        # 自适应阈值调整
        if self.auto_adjust_threshold and len(self.energy_history) >= 10:
            # 使用历史能量的中位数作为噪音估计
            sorted_energies = sorted(self.energy_history)
            self.noise_energy = sorted_energies[len(sorted_energies) // 4]  # 25% 分位数
            
            # 动态阈值 = 噪音能量 * 3
            dynamic_threshold = self.noise_energy * 3
            threshold = max(self.energy_threshold, dynamic_threshold)
        else:
            threshold = self.energy_threshold
        
        return energy > threshold
    
    def detect_speech_boundaries(
        self,
        audio_generator: Generator[bytes, None, None]
    ) -> Generator[Tuple[bytes, bool, bool], None, None]:
        """
        实时检测语音边界（流式处理）
        
        Args:
            audio_generator: 音频帧生成器
        
        Yields:
            (frame, is_speech_start, is_speech_end)
        """
        ring_buffer = collections.deque(maxlen=self.num_pre_padding_frames)
        triggered = False
        silence_frames = 0
        
        for frame in audio_generator:
            if len(frame) != self.frame_bytes:
                continue
            
            is_speech = self.is_speech(frame)
            
            if not triggered:
                # 未触发状态：等待语音开始
                ring_buffer.append(frame)
                
                # 检查是否达到触发条件
                if is_speech:
                    triggered = True
                    silence_frames = 0
                    
                    # 输出缓冲区的帧（语音开始前的填充）
                    for buffered_frame in ring_buffer:
                        yield (buffered_frame, True, False)  # is_speech_start=True
                    
                    ring_buffer.clear()
            
            else:
                # 已触发状态：收集语音并检测结束
                if is_speech:
                    silence_frames = 0
                else:
                    silence_frames += 1
                
                # 检测静音持续时间
                if silence_frames >= self.num_silence_frames:
                    # 语音结束
                    yield (frame, False, True)  # is_speech_end=True
                    triggered = False
                    silence_frames = 0
                    ring_buffer.clear()
                else:
                    yield (frame, False, False)
    
    def extract_speech(
        self,
        audio_generator: Generator[bytes, None, None]
    ) -> Generator[bytes, None, None]:
        """
        提取语音片段（去除静音）
        
        Args:
            audio_generator: 音频帧生成器
        
        Yields:
            完整的语音片段
        """
        ring_buffer = collections.deque(maxlen=self.num_pre_padding_frames)
        triggered = False
        voiced_frames = []
        silence_frames = 0
        
        for frame in audio_generator:
            if len(frame) != self.frame_bytes:
                continue
            
            is_speech = self.is_speech(frame)
            
            if not triggered:
                # 未触发状态
                ring_buffer.append(frame)
                
                if is_speech:
                    triggered = True
                    logger.debug("🎤 检测到语音开始")
                    
                    # 添加填充
                    for buffered_frame in ring_buffer:
                        voiced_frames.append(buffered_frame)
                    
                    ring_buffer.clear()
                    silence_frames = 0
            
            else:
                # 已触发状态
                voiced_frames.append(frame)
                
                if is_speech:
                    silence_frames = 0
                else:
                    silence_frames += 1
                
                # 检测语音结束
                if silence_frames >= self.num_silence_frames:
                    logger.debug("🔇 检测到语音结束")
                    
                    # 添加后填充
                    for _ in range(self.num_post_padding_frames):
                        if len(ring_buffer) > 0:
                            voiced_frames.append(ring_buffer.popleft())
                    
                    # 输出完整的语音片段
                    yield b''.join(voiced_frames)
                    
                    # 重置
                    triggered = False
                    voiced_frames = []
                    ring_buffer.clear()
                    silence_frames = 0
        
        # 处理最后的语音片段
        if voiced_frames:
            yield b''.join(voiced_frames)
    
    def filter_silence(self, audio_data: bytes) -> bytes:
        """
        批量过滤静音（用于已录制的音频）
        
        Args:
            audio_data: 完整音频数据
        
        Returns:
            去除静音后的音频数据
        """
        frames = []
        offset = 0
        
        while offset + self.frame_bytes <= len(audio_data):
            frame = audio_data[offset:offset + self.frame_bytes]
            
            if self.is_speech(frame):
                frames.append(frame)
            
            offset += self.frame_bytes
        
        return b''.join(frames)
    
    def get_stats(self) -> dict:
        """
        获取 VAD 统计信息
        
        Returns:
            统计字典
        """
        return {
            'current_threshold': self.energy_threshold,
            'noise_energy': self.noise_energy,
            'auto_adjust': self.auto_adjust_threshold,
            'avg_energy': np.mean(list(self.energy_history)) if self.energy_history else 0
        }


