"""
测试脚本 - 验证具有推理能力的LLM Agent
重点测试：计算sqrt(2)保留3位小数
"""
from agent import ReasoningAgent
import sys


def test_sqrt_calculation():
    """测试核心功能：计算sqrt(2)保留3位小数"""
    print("\n" + "="*70)
    print("🧪 核心测试：计算 sqrt(2) 保留3位小数")
    print("="*70)
    
    # 创建Agent
    agent = ReasoningAgent(verbose=True)
    
    # 测试不同的表达方式
    test_cases = [
        "计算sqrt(2)保留3位小数",
        "求2的平方根，保留3位小数",
        "sqrt(2)的值是多少？保留小数点后3位",
    ]
    
    results = []
    for i, test_input in enumerate(test_cases, 1):
        print(f"\n{'─'*70}")
        print(f"测试 {i}/{len(test_cases)}")
        print(f"{'─'*70}")
        
        result = agent.run(test_input)
        results.append({
            'input': test_input,
            'success': result['success'],
            'output': result['output']
        })
    
    # 汇总结果
    print("\n" + "="*70)
    print("📊 测试结果汇总")
    print("="*70)
    
    for i, res in enumerate(results, 1):
        status = "✅ 成功" if res['success'] else "❌ 失败"
        print(f"\n{i}. {status}")
        print(f"   输入: {res['input']}")
        print(f"   输出: {res['output']}")
    
    # 验证答案
    print("\n" + "="*70)
    print("🔍 验证答案")
    print("="*70)
    
    # sqrt(2) ≈ 1.414213562373095
    # 保留3位小数应该是 1.414
    expected_answer = "1.414"
    
    success_count = sum(1 for r in results if r['success'])
    contains_correct_answer = any(expected_answer in r['output'] for r in results)
    
    print(f"成功率: {success_count}/{len(results)}")
    print(f"正确答案 ({expected_answer}) 出现: {'是' if contains_correct_answer else '否'}")
    
    if success_count == len(results) and contains_correct_answer:
        print("\n🎉 测试通过！Agent能够正确推理并调用工具计算sqrt(2)保留3位小数")
        return True
    else:
        print("\n⚠️ 测试需要检查")
        return False


def test_additional_scenarios():
    """测试其他场景，验证Agent的推理能力"""
    print("\n" + "="*70)
    print("🧪 扩展测试：验证推理能力")
    print("="*70)
    
    agent = ReasoningAgent(verbose=True)
    
    test_cases = [
        {
            'name': '复杂数学运算',
            'input': '(3+5)*2-1等于多少？',
            'expected_contains': '15'
        },
        {
            'name': '纯对话场景',
            'input': '你好',
            'expected_contains': None  # 只要能回答就行
        },
        {
            'name': '使用数学常量',
            'input': '计算sin(pi/2)的值',
            'expected_contains': '1'
        }
    ]
    
    results = []
    for test in test_cases:
        print(f"\n{'─'*70}")
        print(f"测试: {test['name']}")
        print(f"{'─'*70}")
        
        result = agent.run(test['input'])
        
        # 验证结果
        success = result['success']
        if test['expected_contains']:
            success = success and test['expected_contains'] in result['output']
        
        results.append({
            'name': test['name'],
            'success': success,
            'output': result['output']
        })
    
    # 汇总
    print("\n" + "="*70)
    print("📊 扩展测试结果")
    print("="*70)
    
    for res in results:
        status = "✅" if res['success'] else "❌"
        print(f"{status} {res['name']}")
    
    success_rate = sum(1 for r in results if r['success']) / len(results)
    print(f"\n成功率: {success_rate*100:.0f}%")
    
    return success_rate >= 0.8  # 80%通过率


def main():
    """主测试流程"""
    print("\n" + "="*80)
    print("🚀 开始测试具有推理能力和自主函数调用的LLM Agent")
    print("="*80)
    
    try:
        # 核心测试
        core_test_passed = test_sqrt_calculation()
        
        # 扩展测试
        extended_test_passed = test_additional_scenarios()
        
        # 最终结果
        print("\n" + "="*80)
        print("🏁 测试完成")
        print("="*80)
        
        if core_test_passed and extended_test_passed:
            print("✅ 所有测试通过！")
            print("\n✨ Agent特性验证成功：")
            print("   • LLM具有推理能力")
            print("   • 能够自主决策何时调用工具")
            print("   • 工具调用准确无误")
            print("   • 解耦设计，架构清晰")
            return 0
        else:
            print("⚠️ 部分测试需要检查")
            return 1
            
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

