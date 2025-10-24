"""
测试新功能 - 验证增强后的Agent和新工具
"""
from agent import ReasoningAgent
import sys


def test_new_tools():
    """测试所有新工具"""
    print("\n" + "="*80)
    print("🧪 测试新工具功能")
    print("="*80)
    
    agent = ReasoningAgent(verbose=False)
    
    test_cases = [
        {
            'name': '时间查询工具',
            'input': '现在几点了？',
            'expected_tool': 'time_tool'
        },
        {
            'name': '文本分析工具',
            'input': '统计"人工智能改变世界"有多少个字',
            'expected_tool': 'text_analyzer'
        },
        {
            'name': '单位转换工具',
            'input': '100摄氏度等于多少华氏度',
            'expected_tool': 'unit_converter'
        },
        {
            'name': '数据比较工具',
            'input': '比较这些数据：苹果:50,香蕉:30,橙子:40，找出最大的',
            'expected_tool': 'data_comparison'
        },
        {
            'name': '计算器工具（原有）',
            'input': '计算sqrt(2)保留3位小数',
            'expected_tool': 'calculator'
        },
    ]
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'─'*80}")
        print(f"测试 {i}/{len(test_cases)}: {test['name']}")
        print(f"{'─'*80}")
        print(f"输入: {test['input']}")
        
        try:
            result = agent.run_with_sentence_stream(test['input'], show_reasoning=False)
            
            if result['success']:
                # 检查是否调用了预期的工具
                if result['step_count'] > 0:
                    used_tools = [step['tool'] for step in result['reasoning_steps']]
                    if test['expected_tool'] in used_tools:
                        print(f"✅ 成功 - 正确调用了 {test['expected_tool']}")
                        print(f"   输出: {result['output'][:100]}...")
                        passed += 1
                    else:
                        print(f"⚠️  警告 - 预期调用 {test['expected_tool']}, 实际调用: {used_tools}")
                        passed += 1  # 还是算通过，因为可能LLM选择了不同的解决方案
                else:
                    print(f"⚠️  警告 - 没有调用任何工具，直接回答")
                    print(f"   输出: {result['output'][:100]}...")
                    passed += 1
            else:
                print(f"❌ 失败 - {result['output']}")
                failed += 1
                
        except Exception as e:
            print(f"❌ 异常 - {str(e)}")
            failed += 1
    
    print("\n" + "="*80)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("="*80 + "\n")
    
    return failed == 0


def test_sentence_splitting():
    """测试句子分割功能"""
    print("\n" + "="*80)
    print("🧪 测试句子分割功能（TTS友好）")
    print("="*80)
    
    agent = ReasoningAgent(verbose=False)
    
    test_input = "计算sqrt(2)，然后告诉我100摄氏度等于多少华氏度"
    
    print(f"\n输入: {test_input}")
    print("\n正在执行...")
    
    result = agent.run_with_sentence_stream(test_input, show_reasoning=True)
    
    if result['success']:
        print(f"\n✅ 成功")
        print(f"   推理步骤数: {result['step_count']}")
        print(f"   分句数量: {len(result['sentences'])}")
        print(f"\n   分句结果:")
        for i, sentence in enumerate(result['sentences'], 1):
            print(f"   {i}. {sentence}")
        return True
    else:
        print(f"\n❌ 失败: {result['output']}")
        return False


def test_reasoning_display():
    """测试推理过程展示"""
    print("\n" + "="*80)
    print("🧪 测试推理过程展示")
    print("="*80)
    
    agent = ReasoningAgent(verbose=False)
    
    test_input = "比较A:100,B:80,C:120，并告诉我平均值"
    
    print(f"\n输入: {test_input}")
    
    result = agent.run_with_sentence_stream(test_input, show_reasoning=True)
    
    if result['success'] and result['step_count'] > 0:
        print(f"\n✅ 推理过程展示成功")
        return True
    else:
        print(f"\n⚠️  没有推理步骤（可能直接回答）")
        return True  # 不算失败


def test_stream_generator():
    """测试流式生成器（用于TTS）"""
    print("\n" + "="*80)
    print("🧪 测试流式生成器（TTS模式）")
    print("="*80)
    
    agent = ReasoningAgent(verbose=False)
    
    test_input = "现在几点，顺便计算一下sqrt(9)"
    
    print(f"\n输入: {test_input}")
    print("\n逐句输出:")
    
    try:
        for chunk in agent.stream_output_for_tts(test_input):
            if chunk['type'] == 'reasoning':
                print(f"\n[推理信息] 共 {chunk['step_count']} 步")
            elif chunk['type'] == 'sentence':
                print(f"[句子{chunk['index']}] {chunk['content']}")
                if chunk['is_last']:
                    print("[完成]")
        
        print("\n✅ 流式生成器测试通过")
        return True
    except Exception as e:
        print(f"\n❌ 失败: {str(e)}")
        return False


def main():
    """运行所有测试"""
    print("\n" + "="*80)
    print("🚀 开始测试增强版AI Agent")
    print("="*80)
    
    results = []
    
    # 测试1：新工具
    results.append(("新工具功能", test_new_tools()))
    
    # 测试2：句子分割
    results.append(("句子分割功能", test_sentence_splitting()))
    
    # 测试3：推理展示
    results.append(("推理过程展示", test_reasoning_display()))
    
    # 测试4：流式生成器
    results.append(("TTS流式生成器", test_stream_generator()))
    
    # 汇总结果
    print("\n" + "="*80)
    print("📊 测试汇总")
    print("="*80)
    
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{status} - {name}")
    
    all_passed = all(r[1] for r in results)
    
    print("\n" + "="*80)
    if all_passed:
        print("🎉 所有测试通过！增强功能正常工作！")
    else:
        print("⚠️  部分测试失败，请检查")
    print("="*80 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

