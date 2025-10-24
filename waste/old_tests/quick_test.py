"""
快速测试新功能
"""
from agent import ReasoningAgent

def main():
    print("\n" + "="*80)
    print("🧪 快速测试新功能")
    print("="*80)
    
    agent = ReasoningAgent(verbose=False)
    
    # 测试1: 图书馆查询
    print("\n【测试1】图书馆查询功能")
    print("-"*80)
    result1 = agent.run_with_sentence_stream(
        "图书馆有哪些关于Python的书？",
        show_reasoning=True
    )
    print(f"结果: {result1['output'][:200]}...")
    
    # 测试2: 对话结束检测
    print("\n\n【测试2】对话结束检测")
    print("-"*80)
    result2 = agent.run_with_sentence_stream(
        "好的，再见！",
        show_reasoning=True
    )
    
    # 检查是否检测到结束意图
    end_detected = False
    for step in result2['reasoning_steps']:
        if step['tool'] == 'end_conversation_detector':
            if 'END_CONVERSATION' in step['output']:
                end_detected = True
    
    if end_detected:
        print("\n✅ 成功检测到结束意图！")
    else:
        print("\n⚠️  未检测到结束意图")
    
    # 测试3: 推理过程展示
    print("\n\n【测试3】复杂推理展示")
    print("-"*80)
    result3 = agent.run_with_sentence_stream(
        "现在几点，然后计算sqrt(9)",
        show_reasoning=True
    )
    
    print("\n" + "="*80)
    print("✅ 测试完成！")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()

