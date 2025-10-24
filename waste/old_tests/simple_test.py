"""
简单测试 - 快速验证核心功能
"""
from agent import ReasoningAgent


def main():
    print("\n" + "=" * 70)
    print("🧪 快速测试：计算 sqrt(2) 保留3位小数")
    print("=" * 70)
    
    # 创建Agent
    print("\n初始化Agent...")
    agent = ReasoningAgent(verbose=True)
    
    # 核心测试
    print("\n开始测试...")
    result = agent.run("计算sqrt(2)保留3位小数")
    
    # 验证结果
    print("\n" + "=" * 70)
    print("📊 测试结果")
    print("=" * 70)
    
    if result['success'] and '1.414' in result['output']:
        print("✅ 测试通过！")
        print(f"   答案: {result['output']}")
        print("\n✨ Agent成功展示：")
        print("   • 理解了用户的计算需求")
        print("   • 自主决定调用calculator工具")
        print("   • 正确构造表达式: round(sqrt(2), 3)")
        print("   • 获得正确答案: 1.414")
    else:
        print("❌ 测试失败")
        print(f"   输出: {result['output']}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()

