#!/usr/bin/env python3
"""
麦克风诊断工具
检测音频设备和音量
"""
import pyaudio
import numpy as np
import time
from colorama import Fore, Style, init

init(autoreset=True)


def list_audio_devices():
    """列出所有音频设备"""
    p = pyaudio.PyAudio()
    
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.CYAN}📋 可用的音频设备")
    print(f"{Fore.CYAN}{'='*80}\n")
    
    default_input = p.get_default_input_device_info()
    
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        
        if info['maxInputChannels'] > 0:  # 输入设备
            is_default = " 🎤 (默认)" if i == default_input['index'] else ""
            print(f"{Fore.GREEN}[{i}] {info['name']}{is_default}")
            print(f"     输入通道: {info['maxInputChannels']}")
            print(f"     采样率: {int(info['defaultSampleRate'])} Hz")
            print()
    
    p.terminate()
    
    return default_input['index']


def test_microphone(device_index=None, duration=5):
    """测试麦克风音量"""
    p = pyaudio.PyAudio()
    
    # 配置
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.CYAN}🎤 麦克风音量测试（{duration}秒）")
    print(f"{Fore.CYAN}{'='*80}\n")
    
    if device_index is None:
        device_index = p.get_default_input_device_info()['index']
    
    device_info = p.get_device_info_by_index(device_index)
    print(f"{Fore.GREEN}使用设备: {device_info['name']}\n")
    print(f"{Fore.YELLOW}请对着麦克风说话...\n")
    
    # 打开音频流
    try:
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=CHUNK
        )
    except Exception as e:
        print(f"{Fore.RED}❌ 打开音频流失败: {e}")
        print(f"{Fore.YELLOW}💡 请检查麦克风权限和连接")
        p.terminate()
        return
    
    print(f"{Fore.CYAN}音量监控（能量值）：")
    print(f"  - 0-100: 静音")
    print(f"  - 100-300: 环境噪音")
    print(f"  - 300-1000: 正常说话 ✅")
    print(f"  - 1000+: 大声说话\n")
    
    max_energy = 0
    min_energy = float('inf')
    energies = []
    
    # 录音并分析
    for i in range(0, int(RATE / CHUNK * duration)):
        try:
            data = stream.read(CHUNK, exception_on_overflow=False)
            
            # 计算能量
            samples = np.frombuffer(data, dtype=np.int16)
            energy = np.sqrt(np.mean(samples.astype(np.float32) ** 2))
            
            energies.append(energy)
            max_energy = max(max_energy, energy)
            min_energy = min(min_energy, energy)
            
            # 显示音量条
            bar_length = int(min(energy / 20, 50))
            bar = "█" * bar_length
            
            # 颜色根据音量变化
            if energy < 100:
                color = Fore.RED
                status = "静音"
            elif energy < 300:
                color = Fore.YELLOW
                status = "噪音"
            elif energy < 1000:
                color = Fore.GREEN
                status = "正常 ✅"
            else:
                color = Fore.CYAN
                status = "大声"
            
            print(f"\r{color}能量: {energy:6.1f} |{bar:<50}| {status}", end='', flush=True)
            
        except Exception as e:
            print(f"\n{Fore.RED}❌ 读取错误: {e}")
            break
    
    print("\n")
    
    # 停止录音
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    # 统计
    avg_energy = np.mean(energies)
    
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.CYAN}📊 统计结果")
    print(f"{Fore.CYAN}{'='*80}\n")
    
    print(f"{Fore.GREEN}最小能量: {Fore.WHITE}{min_energy:.1f}")
    print(f"{Fore.GREEN}平均能量: {Fore.WHITE}{avg_energy:.1f}")
    print(f"{Fore.GREEN}最大能量: {Fore.WHITE}{max_energy:.1f}")
    
    print(f"\n{Fore.CYAN}💡 建议的 VAD 阈值：")
    
    # 根据平均能量推荐阈值
    if avg_energy < 100:
        print(f"{Fore.RED}❌ 麦克风可能未工作或音量太小")
        print(f"   建议:")
        print(f"   1. 检查麦克风是否连接")
        print(f"   2. 检查系统音量设置")
        print(f"   3. 检查麦克风权限")
        recommended_threshold = 50
    elif avg_energy < 300:
        print(f"{Fore.YELLOW}⚠️  环境较安静，使用较低阈值")
        recommended_threshold = avg_energy * 1.5
    else:
        print(f"{Fore.GREEN}✅ 麦克风工作正常")
        recommended_threshold = avg_energy * 1.5
    
    print(f"\n{Fore.GREEN}推荐阈值: {Fore.WHITE}{recommended_threshold:.1f}")
    print(f"{Fore.YELLOW}在 main_voice.py 中设置:")
    print(f"   vad_energy_threshold={recommended_threshold:.1f}")
    
    print(f"\n{Fore.CYAN}{'='*80}\n")


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print(Fore.CYAN + Style.BRIGHT + "🎤 麦克风诊断工具")
    print("=" * 80)
    
    # 1. 列出设备
    default_device = list_audio_devices()
    
    # 2. 选择设备
    choice = input(f"\n{Fore.YELLOW}选择设备编号（直接回车使用默认）: {Style.RESET_ALL}").strip()
    
    if choice:
        try:
            device_index = int(choice)
        except ValueError:
            print(f"{Fore.RED}无效的设备编号，使用默认设备")
            device_index = default_device
    else:
        device_index = default_device
    
    # 3. 测试麦克风
    test_microphone(device_index, duration=5)


if __name__ == "__main__":
    main()

