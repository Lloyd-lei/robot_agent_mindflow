"""
前台接待Agent演示程序
展示前台语音接待的实际应用场景
"""
from agent_hybrid import HybridReasoningAgent
import time

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False
    class Fore:
        CYAN = YELLOW = GREEN = MAGENTA = RED = BLUE = WHITE = LIGHTCYAN_EX = LIGHTYELLOW_EX = ""
    class Style:
        BRIGHT = RESET_ALL = ""


def print_banner():
    """打印欢迎横幅"""
    print("\n" + "="*80)
    print(Fore.CYAN + Style.BRIGHT + "🏢 智能前台接待Agent - 演示系统")
    print("="*80)
    print(Fore.GREEN + "\n✨ 功能展示：")
    print("  1️⃣  访客登记与签到")
    print("  2️⃣  会议室预订管理")
    print("  3️⃣  员工通讯录查询")
    print("  4️⃣  办公室路线指引")
    print("  5️⃣  快递包裹管理")
    print("  6️⃣  常见问题解答")
    print("\n" + Fore.YELLOW + "🎯 特点：")
    print("  • 智能信息提取 - 从对话中自动提取关键信息")
    print("  • 多工具协同 - 一个任务调用多个工具")
    print("  • 上下文理解 - KV Cache优化的对话记忆")
    print("  • 主动服务 - 提供相关建议和指引")
    print("="*80 + "\n")


def demo_scenario_1_visitor_registration(agent):
    """场景1：访客登记"""
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.CYAN}📋 场景1：访客签到流程")
    print(f"{Fore.CYAN}{'='*80}\n")
    
    scenarios = [
        "你好，我是来自华为公司的张伟，来找技术部的王明谈合作项目",
        "帮我查一下王明的联系方式",
        "技术部怎么走？",
    ]
    
    for i, query in enumerate(scenarios, 1):
        print(f"{Fore.YELLOW}访客/员工：{Fore.WHITE}{query}")
        print(f"{Fore.LIGHTCYAN_EX}Agent 思考中...\n")
        
        result = agent.run(query, show_reasoning=False)
        
        if result['success']:
            print(f"\n{Fore.GREEN}🤖 Agent：{Fore.WHITE}")
            for sentence in result['sentences']:
                print(f"  {sentence}")
            print(f"\n{Fore.MAGENTA}⚙️  调用了 {result['tool_calls']} 个工具")
        
        print()
        if i < len(scenarios):
            time.sleep(1)
    
    print(f"{Fore.CYAN}{'─'*80}\n")


def demo_scenario_2_meeting_room(agent):
    """场景2：会议室预订"""
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.CYAN}🏢 场景2：会议室预订")
    print(f"{Fore.CYAN}{'='*80}\n")
    
    scenarios = [
        "下午3点有空闲的会议室吗？需要10人的",
        "预订创新会议室，时间下午3点到5点，组织者是李娜",
        "创新会议室怎么走？",
    ]
    
    for i, query in enumerate(scenarios, 1):
        print(f"{Fore.YELLOW}员工：{Fore.WHITE}{query}")
        print(f"{Fore.LIGHTCYAN_EX}Agent 思考中...\n")
        
        result = agent.run(query, show_reasoning=False)
        
        if result['success']:
            print(f"\n{Fore.GREEN}🤖 Agent：{Fore.WHITE}")
            for sentence in result['sentences']:
                print(f"  {sentence}")
            print(f"\n{Fore.MAGENTA}⚙️  调用了 {result['tool_calls']} 个工具")
        
        print()
        if i < len(scenarios):
            time.sleep(1)
    
    print(f"{Fore.CYAN}{'─'*80}\n")


def demo_scenario_3_employee_directory(agent):
    """场景3：员工查询"""
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.CYAN}📞 场景3：员工通讯录查询")
    print(f"{Fore.CYAN}{'='*80}\n")
    
    scenarios = [
        "帮我找一下人力资源部的李娜",
        "能帮我呼叫她吗？",
    ]
    
    for i, query in enumerate(scenarios, 1):
        print(f"{Fore.YELLOW}访客：{Fore.WHITE}{query}")
        print(f"{Fore.LIGHTCYAN_EX}Agent 思考中...\n")
        
        result = agent.run(query, show_reasoning=False)
        
        if result['success']:
            print(f"\n{Fore.GREEN}🤖 Agent：{Fore.WHITE}")
            for sentence in result['sentences']:
                print(f"  {sentence}")
            print(f"\n{Fore.MAGENTA}⚙️  调用了 {result['tool_calls']} 个工具")
        
        print()
        if i < len(scenarios):
            time.sleep(1)
    
    print(f"{Fore.CYAN}{'─'*80}\n")


