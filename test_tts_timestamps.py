"""
测试 TTS 时间戳功能
展示每个 chunk 的详细时间信息，用于性能分析
"""
from agent_hybrid import HybridReasoningAgent
import time

def test_timestamps():
    """测试时间戳记录功能"""
    print("\n" + "="*80)
    print("🧪 TTS 时间戳测试")
    print("="*80)
    print("\n📌 说明:")
    print("  - perf_counter: Python 高精度计时器（相对时间）")
    print("  - wall_clock: 系统墙钟时间（绝对时间）")
    print("  - 时间戳格式: HH:MM:SS.mmm (毫秒精度)")
    print("\n" + "="*80 + "\n")
    
    # 创建 Agent（启用 TTS）
    print("⏳ 初始化 Agent...")
    agent = HybridReasoningAgent(
        enable_cache=True,
        enable_tts=True,
        voice_mode=True
    )
    print("✅ 初始化完成\n")
    
    # 测试用例
    test_cases = [
        ("短句测试", "现在几点了？"),
        ("中等长度", "计算 sqrt(2) 保留 3 位小数"),
        ("长句测试", "图书馆有哪些关于 Python 编程的书籍？请帮我查询一下。"),
    ]
    
    for i, (name, query) in enumerate(test_cases, 1):
        print(f"\n{'#'*80}")
        print(f"# 测试 {i}/{len(test_cases)}: {name}")
        print(f"# 查询: {query}")
        print(f"{'#'*80}\n")
        
        # 记录整体开始时间
        overall_start = time.perf_counter()
        
        # 执行查询（带真实 TTS 播放）
        result = agent.run_with_tts(
            user_input=query,
            show_reasoning=False,  # 隐藏推理过程，专注时间戳
            simulate_mode=False     # 真实 TTS
        )
        
        # 记录整体结束时间
        overall_end = time.perf_counter()
        overall_time = overall_end - overall_start
        
        # 显示结果
        if result['success']:
            print(f"\n{'='*80}")
            print(f"✅ 测试 {i} 完成")
            print(f"{'='*80}")
            print(f"📊 总体统计:")
            print(f"   - 总耗时: {overall_time:.3f}s")
            print(f"   - 工具调用: {result['tool_calls']}次")
            if result.get('total_tts_chunks', 0) > 0:
                print(f"   - TTS分段: {result['total_tts_chunks']}个")
                print(f"   - 播放状态: {'✅ 成功' if result.get('tts_success') else '❌ 失败'}")
            print(f"{'='*80}")
        else:
            print(f"\n❌ 测试 {i} 失败: {result['output']}")
        
        # 间隔
        if i < len(test_cases):
            print("\n⏸️  等待 2 秒...\n")
            time.sleep(2)
    
    print("\n" + "="*80)
    print("🎉 所有测试完成！")
    print("="*80)
    print("\n💡 分析建议:")
    print("  1. 查看每个 chunk 的生成时间 (TTS耗时)")
    print("  2. 查看音频加载时间 (加载耗时)")
    print("  3. 查看实际播放时间 (播放耗时)")
    print("  4. 对比 perf_counter 和 wall_clock 的差异")
    print("  5. 检查是否有异常的长时间等待")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    try:
        test_timestamps()
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()

