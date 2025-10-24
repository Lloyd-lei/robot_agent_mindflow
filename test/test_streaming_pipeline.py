#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
流式TTS管道测试脚本
测试智能分句、背压控制、资源管理等功能
"""

import time
import asyncio
from streaming_tts_pipeline import (
    StreamingTTSPipeline,
    create_streaming_pipeline,
    SmartSentenceSplitter
)


def test_sentence_splitter():
    """测试智能分句器"""
    print("=" * 70)
    print("测试1: 智能分句器")
    print("=" * 70)
    
    splitter = SmartSentenceSplitter(min_chunk_length=5, max_chunk_length=50)
    
    # 模拟LLM流式输出
    test_texts = [
        "今天",
        "天气",
        "真不错。",
        "我们",
        "去",
        "公园",
        "散步吧！",
        "那里",
        "的",
        "风景",
        "很美。"
    ]
    
    print("\n模拟LLM流式输出：")
    for text in test_texts:
        print(f"输入: '{text}'", end=" -> ")
        sentences = splitter.add_text(text)
        if sentences:
            for s in sentences:
                print(f"\n  ✅ 完整句子: {s}")
        else:
            print("(缓冲中)")
    
    # 刷新剩余文本
    remaining = splitter.flush()
    if remaining:
        print(f"\n  ✅ 剩余文本: {remaining}")
    
    print("\n✅ 智能分句器测试完成\n")


def test_streaming_pipeline_mock():
    """测试流式管道（模拟TTS）"""
    print("=" * 70)
    print("测试2: 流式TTS管道（模拟TTS引擎）")
    print("=" * 70)
    
    class MockTTS:
        """模拟TTS引擎"""
        async def synthesize(self, text: str) -> bytes:
            # 模拟生成延迟
            await asyncio.sleep(0.2)
            return f"[AUDIO:{text}]".encode('utf-8')
    
    mock_tts = MockTTS()
    
    # 创建流式管道
    pipeline = create_streaming_pipeline(
        tts_engine=mock_tts,
        text_queue_size=3,
        audio_queue_size=2,
        max_tasks=5,
        verbose=True
    )
    
    # 启动管道
    pipeline.start()
    
    # 模拟LLM流式输出
    print("\n模拟LLM流式输出：")
    llm_outputs = [
        "今天",
        "天气",
        "真不错。",
        "我们",
        "去",
        "公园",
        "散步",
        "吧！",
        "那里",
        "风景",
        "很美。",
        "你",
        "觉得",
        "怎么样？"
    ]
    
    for i, output in enumerate(llm_outputs):
        success = pipeline.add_text_from_llm(output)
        if not success:
            print(f"⚠️  第{i}个输出被丢弃（背压生效）")
        time.sleep(0.1)  # 模拟LLM生成速度
    
    # 刷新缓冲区
    pipeline.flush_remaining_text()
    
    # 等待处理完成
    print("\n⏳ 等待所有音频处理完成...")
    while True:
        stats = pipeline.get_stats()
        if stats.text_queue_size == 0 and \
           stats.audio_queue_size == 0 and \
           stats.active_tasks == 0:
            break
        time.sleep(0.5)
    
    # 停止管道
    pipeline.stop(wait=True, timeout=5.0)
    
    print("\n✅ 流式管道测试完成\n")


def test_backpressure():
    """测试背压控制"""
    print("=" * 70)
    print("测试3: 背压控制")
    print("=" * 70)
    
    class SlowTTS:
        """慢速TTS（用于测试背压）"""
        async def synthesize(self, text: str) -> bytes:
            # 故意很慢
            await asyncio.sleep(2.0)
            return f"[SLOW_AUDIO:{text}]".encode('utf-8')
    
    slow_tts = SlowTTS()
    
    # 创建小队列的管道
    pipeline = create_streaming_pipeline(
        tts_engine=slow_tts,
        text_queue_size=2,      # 很小的队列
        audio_queue_size=1,     # 很小的队列
        max_tasks=3,            # 限制任务数
        verbose=True
    )
    
    pipeline.start()
    
    # 快速发送大量文本（测试背压）
    print("\n快速发送大量文本（测试背压）：")
    test_sentences = [
        "第一句话。",
        "第二句话。",
        "第三句话。",
        "第四句话。",
        "第五句话。",
        "第六句话。",
        "第七句话。",
        "第八句话。",
    ]
    
    success_count = 0
    dropped_count = 0
    
    for sentence in test_sentences:
        # 尝试快速添加（不等待）
        success = pipeline.add_text_from_llm(sentence, timeout=0.5)
        if success:
            success_count += 1
        else:
            dropped_count += 1
        time.sleep(0.1)  # 很快
    
    print(f"\n📊 背压效果：")
    print(f"   成功添加: {success_count} 个")
    print(f"   被丢弃: {dropped_count} 个（背压保护）")
    
    # 等待处理完成
    print("\n⏳ 等待处理完成...")
    time.sleep(8)  # 给足够的时间
    
    # 停止管道
    pipeline.stop(wait=True, timeout=5.0)
    
    print("\n✅ 背压控制测试完成\n")


def test_edge_tts_integration():
    """测试Edge TTS集成（真实TTS）"""
    print("=" * 70)
    print("测试4: Edge TTS集成（真实语音）")
    print("=" * 70)
    
    try:
        from tts_interface import TTSFactory, TTSProvider
        
        # 创建Edge TTS引擎
        print("\n创建Edge TTS引擎...")
        tts_engine = TTSFactory.create_tts(
            provider=TTSProvider.EDGE,
            voice="zh-CN-XiaoxiaoNeural",
            rate="+0%",
            volume="+0%"
        )
        
        # 创建流式管道
        pipeline = create_streaming_pipeline(
            tts_engine=tts_engine,
            text_queue_size=3,
            audio_queue_size=2,
            max_tasks=5,
            verbose=True
        )
        
        pipeline.start()
        
        # 测试句子
        test_text = "你好，这是流式TTS测试。今天天气真不错！我们一起去公园散步吧。"
        
        print(f"\n测试文本: {test_text}\n")
        
        # 模拟流式输入
        for char in test_text:
            pipeline.add_text_from_llm(char)
            time.sleep(0.05)  # 模拟LLM输出速度
        
        # 刷新缓冲区
        pipeline.flush_remaining_text()
        
        # 等待处理完成
        print("\n⏳ 等待所有音频播放完成...")
        while True:
            stats = pipeline.get_stats()
            if stats.text_queue_size == 0 and \
               stats.audio_queue_size == 0 and \
               stats.active_tasks == 0:
                break
            time.sleep(0.5)
        
        # 停止管道
        pipeline.stop(wait=True, timeout=5.0)
        
        print("\n✅ Edge TTS集成测试完成\n")
        
    except Exception as e:
        print(f"\n❌ Edge TTS测试失败: {e}")
        print("   (可能需要网络连接或pygame支持)\n")


def main():
    """主测试函数"""
    print("\n" + "=" * 70)
    print("🧪 流式TTS管道 - 完整测试套件")
    print("=" * 70 + "\n")
    
    # 测试1: 智能分句器
    test_sentence_splitter()
    time.sleep(1)
    
    # 测试2: 流式管道（模拟）
    test_streaming_pipeline_mock()
    time.sleep(1)
    
    # 测试3: 背压控制
    test_backpressure()
    time.sleep(1)
    
    # 测试4: Edge TTS集成
    print("\n是否测试真实Edge TTS？(y/n): ", end="")
    import sys
    choice = input().strip().lower()
    if choice == 'y':
        test_edge_tts_integration()
    else:
        print("跳过Edge TTS测试")
    
    print("\n" + "=" * 70)
    print("✅ 所有测试完成！")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()

