"""
TTS优化测试程序
展示TTS文本优化和音频管理的效果
"""
from agent_hybrid import HybridReasoningAgent
import time

# 颜色支持
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class Fore:
        CYAN = YELLOW = GREEN = MAGENTA = RED = WHITE = ""
    class Style:
        BRIGHT = RESET_ALL = ""


def print_header():
    """打印标题"""
    print("\n" + "="*80)
    print(Fore.CYAN + Style.BRIGHT + "🎵 TTS优化系统测试")
    print("="*80)
    print(Fore.GREEN + "\n本测试将展示：")
    print("  1. 文本优化（清理格式、智能分句）")
    print("  2. TTS双轨输出（原始文本 vs TTS结构）")
    print("  3. 音频播放模拟（防重叠、处理乱序）")
    print("  4. 语音等待反馈")
    print("="*80 + "\n")


def test_text_optimization():
    """测试1：文本优化"""
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.CYAN}测试1：文本优化功能")
    print(f"{Fore.CYAN}{'='*80}\n")
    
    # 初始化Agent（启用TTS）
    agent = HybridReasoningAgent(
        enable_cache=True,
        enable_tts=True,
        voice_mode=True
    )
    
    # 测试查询
    test_query = "图书馆有哪些关于Python的书？"
    print(f"{Fore.YELLOW}用户: {test_query}\n")
    
    # 执行并展示双轨输出
    result = agent.run_with_tts_demo(test_query, show_text_and_tts=True)
    
    if result['success']:
        print(f"\n{Fore.GREEN}✅ 文本优化成功")
        if 'tts_chunks' in result:
            print(f"{Fore.GREEN}   生成了 {result['total_tts_chunks']} 个TTS分段")


def test_audio_playback():
    """测试2：音频播放模拟"""
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.CYAN}测试2：音频播放模拟（防重叠、处理乱序）")
    print(f"{Fore.CYAN}{'='*80}\n")
    
    # 初始化Agent
    agent = HybridReasoningAgent(
        enable_cache=True,
        enable_tts=True,
        voice_mode=True
    )
    
    # 测试查询
    test_query = "计算1+1，然后告诉我现在几点"
    print(f"{Fore.YELLOW}用户: {test_query}\n")
    
    # 执行推理并播放TTS（模拟模式）
    result = agent.run_with_tts(test_query, show_reasoning=False, simulate_mode=True)
    
    if result['success']:
        print(f"\n{Fore.GREEN}✅ 音频播放测试完成")
        if 'tts_success' in result:
            print(f"{Fore.GREEN}   TTS播放: {'成功' if result['tts_success'] else '部分失败'}")


def test_json_handling():
    """测试3：JSON结果处理"""
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.CYAN}测试3：JSON结果熔炼（自然语言转换）")
    print(f"{Fore.CYAN}{'='*80}\n")
    
    agent = HybridReasoningAgent(
        enable_cache=True,
        enable_tts=True,
        voice_mode=True
    )
    
    # 测试会返回JSON的查询
    test_query = "查询所有图书"
    print(f"{Fore.YELLOW}用户: {test_query}\n")
    
    result = agent.run_with_tts_demo(test_query, show_text_and_tts=True)
    
    if result['success']:
        print(f"\n{Fore.GREEN}✅ JSON处理测试完成")
        print(f"{Fore.GREEN}   模型已将JSON转换为自然语言")


def test_long_response():
    """测试4：长回答分段"""
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.CYAN}测试4：长回答的智能分段")
    print(f"{Fore.CYAN}{'='*80}\n")
    
    agent = HybridReasoningAgent(
        enable_cache=True,
        enable_tts=True,
        voice_mode=False
    )
    
    # 请求详细回答
    test_query = "给我详细介绍一下图书馆里的Python编程书籍"
    print(f"{Fore.YELLOW}用户: {test_query}\n")
    
    result = agent.run_with_tts_demo(test_query, show_text_and_tts=True)
    
    if result['success']:
        print(f"\n{Fore.GREEN}✅ 长回答分段测试完成")


def interactive_tts_test():
    """交互式TTS测试"""
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.CYAN}交互式TTS测试模式")
    print(f"{Fore.CYAN}{'='*80}\n")
    
    print(f"{Fore.GREEN}您可以输入任何问题，查看TTS优化效果")
    print(f"{Fore.GREEN}输入 'q' 退出\n")
    
    agent = HybridReasoningAgent(
        enable_cache=True,
        enable_tts=True,
        voice_mode=True
    )
    
    while True:
        try:
            user_input = input(f"\n{Fore.YELLOW}💬 您: {Style.RESET_ALL}").strip()
            
            if user_input.lower() in ['q', 'quit', 'exit']:
                print(f"\n{Fore.CYAN}退出测试模式\n")
                break
            
            if not user_input:
                continue
            
            # 显示双轨输出
            result = agent.run_with_tts_demo(user_input, show_text_and_tts=True)
            
        except KeyboardInterrupt:
            print(f"\n\n{Fore.CYAN}退出测试模式\n")
            break
        except Exception as e:
            print(f"\n{Fore.RED}错误: {e}\n")


def main():
    """主函数"""
    print_header()
    
    while True:
        print(f"\n{Fore.CYAN}选择测试项目：")
        print("  1. 文本优化测试")
        print("  2. 音频播放模拟")
        print("  3. JSON结果处理")
        print("  4. 长回答分段")
        print("  5. 交互式测试")
        print("  6. 运行所有测试")
        print("  0. 退出")
        
        choice = input(f"\n{Fore.YELLOW}请选择 (0-6): {Style.RESET_ALL}").strip()
        
        if choice == '0':
            print(f"\n{Fore.GREEN}👋 再见！\n")
            break
        elif choice == '1':
            test_text_optimization()
        elif choice == '2':
            test_audio_playback()
        elif choice == '3':
            test_json_handling()
        elif choice == '4':
            test_long_response()
        elif choice == '5':
            interactive_tts_test()
        elif choice == '6':
            test_text_optimization()
            time.sleep(2)
            test_audio_playback()
            time.sleep(2)
            test_json_handling()
            time.sleep(2)
            test_long_response()
        else:
            print(f"{Fore.RED}无效选择\n")


if __name__ == "__main__":
    main()

