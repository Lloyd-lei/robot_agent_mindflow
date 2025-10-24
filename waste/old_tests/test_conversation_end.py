"""
专门测试对话结束检测功能
"""
from agent import ReasoningAgent


def test_end_detection():
    """测试对话结束检测"""
    print("\n" + "="*80)
    print("🧪 测试对话结束检测功能")
    print("="*80)
    
    agent = ReasoningAgent(verbose=False)
    
    # 测试各种结束关键词
    test_cases = [
        "再见",
        "拜拜",
        "bye",
        "退出",
        "结束",
        "不聊了",
        "好的，再见！",
        "那我先走了",
    ]
    
    print("\n测试用例：")
    for i, test_input in enumerate(test_cases, 1):
        print(f"{i}. \"{test_input}\"")
    
    print("\n" + "-"*80)
    
    for i, test_input in enumerate(test_cases, 1):
        print(f"\n【测试 {i}/{len(test_cases)}】输入: \"{test_input}\"")
        print("-"*80)
        
        result = agent.run_with_sentence_stream(test_input, show_reasoning=True)
        
        # 检查是否调用了检测器
        detector_called = False
        end_detected = False
        
        if result['step_count'] > 0:
            for step in result['reasoning_steps']:
                if step['tool'] == 'end_conversation_detector':
                    detector_called = True
                    if 'END_CONVERSATION' in step['output']:
                        end_detected = True
        
        print(f"\n结果:")
        print(f"  ✅ 调用检测器: {'是' if detector_called else '❌ 否'}")
        print(f"  ✅ 检测到结束: {'是' if end_detected else '❌ 否'}")
        
        if not detector_called:
            print(f"  ⚠️  问题：模型没有调用end_conversation_detector工具！")
        elif not end_detected:
            print(f"  ⚠️  问题：调用了工具但没有检测到结束意图！")
        else:
            print(f"  🎉 完美！正确检测并调用")
        
        print("="*80)
    
    print("\n✅ 测试完成\n")


if __name__ == "__main__":
    test_end_detection()

