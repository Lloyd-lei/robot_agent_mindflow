"""
Robot Agent Mindflow - 主入口
支持语音交互的混合架构 AI Agent

使用方式:
    python main.py              # 启动交互式对话
    python main.py --no-tts     # 禁用语音
    python main.py --test       # 测试模式
"""
import sys
from pathlib import Path

# 添加src目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core import HybridReasoningAgent
from src.core.config import settings
from src.tools import load_all_tools
from src.services.tts import TTSFactory, TTSProvider, TTSOptimizer
from src.services.voice import VoiceWaitingFeedback
import argparse
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
    print("\n" + "="*80)
    print(Fore.CYAN + Style.BRIGHT + "🚀 Robot Agent Mindflow - 语音交互版")
    print("="*80)
    print("\n" + Fore.GREEN + "✨ 核心优势:")
    print("  📊 OpenAI原生API - 100%可靠的工具调用")
    print("  🛠️  LangChain工具池 - 17个强大工具")
    print("  ⚡ KV Cache优化 - 多轮对话速度提升3-5倍")
    print("  🗣️  Edge TTS - 真实语音播放(晓晓语音)")
    print("\n" + Fore.YELLOW + "🎯 新架构特性:")
    print("  • 🏗️  分层架构 - Core / Services / Tools")
    print("  • 🔧 模块化设计 - 易于维护和扩展")
    print("  • ⚙️  配置管理 - Pydantic类型验证")
    print("  • 📖 完整文档 - 架构设计 + 迁移指南")
    print("-"*80)


def print_examples():
    """打印示例"""
    print("\n" + Fore.MAGENTA + "💡 试试这些命令(会播放语音):")
    examples = [
        "1️⃣  现在几点了?(语音播报时间)",
        "2️⃣  计算sqrt(2)保留3位小数(听听计算结果)",
        "3️⃣  图书馆有哪些关于Python的书(JSON转语音)",
        "4️⃣  100摄氏度等于多少华氏度(单位转换)",
        "5️⃣  帮我登记访客信息(前台接待)",
        "6️⃣  明天上午10点提醒我开会(设置提醒)",
        "7️⃣  再见(自动结束 + 语音道别)✨",
    ]
    for ex in examples:
        print(f"  {ex}")

    print("\n" + Fore.RED + "⌨️  命令:")
    print("  • 'q' 或 'quit' - 退出")
    print("  • 'help' - 查看帮助")
    print("  • 'stats' - 查看缓存统计")
    print("  • 'clear' - 清除对话历史")
    print("-"*80)


def display_cache_stats(agent):
    """显示缓存统计"""
    stats = agent.get_stats()
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}📊 KV Cache 统计信息")
    print(f"{Fore.CYAN}{'='*70}")
    print(f"{Fore.GREEN}Agent名称: {Fore.WHITE}{stats['agent_name']}")
    print(f"{Fore.GREEN}对话轮次: {Fore.WHITE}{stats['conversation_turns']}")
    print(f"{Fore.GREEN}总消息数: {Fore.WHITE}{stats['total_messages']}")
    print(f"{Fore.GREEN}缓存tokens: {Fore.WHITE}~{stats['estimated_cached_tokens']} tokens")
    print(f"{Fore.GREEN}系统提示词: {Fore.WHITE}~{stats['system_prompt_tokens']} tokens (已缓存50% off)")

    # 估算节省
    if stats['conversation_turns'] > 0:
        saved = stats['estimated_cached_tokens'] * 0.5
        print(f"\n{Fore.YELLOW}💰 预估节省: ~{int(saved)} tokens 成本")
    print(f"{Fore.CYAN}{'='*70}\n")


