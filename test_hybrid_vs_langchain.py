"""
性能对比测试：混合架构 vs 纯LangChain
展示改进效果
"""
import time
from agent_hybrid import HybridReasoningAgent
from agent import ReasoningAgent


def test_tool_calling_reliability():
    """测试工具调用可靠性"""
    print("\n" + "="*80)
    print("🧪 测试1：工具调用可靠性对比")
    print("="*80)
    
    test_cases = [
        ("数学计算", "计算1+1等于多少"),
        ("对话结束1", "再见"),
        ("对话结束2", "拜拜"),
        ("对话结束3", "退出"),
    ]
    
    print("\n" + "-"*80)
    print("🔵 纯LangChain架构")
    print("-"*80)
    
    langchain_agent = ReasoningAgent(verbose=False)
    langchain_results = []
    
    for name, query in test_cases:
        result = langchain_agent.run_with_sentence_stream(query, show_reasoning=False)
        tool_used = result['step_count'] > 0
        tools_called = [s['tool'] for s in result['reasoning_steps']]
        
        langchain_results.append({
            'name': name,
            'tool_used': tool_used,
            'tools': tools_called
        })
        
        status = "✅" if tool_used else "❌"
        print(f"{status} {name}: 调用工具={tool_used}, 工具={tools_called}")
    
    print("\n" + "-"*80)
    print("🟢 混合架构（OpenAI原生）")
    print("-"*80)
    
    hybrid_agent = HybridReasoningAgent(enable_cache=False)
    hybrid_results = []
    
    for name, query in test_cases:
        result = hybrid_agent.run(query, show_reasoning=False)
        tool_used = result['tool_calls'] > 0
        tools_called = [s['tool'] for s in result['reasoning_steps']]
        
        hybrid_results.append({
            'name': name,
            'tool_used': tool_used,
            'tools': tools_called
        })
        
        status = "✅" if tool_used else "❌"
        print(f"{status} {name}: 调用工具={tool_used}, 工具={tools_called}")
    
    # 统计
    print("\n" + "="*80)
    print("📊 对比统计")
    print("="*80)
    
    langchain_success = sum(1 for r in langchain_results if r['tool_used'])
    hybrid_success = sum(1 for r in hybrid_results if r['tool_used'])
    
    print(f"LangChain架构: {langchain_success}/{len(test_cases)} 调用了工具 ({langchain_success/len(test_cases)*100:.0f}%)")
    print(f"混合架构:     {hybrid_success}/{len(test_cases)} 调用了工具 ({hybrid_success/len(test_cases)*100:.0f}%)")
    
    improvement = (hybrid_success - langchain_success) / len(test_cases) * 100
    if improvement > 0:
        print(f"\n✅ 混合架构提升: +{improvement:.0f}% 可靠性")
    
    return hybrid_success > langchain_success


def test_multi_turn_speed():
    """测试多轮对话速度（KV Cache效果）"""
    print("\n" + "="*80)
    print("🧪 测试2：多轮对话速度对比（KV Cache效果）")
    print("="*80)
    
    queries = [
        "计算1+1",
        "现在几点",
        "2+2等于多少",
        "告诉我今天星期几",
    ]
    
    print("\n" + "-"*80)
    print("🔵 纯LangChain（无KV Cache优化）")
    print("-"*80)
    
    langchain_agent = ReasoningAgent(verbose=False)
    langchain_times = []
    
    for i, query in enumerate(queries, 1):
        start = time.time()
        langchain_agent.run_with_sentence_stream(query, show_reasoning=False)
        elapsed = time.time() - start
        langchain_times.append(elapsed)
        print(f"轮次{i}: {elapsed:.2f}秒")
    
    print("\n" + "-"*80)
    print("🟢 混合架构（启用KV Cache）")
    print("-"*80)
    
    hybrid_agent = HybridReasoningAgent(enable_cache=True)
    hybrid_times = []
    
    for i, query in enumerate(queries, 1):
        start = time.time()
        hybrid_agent.run(query, show_reasoning=False)
        elapsed = time.time() - start
        hybrid_times.append(elapsed)
        
        cache_indicator = " 🚀 (KV Cache)" if i > 1 else ""
        print(f"轮次{i}: {elapsed:.2f}秒{cache_indicator}")
    
    # 统计
    print("\n" + "="*80)
    print("📊 速度对比")
    print("="*80)
    
    langchain_avg = sum(langchain_times) / len(langchain_times)
    hybrid_avg = sum(hybrid_times) / len(hybrid_times)
    
    # 第2轮开始的平均速度（KV Cache生效）
    if len(hybrid_times) > 1:
        hybrid_cached_avg = sum(hybrid_times[1:]) / len(hybrid_times[1:])
        speedup = langchain_avg / hybrid_cached_avg
        
        print(f"LangChain平均: {langchain_avg:.2f}秒/轮")
        print(f"混合架构平均: {hybrid_avg:.2f}秒/轮")
        print(f"混合架构(KV Cache生效后): {hybrid_cached_avg:.2f}秒/轮")
        print(f"\n✅ KV Cache加速: {speedup:.1f}x")
    
    return hybrid_avg < langchain_avg


