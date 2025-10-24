#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试所有修复是否生效
"""

from agent_hybrid import HybridReasoningAgent
import time

def test_function_call_fix():
    """测试1: Function Call 参数解析修复"""
    print("\n" + "="*70)
    print("测试1: Function Call 参数解析修复")
    print("="*70)
    
    agent = HybridReasoningAgent(
        enable_cache=True,
        enable_streaming_tts=True,
        voice_mode=False
    )
    
    # 测试工具调用
    test_query = "明天下午三点提醒我开会"
    print(f"\n测试查询: {test_query}\n")
    
    try:
        result = agent.run_with_streaming_tts(test_query, show_reasoning=False)
        
        if result['success']:
            print("\n✅ 测试通过：工具调用成功")
            print(f"   工具调用次数: {result['tool_calls']}")
            print(f"   输出: {result['output'][:100]}...")
            
            # 检查是否有工具执行错误
            if '工具执行错误' in result['output']:
                print("❌ 失败：输出中包含工具执行错误")
                return False
            else:
                print("✅ 没有工具执行错误")
                return True
        else:
            print(f"❌ 测试失败: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_audio_queue_fix():
    """测试2: 音频队列重试机制"""
    print("\n" + "="*70)
    print("测试2: 音频队列重试机制")
    print("="*70)
    
    agent = HybridReasoningAgent(
        enable_cache=True,
        enable_streaming_tts=True,
        voice_mode=False
    )
    
    # 测试长文本（会生成多个音频chunk）
    test_query = "给我详细介绍一下Python编程语言的历史和特点"
    print(f"\n测试查询: {test_query}\n")
    
    try:
        result = agent.run_with_streaming_tts(test_query, show_reasoning=False)
        
        if result['success']:
            stats = result.get('streaming_stats', {})
            
            print("\n📊 音频统计:")
            print(f"   接收文本: {stats.get('text_received', 0)}")
            print(f"   生成音频: {stats.get('audio_generated', 0)}")
            print(f"   播放完成: {stats.get('audio_played', 0)}")
            print(f"   生成失败: {stats.get('audio_failed', 0)}")
            print(f"   播放失败: {stats.get('audio_play_failed', 0)}")
            
            # 检查是否有音频被丢弃
            audio_failed = stats.get('audio_failed', 0)
            if audio_failed == 0:
                print("\n✅ 测试通过：没有音频被丢弃")
                return True
            else:
                print(f"\n⚠️  警告：{audio_failed}个音频被丢弃")
                return False
        else:
            print(f"❌ 测试失败: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_playback_state_fix():
    """测试3: 播放状态检测修复"""
    print("\n" + "="*70)
    print("测试3: 播放状态检测修复")
    print("="*70)
    
    agent = HybridReasoningAgent(
        enable_cache=True,
        enable_streaming_tts=True,
        voice_mode=False
    )
    
    # 测试中等长度文本
    test_query = "现在几点了？"
    print(f"\n测试查询: {test_query}\n")
    
    try:
        result = agent.run_with_streaming_tts(test_query, show_reasoning=False)
        
        if result['success']:
            stats = result.get('streaming_stats', {})
            
            print("\n📊 播放统计:")
            print(f"   音频播放: {stats.get('audio_played', 0)}")
            print(f"   播放失败: {stats.get('audio_play_failed', 0)}")
            
            # 检查是否有播放失败
            play_failed = stats.get('audio_play_failed', 0)
            if play_failed == 0:
                print("\n✅ 测试通过：所有音频都播放完成")
                return True
            else:
                print(f"\n❌ 失败：{play_failed}个音频播放失败")
                return False
        else:
            print(f"❌ 测试失败: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n" + "="*70)
    print("🧪 流式TTS管道 - 修复验证测试")
    print("="*70)
    
    results = []
    
    # 测试1: Function Call
    print("\n⏳ 运行测试1...")
    results.append(("Function Call 参数解析", test_function_call_fix()))
    time.sleep(2)
    
    # 测试2: 音频队列
    print("\n⏳ 运行测试2...")
    results.append(("音频队列重试机制", test_audio_queue_fix()))
    time.sleep(2)
    
    # 测试3: 播放状态
    print("\n⏳ 运行测试3...")
    results.append(("播放状态检测", test_playback_state_fix()))
    
    # 总结
    print("\n" + "="*70)
    print("📊 测试结果总结")
    print("="*70)
    
    for test_name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    print(f"\n总计: {passed_count}/{total_count} 个测试通过")
    
    if passed_count == total_count:
        print("\n🎉 所有修复验证成功！")
    else:
        print(f"\n⚠️  {total_count - passed_count} 个测试失败，需要进一步检查")
    
    print("="*70 + "\n")


if __name__ == "__main__":
    main()

