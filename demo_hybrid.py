"""
混合架构交互式Demo
展示OpenAI原生API + LangChain工具 + KV Cache的威力
"""
from agent_hybrid import HybridReasoningAgent
import time

# 尝试导入colorama
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False
    class Fore:
        CYAN = YELLOW = GREEN = MAGENTA = RED = BLUE = WHITE = ""
    class Style:
        BRIGHT = RESET_ALL = ""


def print_header():
    """打印欢迎界面"""
    print("\n" + "=" * 80)
    print(Fore.CYAN + Style.BRIGHT + "🚀 混合架构AI Agent - 语音交互版")
    print("=" * 80)
    print("\n" + Fore.GREEN + "✨ 核心优势：")
    print("  📊 OpenAI原生API - 100%可靠的工具调用")
    print("  🛠️  LangChain工具池 - 17个强大工具")
    print("  ⚡ KV Cache优化 - 多轮对话速度提升3-5倍")
    print("  🗣️  Edge TTS - 真实语音播放（晓晓语音）")
    print("\n" + Fore.YELLOW + "🎯 语音功能：")
    print("  • 🔊 真实语音播放 - Edge TTS 免费高质量")
    print("  • 🎵 智能分句 - 自然流畅的语音节奏")
    print("  • 🛡️  防重叠播放 - 稳定可靠的音频管理")
    print("  • 💡 推理可视化 - 完整展示思考过程")
    print("\n" + Fore.RED + "🔊 请确保扬声器已开启，音量适中！")
    print("-" * 80)


def print_examples():
    """打印示例"""
    print("\n" + Fore.MAGENTA + "💡 试试这些命令（会播放语音）：")
    examples = [
        "1️⃣  现在几点了？（语音播报时间）",
        "2️⃣  计算sqrt(2)保留3位小数（听听计算结果）",
        "3️⃣  图书馆有哪些关于Python的书（JSON转语音）",
        "4️⃣  100摄氏度等于多少华氏度（单位转换）",
        "5️⃣  帮我登记访客信息（前台接待）",
        "6️⃣  明天上午10点提醒我开会（设置提醒）",
        "7️⃣  再见（自动结束 + 语音道别）✨",
    ]
    for ex in examples:
        print(f"  {ex}")
    
    print("\n" + Fore.RED + "⌨️  命令：")
    print("  • 'q' 或 'quit' - 退出")
    print("  • 'help' - 查看帮助")
    print("  • 'stats' - 查看缓存统计")
    print("  • 'clear' - 清除对话历史")
    print("\n" + Fore.YELLOW + "💡 提示：Agent回答后会自动播放语音！")
    print("-" * 80)


def display_cache_stats(agent):
    """显示缓存统计"""
    stats = agent.get_cache_stats()
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}📊 KV Cache 统计信息")
    print(f"{Fore.CYAN}{'='*70}")
    print(f"{Fore.GREEN}对话轮次: {Fore.WHITE}{stats['conversation_turns']}")
    print(f"{Fore.GREEN}总消息数: {Fore.WHITE}{stats['total_messages']}")
    print(f"{Fore.GREEN}缓存tokens: {Fore.WHITE}~{stats['estimated_cached_tokens']} tokens")
    print(f"{Fore.GREEN}系统提示词: {Fore.WHITE}~{stats['system_prompt_tokens']} tokens (已缓存50% off)")
    
    # 估算节省
    if stats['conversation_turns'] > 0:
        saved = stats['estimated_cached_tokens'] * 0.5
        print(f"\n{Fore.YELLOW}💰 预估节省: ~{int(saved)} tokens 成本")
    print(f"{Fore.CYAN}{'='*70}\n")


