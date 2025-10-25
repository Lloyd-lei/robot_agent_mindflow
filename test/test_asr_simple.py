#!/usr/bin/env python3
"""
ASR 简单测试脚本
快速测试 ASR 准确性和速度
"""
from asr_interface import OpenAIASR
from pathlib import Path
import time


def test_asr_quick():
    """快速测试 ASR"""
    print("=" * 80)
    print("🎤 OpenAI Whisper ASR 快速测试")
    print("=" * 80)
    print()
    
    # 初始化 ASR
    print("⏳ 初始化 ASR...")
    asr = OpenAIASR(
        model="whisper-1",
        temperature=0.0
    )
    print("✅ 初始化完成\n")
    
    # 测试用例（使用已有的音频文件）
    test_files = [
        "test/outputs/openai_tts_shimmer_sample.mp3",
        "test/outputs/test_output.mp3",
        "test/outputs/openai_tts_nova_sample.mp3"
    ]
    
    # 查找存在的测试文件
    existing_files = [f for f in test_files if Path(f).exists()]
    
    if not existing_files:
        print("⚠️  未找到测试音频文件")
        print("\n💡 使用方法：")
        print("   方法1：运行交互式测试")
        print("   python test_asr_interactive.py")
        print()
        print("   方法2：指定音频文件")
        print("   python test_asr_simple.py <音频文件路径>")
        print()
        return
    
    print(f"找到 {len(existing_files)} 个测试文件\n")
    
    # 测试每个文件
    for i, file_path in enumerate(existing_files, 1):
        print(f"{'='*80}")
        print(f"测试 {i}/{len(existing_files)}: {Path(file_path).name}")
        print(f"{'='*80}")
        
        try:
            # 识别
            result = asr.transcribe(
                audio_file=file_path,
                language=None,  # 自动检测语言
                verbose=True
            )
            
            print(f"\n✅ 识别成功！")
            print(f"   文本: {result.text}")
            print(f"   语言: {result.language}")
            print(f"   速度: {result.duration / result.processing_time:.1f}x 实时")
            print()
        
        except Exception as e:
            print(f"❌ 识别失败: {e}\n")
        
        if i < len(existing_files):
            time.sleep(0.5)  # 短暂等待
    
    # 总结
    print("=" * 80)
    print("✅ 测试完成！")
    print("=" * 80)
    print()
    print("💡 完整测试请运行:")
    print("   python test_asr_interactive.py")
    print()


if __name__ == "__main__":
    import sys
    
    # 如果提供了文件路径参数
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        
        print("=" * 80)
        print(f"🎤 测试文件: {Path(file_path).name}")
        print("=" * 80)
        print()
        
        asr = OpenAIASR(temperature=0.0)
        
        try:
            result = asr.transcribe(
                audio_file=file_path,
                language=None,
                verbose=True
            )
            
            print(f"\n✅ 识别成功！")
            print(f"   完整文本: {result.text}")
            print(f"   检测语言: {result.language}")
            print(f"   音频时长: {result.duration:.2f}秒")
            print(f"   处理耗时: {result.processing_time:.2f}秒")
            print(f"   处理速度: {result.duration / result.processing_time:.1f}x 实时")
            
            cost = result.duration / 60 * 0.006
            print(f"   API 成本: ${cost:.4f} (约 ¥{cost * 7:.4f})")
            print()
        
        except Exception as e:
            print(f"❌ 识别失败: {e}\n")
            import traceback
            traceback.print_exc()
    
    else:
        # 快速测试
        test_asr_quick()

