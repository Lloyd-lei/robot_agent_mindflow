"""
增强版交互式演示 - 展示推理过程 + 句子分割输出
支持彩色输出和TTS友好的分句展示
"""
from agent import ReasoningAgent
import time
import sys

# 尝试导入colorama，如果没有就使用普通输出
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False
    # 定义空的颜色常量
    class Fore:
        CYAN = YELLOW = GREEN = MAGENTA = RED = BLUE = WHITE = ""
    class Style:
        BRIGHT = RESET_ALL = ""


def print_header():
    """打印欢迎界面"""
    print("\n" + "=" * 80)
    print(Fore.CYAN + Style.BRIGHT + "🤖 多模态AI Agent - 增强版交互演示")
    print("=" * 80)
    print("\n" + Fore.GREEN + "✨ 新特性：")
    print("  📊 实时展示推理过程")
    print("  🔊 句子分割输出（TTS友好）")
    print("  🛠️  6种工具支持")
    print("\n" + Fore.YELLOW + "🎯 可用功能：")
    print("  • 数学计算 - 复杂运算、函数计算")
    print("  • 时间查询 - 获取当前时间日期")
    print("  • 文本分析 - 字数统计、句子分析")
    print("  • 单位转换 - 温度、长度等转换")
    print("  • 数据比较 - 数值比较、排序")
    print("  • 逻辑推理 - 结构化推理分析")
    print("  • 图书馆系统 - 查询图书信息")
    print("  • 对话结束检测 - 智能识别结束意图")
    print("\n" + "-" * 80)


def print_examples():
    """打印示例"""
    print("\n" + Fore.MAGENTA + "💡 试试这些命令：")
    examples = [
        "1️⃣  计算sqrt(2)保留3位小数",
        "2️⃣  现在几点了？",
        "3️⃣  统计'人工智能改变世界'有多少个字",
        "4️⃣  100摄氏度等于多少华氏度？",
        "5️⃣  比较这些：苹果:50,香蕉:30,橙子:40，找出最贵的",
        "6️⃣  (3+5)*2-1等于多少",
    ]
    for ex in examples:
        print(f"  {ex}")
    
    print("\n" + Fore.RED + "⌨️  命令：")
    print("  • 输入 'q' 或 'quit' - 退出程序")
    print("  • 输入 'help' - 查看帮助")
    print("  • 输入 'mode' - 切换显示模式")
    print("  • 输入 'tts' - 切换TTS模拟")
    print("-" * 80)


def simulate_tts_output(sentences: list, enabled: bool = True):
    """模拟TTS逐句播放效果"""
    if not enabled:
        return
    
    print(f"\n{Fore.YELLOW}{'='*70}")
    print(f"{Fore.YELLOW}🔊 模拟TTS逐句播放效果")
    print(f"{Fore.YELLOW}{'='*70}")
    
    for i, sentence in enumerate(sentences, 1):
        print(f"\n{Fore.GREEN}[TTS-句子{i}] {Fore.WHITE}", end="", flush=True)
        # 逐字输出，模拟语音播放
        for char in sentence:
            print(char, end="", flush=True)
            time.sleep(0.02)  # 模拟语音速度
        time.sleep(0.3)  # 句子间停顿
    
    print(f"\n{Fore.YELLOW}{'='*70}\n")


