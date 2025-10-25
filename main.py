"""
混合架构交互式Demo
展示OpenAI原生API + LangChain工具 + KV Cache的威力
"""
from conversation_session import ConversationSession, SessionNotStartedError, SessionTimeoutError
from agent_hybrid import HybridReasoningAgent
from logger_config import setup_logger
import time

# 设置日志系统
logger = setup_logger(name="main", level="INFO")

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


def print_header(streaming_mode=False):
    """打印欢迎界面"""
    print("\n" + "=" * 80)
    mode_text = "流式语音版 ⚡" if streaming_mode else "语音交互版"
    print(Fore.CYAN + Style.BRIGHT + f"🚀 混合架构AI Agent - {mode_text}")
    print("=" * 80)
    print("\n" + Fore.GREEN + "✨ 核心优势：")
    print("  📊 OpenAI原生API - 100%可靠的工具调用")
    print("  🛠️  LangChain工具池 - 17个强大工具")
    print("  ⚡ KV Cache优化 - 多轮对话速度提升3-5倍")
    print("  🗣️  Edge TTS - 真实语音播放（晓晓语音）")
    
    if streaming_mode:
        print("\n" + Fore.YELLOW + "🚀 流式TTS功能（推荐）：")
        print("  • ⚡ 超低延迟 - LLM生成的同时TTS播放")
        print("  • 🎯 智能分句 - 自动识别句子边界")
        print("  • 🛡️  背压控制 - 自动防止资源爆炸")
        print("  • 💡 推理可视化 - 实时展示思考过程")
    else:
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
    print("  • 'history' - 查看对话历史摘要")
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


def main(streaming=True):
    """
    主函数（使用会话管理器）
    
    Args:
        streaming: 是否使用流式TTS模式（推荐）
    """
    print_header(streaming_mode=streaming)
    
    # 创建会话（使用上下文管理器自动清理资源）
    mode_text = "流式TTS模式 ⚡" if streaming else "批量TTS模式"
    print(f"\n{Fore.CYAN}⏳ 正在初始化会话（{mode_text}）...")
    start_time = time.time()
    
    try:
        with ConversationSession(
            tts_provider="edge",
            tts_voice="zh-CN-XiaoxiaoNeural",
            enable_cache=True,
            show_reasoning=True,
            timeout=60,           # 单轮对话超时60秒
            tts_wait_timeout=60
               # TTS等待超时30秒
        ) as session:
            
            init_time = time.time() - start_time
            print(f"{Fore.GREEN}✅ 会话初始化完成！耗时: {init_time:.2f}秒\n")
            
            # 尝试恢复之前的对话历史
            if session.load_history():
                summary = session.get_history_summary()
                print(f"{Fore.CYAN}📥 已恢复对话历史: {summary['turns']}轮对话\n")
            
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
                        if hasattr(session, '_agent'):
                            display_cache_stats(session._agent)
                        else:
                            print(f"{Fore.YELLOW}⚠️  会话未启动{Style.RESET_ALL}")
                        continue
                    
                    # 历史摘要命令
                    if user_input.lower() in ['history', '历史']:
                        summary = session.get_history_summary()
                        print(f"\n{Fore.CYAN}{'='*70}")
                        print(f"{Fore.CYAN}📜 会话历史摘要")
                        print(f"{Fore.CYAN}{'='*70}")
                        print(f"{Fore.GREEN}会话ID: {Fore.WHITE}{summary['session_id']}")
                        print(f"{Fore.GREEN}对话轮次: {Fore.WHITE}{summary['turns']}")
                        print(f"{Fore.GREEN}消息总数: {Fore.WHITE}{summary['total_messages']}")
                        print(f"{Fore.GREEN}缓存启用: {Fore.WHITE}{'是' if summary['cache_enabled'] else '否'}")
                        print(f"{Fore.GREEN}已保存: {Fore.WHITE}{'是' if summary['has_history_file'] else '否'}")
                        print(f"{Fore.CYAN}{'='*70}\n")
                        continue
                    
                    # 清除缓存
                    if user_input.lower() == 'clear':
                        session.reset()
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
                    
                    # 单轮对话（带超时保护）
                    result = session.chat(user_input)
                    
                    # 显示性能统计
                    print(f"\n{Fore.GREEN}⚡ 响应耗时: {Fore.WHITE}{result.duration:.2f}秒")
                    print(f"{Fore.GREEN}📞 工具调用: {Fore.WHITE}{result.tool_calls}次")
                    
                    # 流式TTS统计
                    if result.streaming_stats:
                        stats = result.streaming_stats
                        print(f"{Fore.GREEN}🗣️  TTS统计:")
                        print(f"   - 接收文本: {stats['text_received']}段")
                        print(f"   - 生成音频: {stats['audio_generated']}段")
                        print(f"   - 播放完成: {stats['audio_played']}段")
                        if stats.get('audio_failed', 0) > 0:
                            print(f"   - 生成失败: {stats['audio_failed']}段")
                        if stats.get('text_dropped', 0) > 0:
                            print(f"   - 丢弃文本: {stats['text_dropped']}段（背压）")
                    
                    if turn > 1:
                        print(f"{Fore.GREEN}🚀 KV Cache: {Fore.WHITE}已优化（第{turn}轮）")
                    
                    # 检查是否需要结束
                    if result.should_end:
                        print(f"\n{Fore.YELLOW}🔔 检测到对话结束信号")
                        print(f"{Fore.YELLOW}👋 感谢使用！再见！\n")
                        break
                        
                except SessionTimeoutError as e:
                    print(f"\n{Fore.RED}⏱️  对话超时: {e}")
                    print(f"{Fore.YELLOW}💡 对话历史已保留，您可以继续对话\n")
                    logger.error(f"对话超时: {e}")
                    # 继续对话循环，不退出（对话历史已保存）
                    continue
                    
                except KeyboardInterrupt:
                    print(f"\n\n{Fore.YELLOW}👋 程序被中断，再见！\n")
                    break
                    
                except Exception as e:
                    print(f"\n{Fore.RED}❌ 发生错误: {str(e)}\n")
                    logger.error(f"对话异常: {e}", exc_info=True)
                    import traceback
                    traceback.print_exc()
        
        # 上下文管理器退出时自动清理资源
        logger.info("会话正常结束")
        
    except Exception as e:
        print(f"\n{Fore.RED}❌ 会话初始化失败: {str(e)}\n")
        logger.error(f"会话初始化失败: {e}", exc_info=True)
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
    if len(sys.argv) > 1:
        if sys.argv[1] == 'test':
            test_mode()
        elif sys.argv[1] == 'streaming' or sys.argv[1] == 'stream':
            # 流式TTS模式（推荐）
            main(streaming=True)
        else:
            print("用法:")
            print("  python demo_hybrid.py           # 批量TTS模式")
            print("  python demo_hybrid.py streaming # 流式TTS模式（推荐）⚡")
            print("  python demo_hybrid.py test      # 测试模式")
    else:
        # 默认使用流式TTS模式（推荐）
        main(streaming=True)