class VoiceAgent:
    """语音交互Agent封装"""

    def __init__(self, enable_tts: bool = True, voice_mode: bool = True):
        """
        初始化语音Agent

        Args:
            enable_tts: 是否启用TTS
            voice_mode: 是否启用语音等待反馈
        """
        self.enable_tts = enable_tts
        self.voice_mode = voice_mode

        # 加载工具
        print(f"\n{Fore.CYAN}📦 正在加载工具...")
        self.tools = load_all_tools()
        print(f"{Fore.GREEN}✅ 已加载 {len(self.tools)} 个工具")

        # 创建Agent
        print(f"\n{Fore.CYAN}🤖 正在初始化Agent...")
        self.agent = HybridReasoningAgent(
            tools=self.tools,
            enable_cache=settings.enable_cache,
            name="VoiceAgent"
        )

        # 创建TTS
        if self.enable_tts:
            print(f"{Fore.CYAN}🎵 正在初始化TTS服务...")
            try:
                tts_engine = TTSFactory.create_tts(
                    provider=TTSProvider.EDGE,
                    voice=settings.tts_voice,
                    rate=settings.tts_rate,
                    volume=settings.tts_volume
                )

                self.tts_optimizer = TTSOptimizer(
                    tts_engine=tts_engine,
                    max_chunk_length=settings.max_chunk_length,
                    max_retries=3,
                    timeout_per_chunk=10,
                    buffer_size=3
                )
                print(f"{Fore.GREEN}✅ TTS服务初始化成功 ({settings.tts_voice})")
            except Exception as e:
                print(f"{Fore.RED}⚠️  TTS初始化失败: {e}")
                print(f"{Fore.YELLOW}💡 将以文本模式运行")
                self.enable_tts = False

        # 语音反馈
        if self.voice_mode:
            self.voice_feedback = VoiceWaitingFeedback(mode='text')

        print(f"{Fore.GREEN}✅ 初始化完成!\n")

    def run(self, user_input: str, show_reasoning: bool = True) -> dict:
        """
        执行推理并播放TTS

        Args:
            user_input: 用户输入
            show_reasoning: 是否显示推理过程

        Returns:
            执行结果字典
        """
        # 语音反馈: 开始思考
        if self.voice_mode:
            self.voice_feedback.start('thinking')

        try:
            # 执行推理
            result = self.agent.run(user_input, show_reasoning=show_reasoning)

            # 停止语音反馈
            if self.voice_mode:
                self.voice_feedback.stop()

            if not result.success:
                return {
                    'success': False,
                    'output': result.output,
                    'error': result.error
                }

            # TTS优化并播放
            if self.enable_tts:
                print(f"\n{Fore.CYAN}{'='*70}")
                print(f"{Fore.CYAN}🎵 TTS音频播放")
                print(f"{Fore.CYAN}{'='*70}\n")

                try:
                    tts_result = self.tts_optimizer.optimize_and_play(
                        text=result.output,
                        simulate_mode=False  # 真实播放
                    )

                    return {
                        'success': True,
                        'output': result.output,
                        'tool_calls': result.tool_calls,
                        'reasoning_steps': result.reasoning_steps,
                        'should_end': result.metadata.get('should_end', False),
                        'tts_success': tts_result.get('success', False),
                        'tts_chunks': tts_result.get('total_chunks', 0)
                    }
                except Exception as e:
                    print(f"{Fore.RED}⚠️  TTS播放失败: {e}")
                    print(f"{Fore.YELLOW}💬 文本输出: {result.output}")

                    return {
                        'success': True,
                        'output': result.output,
                        'tool_calls': result.tool_calls,
                        'should_end': result.metadata.get('should_end', False),
                        'tts_success': False
                    }
            else:
                # 无TTS模式
                return {
                    'success': True,
                    'output': result.output,
                    'tool_calls': result.tool_calls,
                    'should_end': result.metadata.get('should_end', False)
                }

        except Exception as e:
            if self.voice_mode:
                self.voice_feedback.stop()

            return {
                'success': False,
                'output': f"执行错误: {str(e)}",
                'error': str(e)
            }

    def get_stats(self):
        """获取统计信息"""
        return self.agent.get_stats()

    def clear_history(self):
        """清除对话历史"""
        self.agent.clear_history()


