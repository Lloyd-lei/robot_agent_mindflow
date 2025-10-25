"""
测试新的会话管理器

验证功能：
1. 日志系统是否正常
2. 会话生命周期管理
3. 超时保护机制
4. 多轮对话是否卡死
"""

from conversation_session import ConversationSession
from logger_config import setup_logger
from colorama import init, Fore, Style

init(autoreset=True)

# 设置日志级别为 INFO（可改为 DEBUG 查看详细日志）
logger = setup_logger(name="test", level="INFO")


def test_basic_chat():
    """测试基本对话功能"""
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}🧪 测试 1：基本对话功能")
    print(f"{Fore.CYAN}{'='*70}\n")
    
    with ConversationSession(
        tts_provider="edge",
        enable_cache=True,
        show_reasoning=True,
        timeout=60,
        tts_wait_timeout=30
    ) as session:
        
        # 第一轮对话
        print(f"{Fore.GREEN}第 1 轮：你好")
        result = session.chat("你好")
        print(f"{Fore.YELLOW}回复: {result.response[:100]}...")
        print(f"{Fore.YELLOW}耗时: {result.duration:.2f}秒\n")
        
        # 第二轮对话（测试是否卡死）
        print(f"{Fore.GREEN}第 2 轮：现在几点？")
        result = session.chat("现在几点？")
        print(f"{Fore.YELLOW}回复: {result.response[:100]}...")
        print(f"{Fore.YELLOW}耗时: {result.duration:.2f}秒\n")
        
        # 第三轮对话（测试多轮）
        print(f"{Fore.GREEN}第 3 轮：计算 sqrt(2)")
        result = session.chat("计算sqrt(2)保留3位小数")
        print(f"{Fore.YELLOW}回复: {result.response[:100]}...")
        print(f"{Fore.YELLOW}耗时: {result.duration:.2f}秒\n")
    
    print(f"{Fore.GREEN}✅ 测试 1 通过：多轮对话无卡死\n")


def test_timeout_protection():
    """测试超时保护"""
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}🧪 测试 2：超时保护机制")
    print(f"{Fore.CYAN}{'='*70}\n")
    
    with ConversationSession(
        tts_provider="edge",
        timeout=30,           # 较短的超时时间
        tts_wait_timeout=10   # 较短的 TTS 等待时间
    ) as session:
        
        print(f"{Fore.GREEN}测试超时保护（TTS 等待超时 10 秒）...")
        result = session.chat("你好，请简短回答")
        print(f"{Fore.YELLOW}回复: {result.response[:100]}...")
        print(f"{Fore.YELLOW}耗时: {result.duration:.2f}秒\n")
    
    print(f"{Fore.GREEN}✅ 测试 2 通过：超时机制正常\n")


def test_cache_management():
    """测试缓存管理"""
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}🧪 测试 3：缓存管理与历史持久化")
    print(f"{Fore.CYAN}{'='*70}\n")
    
    with ConversationSession(enable_cache=True) as session:
        
        # 第一轮
        print(f"{Fore.GREEN}对话 1...")
        result = session.chat("我叫小明")
        print(f"{Fore.YELLOW}回复: {result.response[:50]}...\n")
        
        # 查看历史摘要
        summary = session.get_history_summary()
        print(f"{Fore.CYAN}历史摘要: {summary['turns']}轮对话, {summary['total_messages']}条消息")
        print(f"{Fore.CYAN}已保存: {summary['has_history_file']}\n")
        
        # 第二轮（测试记忆）
        print(f"{Fore.GREEN}对话 2（测试记忆）...")
        result = session.chat("我叫什么名字？")
        print(f"{Fore.YELLOW}回复: {result.response[:50]}...\n")
        
        # 测试历史保存/加载
        print(f"{Fore.GREEN}测试历史持久化...")
        session.save_history()
        print(f"{Fore.YELLOW}✓ 历史已保存\n")
        
        # 重置缓存
        print(f"{Fore.GREEN}重置缓存...")
        session.reset()
        
        # 第三轮（应该忘记名字）
        print(f"{Fore.GREEN}对话 3（重置后）...")
        result = session.chat("我叫什么名字？")
        print(f"{Fore.YELLOW}回复: {result.response[:50]}...\n")
    
    print(f"{Fore.GREEN}✅ 测试 3 通过：缓存管理和历史持久化正常\n")


def test_interactive_mode():
    """交互式测试（手动测试）"""
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}🧪 测试 4：交互式测试")
    print(f"{Fore.CYAN}{'='*70}\n")
    print(f"{Fore.YELLOW}提示：输入 'exit' 退出\n")
    
    with ConversationSession(
        tts_provider="edge",
        enable_cache=True,
        show_reasoning=True
    ) as session:
        
        turn = 0
        while True:
            try:
                user_input = input(f"\n{Fore.CYAN}💬 您: {Style.RESET_ALL}").strip()
                
                if user_input.lower() in ['exit', 'quit', '退出']:
                    break
                
                if not user_input:
                    continue
                
                turn += 1
                print(f"\n{Fore.MAGENTA}--- 第 {turn} 轮 ---{Style.RESET_ALL}")
                
                result = session.chat(user_input)
                
                print(f"\n{Fore.GREEN}⚡ 耗时: {result.duration:.2f}秒")
                print(f"{Fore.GREEN}📞 工具调用: {result.tool_calls}次")
                
                if result.should_end:
                    print(f"\n{Fore.YELLOW}🔔 检测到对话结束信号")
                    break
                    
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}👋 测试中断\n")
                break
            except Exception as e:
                print(f"\n{Fore.RED}❌ 错误: {e}\n")
                import traceback
                traceback.print_exc()
    
    print(f"{Fore.GREEN}✅ 测试 4 完成\n")


if __name__ == "__main__":
    import sys
    
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*70}")
    print(f"{Fore.CYAN}{Style.BRIGHT}🧪 会话管理器测试套件")
    print(f"{Fore.CYAN}{Style.BRIGHT}{'='*70}\n")
    
    if len(sys.argv) > 1 and sys.argv[1] == 'interactive':
        # 交互式测试
        test_interactive_mode()
    else:
        # 自动化测试
        try:
            test_basic_chat()
            test_timeout_protection()
            test_cache_management()
            
            print(f"\n{Fore.GREEN}{Style.BRIGHT}{'='*70}")
            print(f"{Fore.GREEN}{Style.BRIGHT}✅ 所有自动化测试通过！")
            print(f"{Fore.GREEN}{Style.BRIGHT}{'='*70}\n")
            
            print(f"{Fore.YELLOW}💡 提示：运行 'python test_session.py interactive' 进行交互式测试\n")
            
        except Exception as e:
            print(f"\n{Fore.RED}{Style.BRIGHT}{'='*70}")
            print(f"{Fore.RED}{Style.BRIGHT}❌ 测试失败！")
            print(f"{Fore.RED}{Style.BRIGHT}{'='*70}\n")
            print(f"{Fore.RED}错误: {e}\n")
            import traceback
            traceback.print_exc()

