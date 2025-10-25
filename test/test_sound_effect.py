#!/usr/bin/env python3
"""
测试工具调用音效功能
"""
import time
from voice_feedback import VoiceWaitingFeedback

def test_sound_effect():
    """测试音效播放"""
    print("=" * 70)
    print("🎵 测试工具调用音效")
    print("=" * 70)
    
    # 初始化音效系统
    print("\n1️⃣  初始化音效系统...")
    feedback = VoiceWaitingFeedback(mode='audio')
    
    # 测试1：播放工具调用音效（完整播放）
    print("\n2️⃣  测试完整播放（23秒）...")
    print("   （模拟工具执行时间：5秒）")
    feedback.start('tool_thinking')
    time.sleep(5)  # 模拟工具执行
    feedback.stop()
    print("   ✅ 音效已停止")
    
    time.sleep(1)
    
    # 测试2：播放并提前停止
    print("\n3️⃣  测试提前停止（播放3秒后停止）...")
    feedback.start('tool_thinking')
    time.sleep(3)  # 只播放3秒
    feedback.stop()
    print("   ✅ 音效已淡出停止")
    
    time.sleep(1)
    
    # 测试3：连续调用（模拟多个工具）
    print("\n4️⃣  测试连续调用（模拟多工具场景）...")
    for i in range(3):
        print(f"   工具 {i+1} 执行中...")
        feedback.start('tool_thinking')
        time.sleep(2)  # 每个工具2秒
        feedback.stop()
        time.sleep(0.5)  # 工具之间间隔
    print("   ✅ 连续调用测试完成")
    
    print("\n" + "=" * 70)
    print("✅ 音效测试完成！")
    print("=" * 70)
    print("\n💡 提示：")
    print("   - 音效会在工具调用时自动播放")
    print("   - 23秒的音效会循环播放，直到工具执行完成")
    print("   - 如果工具执行时间短，音效会提前淡出停止")
    print()


if __name__ == "__main__":
    test_sound_effect()

