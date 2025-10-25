#!/usr/bin/env python3
"""
ASR 交互式测试工具
支持录音测试和文件测试
"""
import sys
import time
from pathlib import Path
from colorama import Fore, Style, init
from asr_interface import OpenAIASR, ASRResult

init(autoreset=True)


def print_header():
    """打印标题"""
    print("\n" + "=" * 80)
    print(Fore.CYAN + Style.BRIGHT + "🎤 OpenAI Whisper ASR 测试工具")
    print("=" * 80)
    print(f"\n{Fore.GREEN}特性：")
    print("  ✅ 自动语言检测（98+ 种语言）")
    print("  ✅ 超高准确率（State-of-the-art）")
    print("  ✅ 支持噪音环境")
    print("  ✅ 实时性能监控")
    print("-" * 80 + "\n")


def print_result(result: ASRResult, file_name: str = ""):
    """打印识别结果"""
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.CYAN}📊 识别结果")
    print(f"{Fore.CYAN}{'='*80}")
    
    if file_name:
        print(f"\n{Fore.YELLOW}文件: {Fore.WHITE}{file_name}")
    
    print(f"\n{Fore.GREEN}识别文本:")
    print(f"{Fore.WHITE}{result.text}")
    
    print(f"\n{Fore.GREEN}详细信息:")
    print(f"  语言: {Fore.WHITE}{result.language}")
    print(f"  音频时长: {Fore.WHITE}{result.duration:.2f} 秒")
    print(f"  处理耗时: {Fore.WHITE}{result.processing_time:.2f} 秒")
    
    # 速度比（处理速度 vs 实时）
    speed_ratio = result.duration / result.processing_time if result.processing_time > 0 else 0
    if speed_ratio > 1:
        speed_color = Fore.GREEN
        speed_text = f"{speed_ratio:.1f}x 实时（快）"
    else:
        speed_color = Fore.YELLOW
        speed_text = f"{speed_ratio:.1f}x 实时（慢）"
    
    print(f"  处理速度: {speed_color}{speed_text}")
    
    # 成本估算
    cost = result.duration / 60 * 0.006  # $0.006 / 分钟
    print(f"  API 成本: {Fore.WHITE}${cost:.4f} (约 ¥{cost * 7:.4f})")
    
    print(f"\n{Fore.CYAN}{'='*80}\n")


def test_with_file(asr: OpenAIASR, file_path: str, prompt: str = None):
    """测试单个文件"""
    try:
        print(f"{Fore.YELLOW}🔄 正在识别: {Path(file_path).name}...")
        
        result = asr.transcribe(
            audio_file=file_path,
            language=None,  # 自动检测
            prompt=prompt,
            return_segments=False,
            verbose=False
        )
        
        print_result(result, Path(file_path).name)
        
        return result
    
    except FileNotFoundError:
        print(f"{Fore.RED}❌ 文件不存在: {file_path}")
        return None
    
    except Exception as e:
        print(f"{Fore.RED}❌ 识别失败: {e}")
        return None


