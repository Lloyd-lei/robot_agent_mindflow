#!/usr/bin/env python3
"""
语音交互 Agent 主程序
完整的语音交互闭环：录音 → VAD → ASR → LLM → TTS → 播放
"""
import sys
from pathlib import Path
import pyaudio
import numpy as np
import wave
import time
from colorama import Fore, Style, init

from conversation_session import ConversationSession
from asr_interface import OpenAIASR
from voice_feedback import VoiceWaitingFeedback
import config

init(autoreset=True)


class SimpleVAD:
    """简化的 VAD（基于能量检测）"""
    
    def __init__(self, energy_threshold: float = 1100.0, silence_duration_ms: int = 900, frame_duration_ms: int = 30):
        self.energy_threshold = energy_threshold
        self.silence_duration_ms = silence_duration_ms
        self.num_silence_frames = int(silence_duration_ms / frame_duration_ms)
    
    def is_speech(self, audio_data: bytes) -> tuple[bool, float]:
        """判断是否为语音"""
        samples = np.frombuffer(audio_data, dtype=np.int16)
        energy = np.sqrt(np.mean(samples.astype(np.float32) ** 2))
        return energy > self.energy_threshold, energy


class VoiceRecorder:
    """语音录音器（带 VAD）"""
    
    def __init__(self, vad: SimpleVAD, sample_rate: int = 16000, chunk_size: int = 480):
        self.vad = vad
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.audio = pyaudio.PyAudio()
        self.stream = None
    
    def record_until_silence(self, max_duration: float = 30.0) -> tuple[bytes, dict]:
        """录音直到检测到静音"""
        print(f"{Fore.YELLOW}🎤 正在监听...（请说话）\n")
        
        try:
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
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
        energies = []
        
        try:
            while True:
                if time.time() - start_time > max_duration:
                    break
                
                try:
                    frame = self.stream.read(self.chunk_size, exception_on_overflow=False)
                except Exception as e:
                    print(f"\n{Fore.RED}❌ 读取音频失败: {e}")
                    break
                
                is_speech, energy = self.vad.is_speech(frame)
                energies.append(energy)
                max_energy = max(max_energy, energy)
                
                # 显示能量条
                bar_length = int(min(energy / 50, 40))
                bar = "█" * bar_length
                status = "🗣️" if is_speech else "🔇"
                print(f"\r{Fore.GREEN if is_speech else Fore.YELLOW}能量: {energy:7.1f} |{bar:<40}| {status}", end='', flush=True)
                
                if not speech_started:
                    if is_speech:
                        speech_started = True
                        audio_frames.append(frame)
                        silence_frames = 0
                        print(f"\n{Fore.GREEN}✅ 开始录音...\n")
                else:
                    audio_frames.append(frame)
                    if is_speech:
                        silence_frames = 0
                    else:
                        silence_frames += 1
                        if silence_frames >= self.vad.num_silence_frames:
                            print(f"\n{Fore.GREEN}✅ 检测到静音，停止录音\n")
                            break
        
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}⚠️  用户中断")
        
        finally:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
        
        audio_data = b''.join(audio_frames)
        duration = len(audio_data) / (self.sample_rate * 2)
        
        stats = {
            'duration': duration,
            'frames': len(audio_frames),
            'max_energy': max_energy,
            'avg_energy': np.mean(energies) if energies else 0,
            'speech_started': speech_started
        }
        
        return audio_data, stats
    
    def save_wav(self, audio_data: bytes, filename: str):
        """保存为 WAV 文件"""
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_data)
    
    def cleanup(self):
        """清理资源"""
        if self.stream:
            self.stream.close()
        if self.audio:
            self.audio.terminate()


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print(Fore.CYAN + Style.BRIGHT + "🎤 语音交互 AI Agent")
    print("=" * 80 + "\n")
    
    # 询问用户是否戴耳机
    print(f"{Fore.YELLOW}请选择麦克风类型：")
    print(f"  1. AirPods Pro / 蓝牙耳机 (推荐阈值: 1100)")
    print(f"  2. MacBook Pro 内置麦克风 (推荐阈值: 300)")
    
    choice = input(f"\n{Fore.YELLOW}请输入选项 (1/2，默认1): {Style.RESET_ALL}").strip()
    
    if choice == "2":
        vad_threshold = 300.0
        mic_type = "MacBook Pro 内置麦克风"
    else:
        vad_threshold = 1100.0
        mic_type = "AirPods Pro / 蓝牙耳机"
    
    print(f"\n{Fore.GREEN}✅ 已选择: {mic_type}\n")
    
    # 初始化 VAD
    vad = SimpleVAD(energy_threshold=vad_threshold, silence_duration_ms=700)
    print(f"{Fore.GREEN}✅ VAD 初始化: 阈值={vad_threshold}, 静音=900ms\n")
    
    # 初始化录音器
    recorder = VoiceRecorder(vad)
    
    # 初始化 ASR
    print(f"{Fore.CYAN}⏳ 初始化 ASR...")
    asr = OpenAIASR(api_key=config.OPENAI_API_KEY, model="whisper-1")
    print(f"{Fore.GREEN}✅ ASR 初始化完成\n")
    
    # 初始化 ConversationSession（LLM + TTS）
    print(f"{Fore.CYAN}⏳ 初始化 LLM + TTS...")
    session = ConversationSession(
        llm_model=config.LLM_MODEL,
        tts_provider="openai",
        tts_voice="shimmer",
        enable_cache=True,
        show_reasoning=True,
        timeout=60,
        tts_wait_timeout=60,
        voice_mode=True  # ✅ 启用语音模式（工具调用音效）
    )
    session.start()
    
    print(f"{Fore.GREEN}✅ LLM + TTS 初始化完成")
    print(f"{Fore.GREEN}✅ 音效系统已启用\n")
    
    # 创建临时目录
    temp_dir = Path("temp_audio")
    temp_dir.mkdir(exist_ok=True)
    
    round_num = 0
    
    try:
        while True:
            round_num += 1
            print(f"\n{Fore.MAGENTA}{'='*80}")
            print(f"{Fore.MAGENTA}🔄 对话轮次 {round_num}")
            print(f"{Fore.MAGENTA}{'='*80}\n")
            
            # 1. 录音（带 VAD）
            audio_data, stats = recorder.record_until_silence(max_duration=30.0)
            
            if not audio_data or not stats.get('speech_started'):
                print(f"{Fore.RED}⚠️  未检测到有效语音\n")
                continue
            
            # 2. 保存音频
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            audio_file = temp_dir / f"recording_{timestamp}.wav"
            recorder.save_wav(audio_data, str(audio_file))
            print(f"{Fore.GREEN}💾 已保存: {audio_file}\n")
            
            # 3. ASR 识别
            print(f"{Fore.CYAN}🔄 正在识别...\n")
            asr_start = time.time()
            result = asr.transcribe(str(audio_file))
            asr_time = time.time() - asr_start
            
            if not result.text:
                print(f"{Fore.RED}❌ ASR 识别失败\n")
                continue
            
            print(f"{Fore.GREEN}📝 识别结果: {Fore.WHITE}{result.text}")
            print(f"{Fore.GREEN}🌍 语言: {Fore.WHITE}{result.language}\n")
            
            # 4. LLM 推理 + TTS 播放
            print(f"{Fore.CYAN}🧠 LLM 推理中...\n")
            
            session_result = session.chat(result.text)
            
            if session_result.should_end:
                print(f"\n{Fore.YELLOW}👋 检测到对话结束，再见！\n")
                break
            
            print(f"\n{Fore.GREEN}✅ 对话轮次 {round_num} 完成\n")
    
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}⚠️  用户中断，再见！\n")
    
    finally:
        # 清理资源
        print(f"{Fore.CYAN}🧹 清理资源...\n")
        recorder.cleanup()
        session.end()
        print(f"{Fore.GREEN}✅ 程序结束\n")


if __name__ == "__main__":
    main()