def demo_scenario_4_package(agent):
    """场景4：快递管理"""
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.CYAN}📦 场景4：快递包裹管理")
    print(f"{Fore.CYAN}{'='*80}\n")
    
    scenarios = [
        "有张伟的一个顺丰快递，单号SF1234567890",
        "我是张伟，查一下我的快递",
    ]
    
    for i, query in enumerate(scenarios, 1):
        role = "快递员" if i == 1 else "员工"
        print(f"{Fore.YELLOW}{role}：{Fore.WHITE}{query}")
        print(f"{Fore.LIGHTCYAN_EX}Agent 思考中...\n")
        
        result = agent.run(query, show_reasoning=False)
        
        if result['success']:
            print(f"\n{Fore.GREEN}🤖 Agent：{Fore.WHITE}")
            for sentence in result['sentences']:
                print(f"  {sentence}")
            print(f"\n{Fore.MAGENTA}⚙️  调用了 {result['tool_calls']} 个工具")
        
        print()
        if i < len(scenarios):
            time.sleep(1)
    
    print(f"{Fore.CYAN}{'─'*80}\n")


def demo_scenario_5_faq(agent):
    """场景5：常见问题"""
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.CYAN}❓ 场景5：常见问题解答")
    print(f"{Fore.CYAN}{'='*80}\n")
    
    scenarios = [
        "WiFi密码是什么？",
        "停车怎么办理？",
        "公司餐厅在哪里？",
    ]
    
    for i, query in enumerate(scenarios, 1):
        print(f"{Fore.YELLOW}访客：{Fore.WHITE}{query}")
        print(f"{Fore.LIGHTCYAN_EX}Agent 思考中...\n")
        
        result = agent.run(query, show_reasoning=False)
        
        if result['success']:
            print(f"\n{Fore.GREEN}🤖 Agent：{Fore.WHITE}")
            for sentence in result['sentences']:
                print(f"  {sentence}")
            print(f"\n{Fore.MAGENTA}⚙️  调用了 {result['tool_calls']} 个工具")
        
        print()
        if i < len(scenarios):
            time.sleep(1)
    
    print(f"{Fore.CYAN}{'─'*80}\n")


def demo_comprehensive_scenario(agent):
    """综合场景：完整的访客接待流程"""
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.CYAN}🎬 综合场景：完整访客接待流程")
    print(f"{Fore.CYAN}{'='*80}\n")
    
    print(f"{Fore.LIGHTYELLOW_EX}【场景描述】")
    print(f"一位来自ABC公司的访客到达前台，需要完成签到、")
    print(f"查找受访人、获取路线指引、了解停车信息等一系列流程。\n")
    
    conversation = [
        ("访客", "你好！"),
        ("访客", "我是ABC公司的刘强，来找技术部的张伟讨论项目"),
        ("访客", "停车怎么办理？我的车牌是京A12345"),
        ("访客", "张伟的办公室在哪里？"),
        ("访客", "好的，谢谢！我可以连WiFi吗？"),
        ("访客", "太好了，谢谢你的帮助！"),
    ]
    
    for i, (role, query) in enumerate(conversation, 1):
        print(f"{Fore.YELLOW}{role}：{Fore.WHITE}{query}")
        print(f"{Fore.LIGHTCYAN_EX}Agent 思考中...\n")
        
        result = agent.run(query, show_reasoning=False)
        
        if result['success']:
            print(f"\n{Fore.GREEN}🤖 Agent：{Fore.WHITE}")
            for sentence in result['sentences']:
                print(f"  {sentence}")
            
            if result['tool_calls'] > 0:
                print(f"\n{Fore.MAGENTA}⚙️  调用了 {result['tool_calls']} 个工具：", end="")
                tools_used = [step['tool'] for step in result['reasoning_steps']]
                print(f" {', '.join(tools_used)}")
        
        print()
        if i < len(conversation):
            time.sleep(1.5)
    
    print(f"{Fore.CYAN}{'─'*80}\n")


