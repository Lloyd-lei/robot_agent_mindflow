"""
TTS优化系统演示
自动运行展示所有TTS优化功能
"""
from agent_hybrid import HybridReasoningAgent
import time

# 颜色支持
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class Fore:
        CYAN = YELLOW = GREEN = MAGENTA = RED = WHITE = LIGHTBLACK_EX = ""
    class Style:
        BRIGHT = RESET_ALL = ""


def print_banner():
    """打印横幅"""
    print("\n" + "="*80)
    print(Fore.CYAN + Style.BRIGHT + "🎵 TTS优化系统完整演示")
    print("="*80)
    print(Fore.GREEN + "\n功能展示：")
    print("  ✅ 文本优化 - 清理markdown、智能分句")
    print("  ✅ TTS双轨输出 - 同时显示原始文本和TTS结构")
    print("  ✅ 音频播放管理 - 防重叠、乱序处理、失败重试")
    print("  ✅ 语音等待反馈 - 用户友好的思考提示")
    print("  ✅ JSON结果熔炼 - 将工具返回的JSON转为自然语言")
    print("="*80 + "\n")


def demo_1_basic_query():
    """演示1：基本查询 + TTS双轨输出"""
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.CYAN}演示1：基本查询 + TTS双轨输出")
    print(f"{Fore.CYAN}{'='*80}\n")
    
    # 初始化Agent（启用TTS但不启用语音反馈，避免等待）
    print(f"{Fore.GREEN}初始化Agent...")
    agent = HybridReasoningAgent(
        enable_cache=True,
        enable_tts=True,
        voice_mode=False  # 非交互式，关闭语音反馈
    )
    
    # 测试查询
    query = "计算sqrt(2)保留3位小数"
    print(f"\n{Fore.YELLOW}用户输入: {query}")
    print(f"{Fore.LIGHTBLACK_EX}(这是一个简单的数学计算，会调用calculator工具)\n")
    
    time.sleep(1)
    
    # 执行并展示双轨输出
    result = agent.run_with_tts_demo(query, show_text_and_tts=True)
    
    if result['success']:
        print(f"\n{Fore.GREEN}✅ 演示1完成")
        print(f"{Fore.GREEN}   观察：原始文本 vs TTS优化后的分段结构")
    
    return agent


def demo_2_json_result():
    """演示2：JSON结果熔炼"""
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.CYAN}演示2：JSON结果熔炼（自然语言转换）")
    print(f"{Fore.CYAN}{'='*80}\n")
    
    # 复用Agent（利用KV Cache）
    agent = HybridReasoningAgent(
        enable_cache=True,
        enable_tts=True,
        voice_mode=False
    )
    
    query = "图书馆有哪些关于Python的书"
    print(f"\n{Fore.YELLOW}用户输入: {query}")
    print(f"{Fore.LIGHTBLACK_EX}(这会调用library_system工具，返回JSON数据)\n")
    
    time.sleep(1)
    
    result = agent.run_with_tts_demo(query, show_text_and_tts=True)
    
    if result['success']:
        print(f"\n{Fore.GREEN}✅ 演示2完成")
        print(f"{Fore.GREEN}   观察：LLM已将JSON数据熔炼为自然语言，适合TTS播报")
    
    return agent


def demo_3_long_response():
    """演示3：长回答的智能分段"""
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.CYAN}演示3：长回答的智能分段")
    print(f"{Fore.CYAN}{'='*80}\n")
    
    agent = HybridReasoningAgent(
        enable_cache=True,
        enable_tts=True,
        voice_mode=False
    )
    
    query = "现在几点？"
    print(f"\n{Fore.YELLOW}用户输入: {query}")
    print(f"{Fore.LIGHTBLACK_EX}(测试时间查询工具)\n")
    
    time.sleep(1)
    
    result = agent.run_with_tts_demo(query, show_text_and_tts=True)
    
    if result['success']:
        print(f"\n{Fore.GREEN}✅ 演示3完成")
        if 'tts_chunks' in result and len(result['tts_chunks']) > 1:
            print(f"{Fore.GREEN}   观察：长回答被智能分段，每段不超过100字符")