def interactive_mode(enable_tts: bool = True):
    """交互式对话模式"""
    print_header()

    # 创建Agent
    try:
        agent = VoiceAgent(enable_tts=enable_tts, voice_mode=enable_tts)
    except Exception as e:
        print(f"\n{Fore.RED}❌ Agent初始化失败: {e}")
        print(f"{Fore.YELLOW}💡 提示: 请检查 .env 文件是否正确配置")
        return

    print_examples()

    if enable_tts:
        print(f"\n{Fore.RED}🔊 请确保扬声器已开启,音量适中!")

    # 交互循环
    turn = 0
    while True:
        try:
            # 获取用户输入
            user_input = input(f"\n{Fore.CYAN}💬 您: {Style.RESET_ALL}").strip()

            # 退出命令
            if user_input.lower() in ['q', 'quit', 'exit', '退出']:
                print(f"\n{Fore.YELLOW}👋 再见!感谢使用 Robot Agent Mindflow!\n")
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
                agent.clear_history()
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
            result = agent.run(user_input, show_reasoning=True)
            response_time = time.time() - start_time

            if result['success']:
                # 显示性能统计
                print(f"\n{Fore.GREEN}⚡ 响应耗时: {Fore.WHITE}{response_time:.2f}秒")
                print(f"{Fore.GREEN}📞 工具调用: {Fore.WHITE}{result['tool_calls']}次")

                if result.get('tts_chunks', 0) > 0:
                    print(f"{Fore.GREEN}🗣️  TTS分段: {Fore.WHITE}{result['tts_chunks']}个")
                    if result.get('tts_success'):
                        print(f"{Fore.GREEN}🔊 语音播放: {Fore.WHITE}✅ 完成")
                    else:
                        print(f"{Fore.YELLOW}🔊 语音播放: {Fore.WHITE}⚠️  失败(已显示文本)")

                if turn > 1:
                    print(f"{Fore.GREEN}🚀 KV Cache: {Fore.WHITE}已优化(第{turn}轮)")

                # 检查是否需要结束
                if result.get('should_end'):
                    print(f"\n{Fore.YELLOW}🔔 检测到对话结束信号")
                    print(f"{Fore.YELLOW}👋 感谢使用!再见!\n")
                    break
            else:
                print(f"\n{Fore.RED}❌ 出错了: {result['output']}\n")

        except KeyboardInterrupt:
            print(f"\n\n{Fore.YELLOW}👋 程序被中断,再见!\n")
            break
        except Exception as e:
            print(f"\n{Fore.RED}❌ 发生错误: {str(e)}\n")
            import traceback
            traceback.print_exc()


def test_mode():
    """测试模式 - 快速测试几个示例"""
    print("\n" + "="*80)
    print(Fore.CYAN + Style.BRIGHT + "🧪 测试模式 - 快速验证")
    print("="*80)

    try:
        agent = VoiceAgent(enable_tts=True, voice_mode=False)
    except Exception as e:
        print(f"\n{Fore.RED}❌ Agent初始化失败: {e}")
        return

    test_cases = [
        ("数学计算", "计算sqrt(2)保留3位小数"),
        ("时间查询", "现在几点?"),
        ("对话结束", "好的,再见!"),
    ]

    print(f"\n{Fore.CYAN}开始测试...\n")

    for i, (name, query) in enumerate(test_cases, 1):
        print(f"{Fore.YELLOW}{'─'*70}")
        print(f"{Fore.YELLOW}测试 {i}/{len(test_cases)}: {name}")
        print(f"{Fore.YELLOW}查询: {query}")
        print(f"{Fore.YELLOW}{'─'*70}\n")

        result = agent.run(query, show_reasoning=False)

        if result['success']:
            print(f"\n{Fore.GREEN}✅ 成功")
            print(f"   输出: {result['output'][:100]}...")
            print(f"   工具调用: {result['tool_calls']}次")

            if result.get('should_end'):
                print(f"   检测到对话结束\n")
                break
        else:
            print(f"\n{Fore.RED}❌ 失败: {result['output']}\n")

        time.sleep(1)

    # 显示统计
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}📊 最终统计")
    print(f"{Fore.CYAN}{'='*70}")
    display_cache_stats(agent)

    print(f"{Fore.GREEN}✅ 测试完成!\n")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Robot Agent Mindflow - 语音交互AI Agent"
    )
    parser.add_argument(
        '--no-tts',
        action='store_true',
        help='禁用TTS语音播放'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='运行测试模式'
    )

    args = parser.parse_args()

    # 测试模式
    if args.test:
        test_mode()
        return

    # 交互模式
    interactive_mode(enable_tts=not args.no_tts)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 再见!\n")
    except Exception as e:
        print(f"\n❌ 错误: {e}\n")
        import traceback
        traceback.print_exc()