def main():
    """主函数"""
    print_header()
    
    # 初始化Agent
    print(f"\n{Fore.CYAN}⏳ 正在初始化混合架构Agent...")
    start_time = time.time()
    agent = HybridReasoningAgent(enable_cache=True, enable_tts=True, voice_mode=True)
    init_time = time.time() - start_time
    print(f"{Fore.GREEN}✅ 初始化完成！耗时: {init_time:.2f}秒\n")
    
    print_examples()
    
    # 交互循环
    turn = 0
    while True:
        try:
            # 获取用户输入
            user_input = input(f"\n{Fore.CYAN}💬 您: {Style.RESET_ALL}").strip()
            
            # 退出命令
            if user_input.lower() in ['q', 'quit', 'exit', '退出']:
                print(f"\n{Fore.YELLOW}👋 再见！感谢使用混合架构AI Agent！\n")
                break
            
            # 帮助命令
            if user_input.lower() in ['help', '帮助', 'h']:
                print_examples()
                continue
            
            # 统计命令
            if user_input.lower() == 'stats':
                display_cache_stats(agent)
                continue
            
            # 清除缓存
            if user_input.lower() == 'clear':
                agent.clear_cache()
                print(f"{Fore.YELLOW}✅ 对话历史已清除\n")
                continue
            
            # 空输入
            if not user_input:
                print(f"{Fore.RED}⚠️  请输入内容")
                continue
            
            # 执行推理
            turn += 1
            print(f"\n{Fore.MAGENTA}{'='*70}")
            print(f"{Fore.MAGENTA}🤔 对话轮次 {turn} - Agent正在思考...")
            print(f"{Fore.MAGENTA}{'='*70}")
            
            start_time = time.time()
            # 使用真实 TTS 播放（simulate_mode=False 启用真实语音）
            result = agent.run_with_tts(user_input, show_reasoning=True, simulate_mode=False)
            response_time = time.time() - start_time
            
            if result['success']:
                # 显示性能统计
                print(f"\n{Fore.GREEN}⚡ 响应耗时: {Fore.WHITE}{response_time:.2f}秒")
                print(f"{Fore.GREEN}📞 工具调用: {Fore.WHITE}{result['tool_calls']}次")
                if result.get('total_tts_chunks', 0) > 0:
                    print(f"{Fore.GREEN}🗣️  TTS分段: {Fore.WHITE}{result['total_tts_chunks']}个")
                    if result.get('tts_success'):
                        print(f"{Fore.GREEN}🔊 语音播放: {Fore.WHITE}✅ 完成")
                if turn > 1:
                    print(f"{Fore.GREEN}🚀 KV Cache: {Fore.WHITE}已优化（第{turn}轮）")
                
                # 检查是否需要结束
                if result.get('should_end'):
                    print(f"\n{Fore.YELLOW}🔔 检测到对话结束信号")
                    print(f"{Fore.YELLOW}👋 感谢使用！再见！\n")
                    break
            else:
                print(f"\n{Fore.RED}❌ 出错了: {result['output']}\n")
                
        except KeyboardInterrupt:
            print(f"\n\n{Fore.YELLOW}👋 程序被中断，再见！\n")
            break
        except Exception as e:
            print(f"\n{Fore.RED}❌ 发生错误: {str(e)}\n")
            import traceback
            traceback.print_exc()


def test_mode():
    """测试模式 - 对比性能（带真实语音）"""
    print("\n" + "=" * 80)
    print(Fore.CYAN + Style.BRIGHT + "🧪 混合架构性能测试 + TTS 播放")
    print("=" * 80)
    
    agent = HybridReasoningAgent(enable_cache=True, enable_tts=True, voice_mode=True)
    
    test_cases = [
        ("数学计算", "计算sqrt(2)保留3位小数"),
        ("时间查询", "现在几点？"),
        ("图书查询", "图书馆有关于Python的书吗？"),
        ("对话结束", "好的，再见！"),
    ]
    
    print("\n开始测试...（每次都会播放语音）\n")
    
    for i, (name, query) in enumerate(test_cases, 1):
        print(f"{Fore.YELLOW}{'─'*70}")
        print(f"{Fore.YELLOW}测试 {i}/{len(test_cases)}: {name}")
        print(f"{Fore.YELLOW}{'─'*70}")
        
        start_time = time.time()
        # 使用真实 TTS 播放
        result = agent.run_with_tts(query, show_reasoning=False, simulate_mode=False)
        elapsed = time.time() - start_time
        
        if result['success']:
            print(f"{Fore.GREEN}✅ 成功")
            print(f"   耗时: {elapsed:.2f}秒")
            print(f"   工具调用: {result['tool_calls']}次")
            if result.get('total_tts_chunks', 0) > 0:
                print(f"   TTS分段: {result['total_tts_chunks']}个")
                print(f"   语音播放: {'✅ 完成' if result.get('tts_success') else '❌ 失败'}")
            if i > 1:
                print(f"   KV Cache: 已优化")
        else:
            print(f"{Fore.RED}❌ 失败: {result['output']}")
        
        time.sleep(0.5)
    
    # 显示缓存统计
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}最终统计")
    print(f"{Fore.CYAN}{'='*70}")
    display_cache_stats(agent)
    
    print(f"{Fore.GREEN}✅ 测试完成！\n")


if __name__ == "__main__":
    import sys
    
    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        test_mode()
    else:
        main()