def demo_4_audio_playback_simulation():
    """演示4：音频播放模拟（展示防重叠、乱序处理）"""
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.CYAN}演示4：音频播放模拟（防重叠、乱序处理、失败重试）")
    print(f"{Fore.CYAN}{'='*80}\n")
    
    agent = HybridReasoningAgent(
        enable_cache=True,
        enable_tts=True,
        voice_mode=False
    )
    
    query = "帮我查询技术部的联系方式"
    print(f"\n{Fore.YELLOW}用户输入: {query}")
    print(f"{Fore.LIGHTBLACK_EX}(这会测试员工通讯录工具)\n")
    
    print(f"{Fore.CYAN}开始模拟TTS音频播放...")
    print(f"{Fore.CYAN}(模拟网络延迟、乱序到达、偶尔失败等真实场景)\n")
    
    time.sleep(1)
    
    # 使用带播放的版本
    result = agent.run_with_tts(query, show_reasoning=False, simulate_mode=True)
    
    if result['success']:
        print(f"\n{Fore.GREEN}✅ 演示4完成")
        print(f"{Fore.GREEN}   观察：")
        print(f"{Fore.GREEN}   - 并发生成音频（加速）")
        print(f"{Fore.GREEN}   - 严格按顺序播放（防重叠）")
        print(f"{Fore.GREEN}   - 失败自动重试（可靠性）")
        print(f"{Fore.GREEN}   - 播放锁机制（解决GIL问题）")


def demo_5_format_cleaning():
    """演示5：格式清理（markdown、代码块等）"""
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.CYAN}演示5：格式清理（markdown、代码块、列表等）")
    print(f"{Fore.CYAN}{'='*80}\n")
    
    from tts_optimizer import TTSTextOptimizer
    
    # 创建文本优化器
    optimizer = TTSTextOptimizer(max_chunk_length=100)
    
    # 测试文本（包含markdown格式）
    test_text = """
这是一个**重要**的测试。下面是代码：

```python
def hello():
    print("world")
```

列表项：
- 第一项
- 第二项
- 第三项

链接：[点击这里](https://example.com)
    """
    
    print(f"{Fore.YELLOW}原始文本（包含markdown）:")
    print(f"{Fore.LIGHTBLACK_EX}{test_text}")
    
    # 优化
    chunks = optimizer.optimize(test_text)
    
    print(f"\n{Fore.GREEN}优化后的TTS分段:")
    for i, chunk in enumerate(chunks):
        print(f"\n{Fore.CYAN}[Chunk {i}]")
        print(f"  文本: {chunk['text']}")
        print(f"  长度: {chunk['length']} 字符")
        print(f"  停顿: {chunk['pause_after']}ms")
    
    print(f"\n{Fore.GREEN}✅ 演示5完成")
    print(f"{Fore.GREEN}   观察：所有markdown格式已清理，适合TTS播报")


def print_summary():
    """打印总结"""
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.CYAN}🎉 TTS优化系统演示完成")
    print(f"{Fore.CYAN}{'='*80}\n")
    
    print(f"{Fore.GREEN}核心特性总结：")
    print()
    print(f"{Fore.YELLOW}1. 文本优化 📝")
    print(f"   • 清理markdown/代码块/链接等格式")
    print(f"   • 智能分句（语义完整性）")
    print(f"   • 缩写展开（AI→人工智能）")
    print(f"   • 长句拆分（不超过100字符）")
    print()
    print(f"{Fore.YELLOW}2. 音频播放管理 🔊")
    print(f"   • 并发生成（提前缓冲3段）")
    print(f"   • 顺序播放（严格按chunk_id）")
    print(f"   • 播放锁（防止GIL导致的重叠）")
    print(f"   • 精确停顿（不依赖sleep精度）")
    print()
    print(f"{Fore.YELLOW}3. 可靠性保障 🛡️")
    print(f"   • 失败重试（最多3次）")
    print(f"   • 超时控制（每段10秒）")
    print(f"   • 乱序处理（有序字典+阻塞等待）")
    print(f"   • 降级策略（失败显示文本）")
    print()
    print(f"{Fore.YELLOW}4. 用户体验 ✨")
    print(f"   • 语音等待反馈（思考提示）")
    print(f"   • JSON结果熔炼（自然语言）")
    print(f"   • 双轨输出（调试友好）")
    print(f"   • KV Cache优化（速度提升）")
    print()
    print(f"{Fore.CYAN}{'='*80}\n")
    
    print(f"{Fore.GREEN}✅ TTS优化器已ready to use!")
    print(f"{Fore.GREEN}只需接入真实TTS引擎（Azure/Google/Edge TTS），即可投入生产。\n")


def main():
    """主函数 - 运行所有演示"""
    print_banner()
    
    time.sleep(2)
    
    # 运行所有演示
    demos = [
        ("基本查询", demo_1_basic_query),
        ("JSON结果熔炼", demo_2_json_result),
        ("长回答分段", demo_3_long_response),
        ("音频播放模拟", demo_4_audio_playback_simulation),
        ("格式清理", demo_5_format_cleaning),
    ]
    
    for i, (name, demo_func) in enumerate(demos, 1):
        try:
            print(f"\n{Fore.MAGENTA}▶ 正在运行演示 {i}/{len(demos)}: {name}")
            demo_func()
            time.sleep(3)  # 演示之间的间隔
        except Exception as e:
            print(f"\n{Fore.RED}❌ 演示 {i} 出错: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # 打印总结
    print_summary()


if __name__ == "__main__":
    main()

