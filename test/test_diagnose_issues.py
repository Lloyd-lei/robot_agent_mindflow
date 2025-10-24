#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
问题诊断测试
1. Function call 参数传递问题
2. 音频队列丢弃问题
3. 播放状态检测问题
"""

import time
import json
import asyncio
from streaming_tts_pipeline import create_streaming_pipeline


def test_function_call_issue():
    """测试 Function call 参数传递问题"""
    print("=" * 70)
    print("测试1: Function Call 参数传递")
    print("=" * 70)
    
    # 模拟 OpenAI 返回的工具调用
    tool_args_str = '{"task":"开会","time":"明天下午三点","priority":"high"}'
    
    print(f"\n工具参数（字符串）: {tool_args_str}")
    print(f"类型: {type(tool_args_str)}")
    
    # 解析参数
    try:
        tool_args = json.loads(tool_args_str)
        print(f"\n解析后的参数: {tool_args}")
        print(f"类型: {type(tool_args)}")
        
        # 模拟 LangChain 工具调用
        print("\n模拟工具调用:")
        print(f"  方式1: tool._run(**tool_args_str)  # ❌ 错误！")
        print(f"  方式2: tool._run(**tool_args)      # ✅ 正确！")
        
        # 测试实际调用
        from tools import ReminderTool
        tool = ReminderTool()
        
        print("\n尝试错误方式（传字符串）:")
        try:
            result = tool._run(**tool_args_str)  # 这会失败
            print(f"  结果: {result}")
        except Exception as e:
            print(f"  ❌ 错误: {e}")
        
        print("\n尝试正确方式（传字典）:")
        try:
            result = tool._run(**tool_args)  # 这应该成功
            print(f"  ✅ 结果: {result}")
        except Exception as e:
            print(f"  ❌ 错误: {e}")
            
    except Exception as e:
        print(f"❌ 解析失败: {e}")
    
    print("\n✅ Function call 测试完成\n")


def test_audio_queue_blocking():
    """测试音频队列阻塞 vs 丢弃"""
    print("=" * 70)
    print("测试2: 音频队列阻塞策略")
    print("=" * 70)
    
    class SlowTTS:
        """慢速TTS（模拟播放慢）"""
        async def synthesize(self, text: str) -> bytes:
            await asyncio.sleep(0.1)  # 生成很快
            return f"[AUDIO:{text}]".encode('utf-8')
    
    class MockPlayback:
        """模拟慢速播放"""
        def __init__(self):
            self.play_count = 0
        
        def play(self, audio_data):
            self.play_count += 1
            print(f"  🔊 开始播放第 {self.play_count} 段...")
            time.sleep(3.0)  # 播放很慢（3秒）
            print(f"  ✅ 播放完成第 {self.play_count} 段")
    
    slow_tts = SlowTTS()
    
    # 创建小队列的管道
    pipeline = create_streaming_pipeline(
        tts_engine=slow_tts,
        text_queue_size=2,
        audio_queue_size=2,  # 很小的队列
        max_tasks=5,
        verbose=True
    )
    
    pipeline.start()
    
    # 快速发送多个句子
    print("\n快速发送10个句子（生成快，播放慢）:")
    sentences = [f"这是第{i}句话。" for i in range(1, 11)]
    
    start_time = time.time()
    for i, sentence in enumerate(sentences, 1):
        print(f"\n发送第 {i} 句: {sentence}")
        success = pipeline.add_text_from_llm(sentence, timeout=1.0)
        if not success:
            print(f"  ⚠️  被丢弃（队列满）")
        else:
            print(f"  ✅ 加入队列")
        time.sleep(0.2)  # 发送很快
    
    elapsed = time.time() - start_time
    print(f"\n发送耗时: {elapsed:.2f}秒")
    
    # 等待处理完成
    print("\n⏳ 等待所有音频处理完成...")
    time.sleep(5)
    
    # 获取统计
    stats = pipeline.get_stats()
    print(f"\n📊 统计:")
    print(f"  接收: {stats.text_received} 个")
    print(f"  丢弃: {stats.text_dropped} 个")
    print(f"  生成: {stats.audio_generated} 个")
    print(f"  播放: {stats.audio_played} 个")
    
    pipeline.stop(wait=True, timeout=10.0)
    
    print("\n分析:")
    if stats.text_dropped > 0:
        print(f"  ⚠️  有 {stats.text_dropped} 个句子被丢弃")
        print(f"  原因: 音频队列满时，代码选择丢弃而不是等待")
        print(f"  解决: 应该改为阻塞等待（或增大队列）")
    else:
        print(f"  ✅ 所有句子都被处理")
    
    print("\n✅ 音频队列测试完成\n")


def test_playback_detection():
    """测试播放状态检测"""
    print("=" * 70)
    print("测试3: 播放状态检测")
    print("=" * 70)
    
    class MockTTS:
        """模拟TTS"""
        async def synthesize(self, text: str) -> bytes:
            await asyncio.sleep(0.1)
            return f"[AUDIO:{text}]".encode('utf-8')
    
    mock_tts = MockTTS()
    
    pipeline = create_streaming_pipeline(
        tts_engine=mock_tts,
        text_queue_size=3,
        audio_queue_size=2,
        verbose=False  # 关闭详细日志
    )
    
    pipeline.start()
    
    # 发送一个句子
    print("\n发送一个句子...")
    pipeline.add_text_from_llm("这是一个测试句子。")
    pipeline.flush_remaining_text()
    
    # 持续监控状态
    print("\n监控管道状态（10秒）:")
    for i in range(20):
        stats = pipeline.get_stats()
        
        # 检查是否有 is_playing 属性
        has_playing_flag = hasattr(stats, 'is_playing')
        
        print(f"\n时刻 {i*0.5:.1f}s:")
        print(f"  文本队列: {stats.text_queue_size}")
        print(f"  音频队列: {stats.audio_queue_size}")
        print(f"  活动任务: {stats.active_tasks}")
        print(f"  播放标志: {'存在' if has_playing_flag else '❌ 不存在'}")
        if has_playing_flag:
            print(f"  正在播放: {stats.is_playing}")
        
        # 模拟等待逻辑
        all_empty = (stats.text_queue_size == 0 and 
                     stats.audio_queue_size == 0 and 
                     stats.active_tasks == 0)
        
        if all_empty:
            print(f"  ⚠️  当前等待逻辑会认为: '任务完成，可以停止'")
            if has_playing_flag and stats.is_playing:
                print(f"  ✅ 但实际上还在播放，不应该停止")
            else:
                print(f"  ⚠️  无法判断是否在播放（可能导致过早停止）")
        
        time.sleep(0.5)
    
    pipeline.stop(wait=True, timeout=5.0)
    
    print("\n分析:")
    if not has_playing_flag:
        print("  ❌ PipelineStats 缺少 is_playing 字段")
        print("  结果: 无法判断音频是否正在播放")
        print("  后果: 可能在播放中途就停止管道，导致播放失败")
    else:
        print("  ✅ PipelineStats 有 is_playing 字段")
    
    print("\n✅ 播放状态检测测试完成\n")


def main():
    """主测试函数"""
    print("\n" + "=" * 70)
    print("🔍 问题诊断测试套件")
    print("=" * 70 + "\n")
    
    # 测试1: Function call
    test_function_call_issue()
    time.sleep(1)
    
    # 测试2: 音频队列
    test_audio_queue_blocking()
    time.sleep(1)
    
    # 测试3: 播放检测
    test_playback_detection()
    
    print("\n" + "=" * 70)
    print("📋 问题总结")
    print("=" * 70)
    print("\n发现的问题:")
    print("  1. ❌ Function call 参数传递 - 传字符串而不是字典")
    print("  2. ⚠️  音频队列满时直接丢弃 - 应该阻塞等待")
    print("  3. ❌ 缺少播放状态标志 - 无法判断是否正在播放")
    print("\n建议修复:")
    print("  1. agent_hybrid.py - 修复工具参数解析")
    print("  2. streaming_tts_pipeline.py - 音频队列改为阻塞")
    print("  3. streaming_tts_pipeline.py - 添加 is_playing 标志")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()

