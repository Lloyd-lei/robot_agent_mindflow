"""
交互式演示 - 体验具有推理能力和函数调用的AI Agent
"""
from agent import ReasoningAgent


def print_header():
    """打印欢迎界面"""
    print("\n" + "=" * 70)
    print("🤖 多模态AI Agent - 交互式演示")
    print("=" * 70)
    print("\n特性：")
    print("  ✅ 推理能力 - LLM自主分析和决策")
    print("  ✅ 函数调用 - 自动调用工具完成任务")
    print("  ✅ 解耦设计 - LLM与工具完全分离")
    print("\n可用功能：")
    print("  • 数学计算（加减乘除、平方根、三角函数等）")
    print("  • 普通对话")
    print("\n" + "-" * 70)


def print_examples():
    """打印示例"""
    print("\n💡 试试这些命令：")
    print("  1️⃣  计算sqrt(2)保留3位小数")
    print("  2️⃣  (3+5)*2-1等于多少")
    print("  3️⃣  计算sin(pi/2)的值")
    print("  4️⃣  你好")
    print("\n输入 'q' 或 'quit' 退出")
    print("输入 'help' 查看帮助")
    print("-" * 70)


def main():
    """主函数"""
    print_header()
    
    # 初始化Agent
    print("\n⏳ 正在初始化Agent...")
    agent = ReasoningAgent(verbose=False)  # 设置verbose=False减少输出
    print("✅ Agent初始化完成！\n")
    
    print_examples()
    
    # 交互循环
    while True:
        try:
            # 获取用户输入
            user_input = input("\n💬 您: ").strip()
            
            # 退出命令
            if user_input.lower() in ['q', 'quit', 'exit', '退出']:
                print("\n👋 再见！感谢使用AI Agent！\n")
                break
            
            # 帮助命令
            if user_input.lower() in ['help', '帮助', 'h']:
                print_examples()
                continue
            
            # 空输入
            if not user_input:
                print("⚠️ 请输入内容")
                continue
            
            # 执行Agent推理
            print("\n🤖 Agent: ", end="", flush=True)
            result = agent.run(user_input)
            
            # 显示结果
            if result['success']:
                print(result['output'])
            else:
                print(f"❌ 出错了: {result['output']}")
                
        except KeyboardInterrupt:
            print("\n\n👋 程序被中断，再见！\n")
            break
        except Exception as e:
            print(f"\n❌ 发生错误: {str(e)}\n")


if __name__ == "__main__":
    main()