def main():
    """主函数"""
    print_header()
    
    # 初始化Agent
    print(f"\n{Fore.CYAN}⏳ 正在初始化Agent...")
    agent = ReasoningAgent(verbose=False)  # 关闭默认verbose
    print(f"{Fore.GREEN}✅ Agent初始化完成！")
    print(f"{Fore.GREEN}   已加载 {len(agent.tools)} 个工具\n")
    
    print_examples()
    
    # 模式配置
    show_reasoning = True
    show_tts_simulation = True
    
    print(f"\n{Fore.CYAN}💬 当前模式：")
    print(f"   推理展示: {'开启' if show_reasoning else '关闭'}")
    print(f"   TTS模拟: {'开启' if show_tts_simulation else '关闭'}")
    
    # 交互循环
    while True:
        try:
            # 获取用户输入
            user_input = input(f"\n{Fore.CYAN}💬 您: {Style.RESET_ALL}").strip()
            
            # 退出命令
            if user_input.lower() in ['q', 'quit', 'exit', '退出']:
                print(f"\n{Fore.YELLOW}👋 再见！感谢使用AI Agent！\n")
                break
            
            # 帮助命令
            if user_input.lower() in ['help', '帮助', 'h']:
                print_examples()
                continue
            
            # 模式切换
            if user_input.lower() == 'mode':
                show_reasoning = not show_reasoning
                status = "开启" if show_reasoning else "关闭"
                print(f"\n{Fore.YELLOW}🔄 推理展示已{status}")
                continue
            
            # TTS模拟切换
            if user_input.lower() == 'tts':
                show_tts_simulation = not show_tts_simulation
                status = "开启" if show_tts_simulation else "关闭"
                print(f"\n{Fore.YELLOW}🔄 TTS模拟已{status}")
                continue
            
            # 空输入
            if not user_input:
                print(f"{Fore.RED}⚠️  请输入内容")
                continue
            
            # 执行Agent推理
            print(f"\n{Fore.MAGENTA}{'='*70}")
            print(f"{Fore.MAGENTA}🤔 Agent正在思考...")
            print(f"{Fore.MAGENTA}{'='*70}")
            
            result = agent.run_with_sentence_stream(
                user_input, 
                show_reasoning=show_reasoning
            )
            
            # 检查是否检测到对话结束
            should_end = False
            if result['success'] and result['step_count'] > 0:
                for step in result['reasoning_steps']:
                    if step['tool'] == 'end_conversation_detector':
                        if 'END_CONVERSATION' in step['output']:
                            should_end = True
                            print(f"\n{Fore.YELLOW}🔔 检测到结束意图，对话即将结束...")
                            break
            
            if result['success']:
                # 显示统计信息
                if result['step_count'] > 0:
                    print(f"\n{Fore.GREEN}✅ 推理完成！共执行了 {result['step_count']} 个推理步骤")
                else:
                    print(f"\n{Fore.GREEN}✅ 直接回答（无需工具）")
                
                # 模拟TTS输出
                if show_tts_simulation and len(result['sentences']) > 1:
                    simulate_tts_output(result['sentences'])
                else:
                    # 简单输出
                    print(f"\n{Fore.GREEN}💬 Agent回答: ")
                    print(f"{Fore.WHITE}{result['output']}\n")
            else:
                print(f"\n{Fore.RED}❌ 出错了: {result['output']}\n")
            
            # 如果检测到结束意图，自动结束程序
            if should_end:
                print(f"\n{Fore.YELLOW}👋 感谢使用！再见！\n")
                break
                
        except KeyboardInterrupt:
            print(f"\n\n{Fore.YELLOW}👋 程序被中断，再见！\n")
            break
        except Exception as e:
            print(f"\n{Fore.RED}❌ 发生错误: {str(e)}\n")
            import traceback
            traceback.print_exc()


def test_mode():
    """测试模式 - 快速验证所有工具"""
    print("\n" + "=" * 80)
    print(Fore.CYAN + Style.BRIGHT + "🧪 测试模式 - 验证所有新功能")
    print("=" * 80)
    
    agent = ReasoningAgent(verbose=False)
    
    test_cases = [
        ("数学计算", "计算sqrt(2)保留3位小数"),
        ("时间查询", "现在几点？"),
        ("文本分析", "统计'人工智能'有多少字"),
        ("单位转换", "100摄氏度等于多少华氏度"),
        ("数据比较", "比较：A:100,B:80,C:90，找出最大的"),
    ]
    
    for i, (category, query) in enumerate(test_cases, 1):
        print(f"\n{Fore.YELLOW}{'─'*70}")
        print(f"{Fore.YELLOW}测试 {i}/{len(test_cases)}: {category}")
        print(f"{Fore.YELLOW}{'─'*70}")
        print(f"{Fore.CYAN}输入: {query}")
        
        result = agent.run_with_sentence_stream(query, show_reasoning=True)
        
        if result['success']:
            print(f"{Fore.GREEN}✅ 测试通过")
        else:
            print(f"{Fore.RED}❌ 测试失败")
        
        time.sleep(1)
    
    print(f"\n{Fore.GREEN}{'='*80}")
    print(f"{Fore.GREEN}测试完成！")
    print(f"{Fore.GREEN}{'='*80}\n")


if __name__ == "__main__":
    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        test_mode()
    else:
        main()

