"""
新架构演示 - 展示如何使用重构后的代码

使用方式:
    python examples/demo_new_architecture.py
"""
import sys
from pathlib import Path

# 添加src目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core import HybridReasoningAgent, settings
from src.tools import load_all_tools


def main():
    """主函数"""
    print("\n" + "="*80)
    print("🚀 新架构演示 - 混合架构AI Agent")
    print("="*80)

    # 加载所有工具
    print("\n📦 正在加载工具...")
    tools = load_all_tools()
    print(f"✅ 已加载 {len(tools)} 个工具\n")

    # 创建Agent
    print("🤖 正在初始化Agent...")
    agent = HybridReasoningAgent(
        tools=tools,
        enable_cache=settings.enable_cache
    )
    print()

    # 测试用例
    test_cases = [
        ("数学计算", "计算sqrt(2)保留3位小数"),
        ("时间查询", "现在几点了?"),
        ("对话结束", "好的,再见!"),
    ]

    print("🧪 开始测试...\n")

    for i, (name, query) in enumerate(test_cases, 1):
        print(f"{'─'*80}")
        print(f"测试 {i}/{len(test_cases)}: {name}")
        print(f"查询: {query}")
        print(f"{'─'*80}\n")

        # 执行
        result = agent.run(query, show_reasoning=True)

        # 显示结果
        if result.success:
            print(f"\n✅ 成功")
            print(f"   工具调用: {result.tool_calls}次")
            if result.metadata.get('should_end'):
                print(f"   检测到对话结束\n")
                break
        else:
            print(f"\n❌ 失败: {result.error}\n")

        print()

    # 显示统计
    print(f"{'='*80}")
    print("📊 统计信息")
    print(f"{'='*80}")

    stats = agent.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")

    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 程序被中断,再见!\n")
    except Exception as e:
        print(f"\n❌ 错误: {e}\n")
        import traceback
        traceback.print_exc()