def interactive_mode(agent):
    """交互模式"""
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.CYAN}💬 进入交互模式")
    print(f"{Fore.CYAN}{'='*80}\n")
    
    print(f"{Fore.GREEN}现在您可以作为访客或员工与前台Agent对话。")
    print(f"{Fore.GREEN}输入 'q' 或 'quit' 退出交互模式。\n")
    
    turn = 0
    while True:
        try:
            user_input = input(f"{Fore.YELLOW}您：{Style.RESET_ALL}").strip()
            
            if user_input.lower() in ['q', 'quit', 'exit', '退出']:
                print(f"\n{Fore.CYAN}返回主菜单...\n")
                break
            
            if not user_input:
                continue
            
            turn += 1
            print(f"{Fore.LIGHTCYAN_EX}Agent 思考中...\n")
            
            result = agent.run(user_input, show_reasoning=False)
            
            if result['success']:
                print(f"\n{Fore.GREEN}🤖 Agent：{Fore.WHITE}")
                for sentence in result['sentences']:
                    print(f"  {sentence}")
                
                if result['tool_calls'] > 0:
                    tools_used = [step['tool'] for step in result['reasoning_steps']]
                    print(f"\n{Fore.MAGENTA}⚙️  调用工具：{', '.join(tools_used)}")
                
                # 检查是否需要结束
                if result.get('should_end'):
                    print(f"\n{Fore.YELLOW}检测到对话结束信号，返回主菜单...\n")
                    break
            else:
                print(f"\n{Fore.RED}❌ 出错了：{result['output']}\n")
            
            print()
            
        except KeyboardInterrupt:
            print(f"\n\n{Fore.CYAN}返回主菜单...\n")
            break
        except Exception as e:
            print(f"\n{Fore.RED}❌ 错误：{str(e)}\n")


def main():
    """主程序"""
    print_banner()
    
    print(f"{Fore.CYAN}⏳ 正在初始化前台接待Agent...")
    start_time = time.time()
    agent = HybridReasoningAgent(enable_cache=True)
    init_time = time.time() - start_time
    print(f"{Fore.GREEN}✅ 初始化完成！耗时: {init_time:.2f}秒\n")
    
    while True:
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"{Fore.CYAN}📋 选择演示场景")
        print(f"{Fore.CYAN}{'='*80}\n")
        
        print(f"{Fore.GREEN}1. 访客登记与签到")
        print(f"{Fore.GREEN}2. 会议室预订管理")
        print(f"{Fore.GREEN}3. 员工通讯录查询")
        print(f"{Fore.GREEN}4. 快递包裹管理")
        print(f"{Fore.GREEN}5. 常见问题解答")
        print(f"{Fore.GREEN}6. 综合场景演示（推荐）")
        print(f"{Fore.GREEN}7. 交互模式（自由对话）")
        print(f"{Fore.GREEN}8. 查看缓存统计")
        print(f"{Fore.GREEN}9. 清除对话历史")
        print(f"{Fore.RED}0. 退出程序\n")
        
        try:
            choice = input(f"{Fore.YELLOW}请选择 (0-9)：{Style.RESET_ALL}").strip()
            
            if choice == '0':
                print(f"\n{Fore.YELLOW}👋 感谢使用！再见！\n")
                break
            elif choice == '1':
                demo_scenario_1_visitor_registration(agent)
            elif choice == '2':
                demo_scenario_2_meeting_room(agent)
            elif choice == '3':
                demo_scenario_3_employee_directory(agent)
            elif choice == '4':
                demo_scenario_4_package(agent)
            elif choice == '5':
                demo_scenario_5_faq(agent)
            elif choice == '6':
                demo_comprehensive_scenario(agent)
            elif choice == '7':
                interactive_mode(agent)
            elif choice == '8':
                stats = agent.get_cache_stats()
                print(f"\n{Fore.CYAN}{'='*70}")
                print(f"{Fore.CYAN}📊 KV Cache 统计")
                print(f"{Fore.CYAN}{'='*70}")
                print(f"{Fore.GREEN}对话轮次：{stats['conversation_turns']}")
                print(f"{Fore.GREEN}缓存tokens：~{stats['estimated_cached_tokens']} tokens")
                print(f"{Fore.GREEN}系统提示词：~{stats['system_prompt_tokens']} tokens (已缓存)")
                if stats['conversation_turns'] > 0:
                    saved = int(stats['estimated_cached_tokens'] * 0.5)
                    print(f"{Fore.YELLOW}💰 预估节省：~{saved} tokens")
                print(f"{Fore.CYAN}{'='*70}\n")
            elif choice == '9':
                agent.clear_cache()
                print(f"\n{Fore.GREEN}✅ 对话历史已清除\n")
            else:
                print(f"\n{Fore.RED}❌ 无效选择，请重新输入\n")
                
        except KeyboardInterrupt:
            print(f"\n\n{Fore.YELLOW}👋 程序被中断，再见！\n")
            break
        except Exception as e:
            print(f"\n{Fore.RED}❌ 发生错误：{str(e)}\n")


if __name__ == "__main__":
    main()