def test_with_recording(asr: OpenAIASR, duration: int = 5, prompt: str = None):
    """测试录音"""
    try:
        import pyaudio
        import wave
        
        print(f"{Fore.YELLOW}🎤 准备录音...")
        print(f"   时长: {duration} 秒")
        print(f"   采样率: 16000 Hz")
        print(f"   格式: WAV\n")
        
        # 录音参数
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000
        
        # 初始化 PyAudio
        p = pyaudio.PyAudio()
        
        # 打开音频流
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )
        
        print(f"{Fore.GREEN}🔴 开始录音...（{duration}秒）")
        
        frames = []
        for i in range(0, int(RATE / CHUNK * duration)):
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
            
            # 显示进度
            progress = (i + 1) / (RATE / CHUNK * duration)
            bar_length = 40
            filled = int(bar_length * progress)
            bar = "█" * filled + "░" * (bar_length - filled)
            print(f"\r{Fore.YELLOW}  [{bar}] {progress * 100:.0f}%", end='', flush=True)
        
        print()  # 换行
        
        # 停止录音
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        print(f"{Fore.GREEN}✅ 录音完成")
        
        # 保存临时文件
        temp_file = Path("temp_audio") / f"test_recording_{int(time.time())}.wav"
        temp_file.parent.mkdir(exist_ok=True)
        
        with wave.open(str(temp_file), 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
        
        print(f"{Fore.CYAN}💾 已保存: {temp_file}\n")
        
        # 识别
        result = test_with_file(asr, str(temp_file), prompt)
        
        # 询问是否保留文件
        keep = input(f"\n{Fore.YELLOW}是否保留录音文件? (y/n): {Style.RESET_ALL}").lower()
        if keep != 'y':
            temp_file.unlink()
            print(f"{Fore.GREEN}✅ 已删除临时文件")
        
        return result
    
    except ImportError:
        print(f"{Fore.RED}❌ PyAudio 未安装")
        print(f"{Fore.YELLOW}请运行: pip install pyaudio")
        return None
    
    except Exception as e:
        print(f"{Fore.RED}❌ 录音失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_batch_files(asr: OpenAIASR, directory: str, prompt: str = None):
    """批量测试目录中的所有音频文件"""
    dir_path = Path(directory)
    
    if not dir_path.exists():
        print(f"{Fore.RED}❌ 目录不存在: {directory}")
        return
    
    # 查找音频文件
    audio_extensions = ['.mp3', '.wav', '.m4a', '.mp4', '.webm']
    audio_files = []
    
    for ext in audio_extensions:
        audio_files.extend(dir_path.glob(f"*{ext}"))
    
    if not audio_files:
        print(f"{Fore.YELLOW}⚠️  目录中没有找到音频文件")
        return
    
    print(f"{Fore.GREEN}找到 {len(audio_files)} 个音频文件\n")
    
    # 批量识别
    results = []
    total_duration = 0
    total_processing_time = 0
    
    for i, audio_file in enumerate(audio_files, 1):
        print(f"{Fore.CYAN}[{i}/{len(audio_files)}] {audio_file.name}")
        
        result = test_with_file(asr, str(audio_file), prompt)
        
        if result:
            results.append(result)
            total_duration += result.duration
            total_processing_time += result.processing_time
    
    # 统计
    if results:
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"{Fore.CYAN}📈 批量测试统计")
        print(f"{Fore.CYAN}{'='*80}")
        print(f"\n{Fore.GREEN}总文件数: {Fore.WHITE}{len(results)}")
        print(f"{Fore.GREEN}总音频时长: {Fore.WHITE}{total_duration:.2f} 秒")
        print(f"{Fore.GREEN}总处理耗时: {Fore.WHITE}{total_processing_time:.2f} 秒")
        print(f"{Fore.GREEN}平均速度: {Fore.WHITE}{total_duration / total_processing_time:.1f}x 实时")
        
        total_cost = total_duration / 60 * 0.006
        print(f"{Fore.GREEN}总成本: {Fore.WHITE}${total_cost:.4f} (约 ¥{total_cost * 7:.4f})")
        print(f"\n{Fore.CYAN}{'='*80}\n")


def interactive_mode(asr: OpenAIASR):
    """交互式模式"""
    while True:
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"{Fore.CYAN}选择测试模式")
        print(f"{Fore.CYAN}{'='*80}")
        print(f"\n{Fore.YELLOW}1. {Fore.WHITE}录音测试（实时录音并识别）")
        print(f"{Fore.YELLOW}2. {Fore.WHITE}文件测试（识别单个音频文件）")
        print(f"{Fore.YELLOW}3. {Fore.WHITE}批量测试（识别目录中的所有音频）")
        print(f"{Fore.YELLOW}4. {Fore.WHITE}查看支持的语言")
        print(f"{Fore.YELLOW}q. {Fore.WHITE}退出")
        
        choice = input(f"\n{Fore.CYAN}请选择 (1-4, q): {Style.RESET_ALL}").strip().lower()
        
        if choice == 'q':
            print(f"\n{Fore.GREEN}👋 再见！\n")
            break
        
        elif choice == '1':
            # 录音测试
            duration = input(f"{Fore.CYAN}录音时长（秒，默认5）: {Style.RESET_ALL}").strip()
            duration = int(duration) if duration else 5
            
            prompt = input(f"{Fore.CYAN}提示词（可选，提升专业术语识别）: {Style.RESET_ALL}").strip()
            prompt = prompt if prompt else None
            
            test_with_recording(asr, duration, prompt)
        
        elif choice == '2':
            # 文件测试
            file_path = input(f"{Fore.CYAN}音频文件路径: {Style.RESET_ALL}").strip()
            
            prompt = input(f"{Fore.CYAN}提示词（可选）: {Style.RESET_ALL}").strip()
            prompt = prompt if prompt else None
            
            test_with_file(asr, file_path, prompt)
        
        elif choice == '3':
            # 批量测试
            directory = input(f"{Fore.CYAN}音频目录路径: {Style.RESET_ALL}").strip()
            
            prompt = input(f"{Fore.CYAN}提示词（可选）: {Style.RESET_ALL}").strip()
            prompt = prompt if prompt else None
            
            test_batch_files(asr, directory, prompt)
        
        elif choice == '4':
            # 支持的语言
            languages = asr.get_supported_languages()
            print(f"\n{Fore.GREEN}支持的主要语言（共 98+ 种）:")
            for i, lang in enumerate(languages, 1):
                print(f"  {i}. {lang}")
            print(f"\n{Fore.YELLOW}注意：Whisper 支持自动检测所有这些语言！")


def main():
    """主函数"""
    print_header()
    
    # 检查是否有命令行参数
    if len(sys.argv) > 1:
        # 命令行模式
        file_path = sys.argv[1]
        prompt = sys.argv[2] if len(sys.argv) > 2 else None
        
        print(f"{Fore.GREEN}📁 文件模式")
        print(f"   文件: {file_path}")
        if prompt:
            print(f"   提示词: {prompt}")
        print()
        
        # 初始化 ASR
        asr = OpenAIASR(temperature=0.0)
        
        # 测试文件
        test_with_file(asr, file_path, prompt)
    
    else:
        # 交互式模式
        print(f"{Fore.GREEN}🎮 交互式模式\n")
        
        # 初始化 ASR
        print(f"{Fore.CYAN}⏳ 正在初始化 ASR...")
        asr = OpenAIASR(temperature=0.0)
        print(f"{Fore.GREEN}✅ 初始化完成\n")
        
        # 进入交互模式
        interactive_mode(asr)


if __name__ == "__main__":
    main()