def test_end_conversation_detection():
    """专门测试end_conversation检测"""
    print("\n" + "="*80)
    print("🧪 测试3：对话结束检测可靠性")
    print("="*80)
    
    end_phrases = [
        "再见",
        "拜拜",
        "bye",
        "退出",
        "好的，再见！",
    ]
    
    print("\n" + "-"*80)
    print("🔵 纯LangChain")
    print("-"*80)
    
    langchain_agent = ReasoningAgent(verbose=False)
    langchain_detected = 0
    
    for phrase in end_phrases:
        result = langchain_agent.run_with_sentence_stream(phrase, show_reasoning=False)
        detected = any(
            s['tool'] == 'end_conversation_detector' 
            for s in result['reasoning_steps']
        )
        langchain_detected += detected
        status = "✅" if detected else "❌"
        print(f"{status} \"{phrase}\": 检测器={'调用' if detected else '未调用'}")
    
    print("\n" + "-"*80)
    print("🟢 混合架构")
    print("-"*80)
    
    hybrid_agent = HybridReasoningAgent(enable_cache=False)
    hybrid_detected = 0
    
    for phrase in end_phrases:
        result = hybrid_agent.run(phrase, show_reasoning=False)
        detected = any(
            s['tool'] == 'end_conversation_detector'
            for s in result['reasoning_steps']
        )
        hybrid_detected += detected
        status = "✅" if detected else "❌"
        print(f"{status} \"{phrase}\": 检测器={'调用' if detected else '未调用'}")
    
    # 统计
    print("\n" + "="*80)
    print("📊 检测成功率")
    print("="*80)
    
    langchain_rate = langchain_detected / len(end_phrases) * 100
    hybrid_rate = hybrid_detected / len(end_phrases) * 100
    
    print(f"LangChain: {langchain_detected}/{len(end_phrases)} ({langchain_rate:.0f}%)")
    print(f"混合架构: {hybrid_detected}/{len(end_phrases)} ({hybrid_rate:.0f}%)")
    
    if hybrid_rate > langchain_rate:
        improvement = hybrid_rate - langchain_rate
        print(f"\n✅ 混合架构提升: +{improvement:.0f}%")
    
    return hybrid_detected > langchain_detected


def main():
    """运行所有测试"""
    print("\n" + "="*80)
    print("🚀 混合架构 vs 纯LangChain 性能对比测试")
    print("="*80)
    print("\n测试项目：")
    print("1. 工具调用可靠性")
    print("2. 多轮对话速度（KV Cache效果）")
    print("3. 对话结束检测")
    
    results = []
    
    # 测试1
    try:
        result1 = test_tool_calling_reliability()
        results.append(("工具调用可靠性", result1))
    except Exception as e:
        print(f"\n❌ 测试1失败: {e}")
        results.append(("工具调用可靠性", False))
    
    # 测试2
    try:
        result2 = test_multi_turn_speed()
        results.append(("多轮对话速度", result2))
    except Exception as e:
        print(f"\n❌ 测试2失败: {e}")
        results.append(("多轮对话速度", False))
    
    # 测试3
    try:
        result3 = test_end_conversation_detection()
        results.append(("对话结束检测", result3))
    except Exception as e:
        print(f"\n❌ 测试3失败: {e}")
        results.append(("对话结束检测", False))
    
    # 总结
    print("\n" + "="*80)
    print("🏁 测试总结")
    print("="*80)
    
    for name, success in results:
        status = "✅ 混合架构优于LangChain" if success else "⚠️  需要检查"
        print(f"{status}: {name}")
    
    passed = sum(1 for _, s in results if s)
    print(f"\n总计: {passed}/{len(results)} 项测试中混合架构表现更好")
    
    if passed == len(results):
        print("\n🎉 混合架构全面优于纯LangChain！")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()

