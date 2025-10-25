"""
测试语音模式和工具调用音效
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from conversation_session import ConversationSession
from colorama import Fore, Style, init
import config

init(autoreset=True)


def test_voice_mode_parameter():
    """测试 voice_mode 参数传递"""
    print(f"{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}测试 1: voice_mode 参数传递")
    print(f"{Fore.CYAN}{'='*70}\n")
    
    # 创建会话（启用 voice_mode）
    session = ConversationSession(
        llm_model=config.LLM_MODEL,
        tts_provider="openai",
        tts_voice="shimmer",
        enable_cache=True,
        show_reasoning=True,
        timeout=60,
        tts_wait_timeout=60,
        voice_mode=True,  # ✅ 启用语音模式
        temperature=0.0
    )
    
    session.start()
    
    # 检查参数是否正确传递
    assert session.voice_mode == True, "❌ voice_mode 未正确传递"
    assert session._agent.voice_mode == True, "❌ voice_mode 未传递给 agent"
    assert hasattr(session._agent, 'voice_feedback'), "❌ voice_feedback 未初始化"
    assert session._agent.voice_feedback.mode == 'audio', "❌ voice_feedback 模式不是 audio"
    assert session.temperature == 0.0, "❌ temperature 未正确传递"
    assert session._agent.temperature == 0.0, "❌ temperature 未传递给 agent"
    
    print(f"{Fore.GREEN}✅ voice_mode 参数传递测试通过")
    print(f"   - session.voice_mode: {session.voice_mode}")
    print(f"   - agent.voice_mode: {session._agent.voice_mode}")
    print(f"   - voice_feedback.mode: {session._agent.voice_feedback.mode}")
    print(f"   - session.temperature: {session.temperature}")
    print(f"   - agent.temperature: {session._agent.temperature}\n")
    
    session.end()


def test_tool_call_with_sound():
    """测试工具调用音效（需要手动验证音效播放）"""
    print(f"{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}测试 2: 工具调用音效播放")
    print(f"{Fore.CYAN}{'='*70}\n")
    
    print(f"{Fore.YELLOW}💡 这个测试需要你手动验证：")
    print(f"   1. 听到键盘敲击音效（工具调用时）")
    print(f"   2. LLM 调用 calculator 工具")
    print(f"   3. 音效在工具调用前开始，工具返回后停止\n")
    
    # 创建会话
    session = ConversationSession(
        llm_model=config.LLM_MODEL,
        tts_provider="openai",
        tts_voice="shimmer",
        enable_cache=True,
        show_reasoning=True,
        timeout=60,
        tts_wait_timeout=60,
        voice_mode=True  # ✅ 启用语音模式
    )
    
    session.start()
    
    # 测试工具调用（会触发音效）
    print(f"{Fore.CYAN}发送测试问题：'计算根号2保留3位小数'\n")
    print(f"{Fore.YELLOW}🎵 请注意听音效...\n")
    
    result = session.chat("计算根号2保留3位小数")
    
    print(f"\n{Fore.GREEN}✅ 工具调用音效测试完成")
    print(f"   - 使用了 {result.tool_calls} 个工具")
    print(f"   - 回复: {result.response}")
    print(f"{Fore.YELLOW}💡 请确认你听到了键盘敲击音效！\n")
    
    session.end()


def test_without_voice_mode():
    """测试不启用 voice_mode（不应播放音效）"""
    print(f"{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}测试 3: 不启用 voice_mode（对照组）")
    print(f"{Fore.CYAN}{'='*70}\n")
    
    # 创建会话（不启用 voice_mode）
    session = ConversationSession(
        llm_model=config.LLM_MODEL,
        tts_provider="openai",
        tts_voice="shimmer",
        enable_cache=True,
        show_reasoning=True,
        timeout=60,
        tts_wait_timeout=60,
        voice_mode=False  # ❌ 不启用语音模式
    )
    
    session.start()
    
    # 检查参数
    assert session.voice_mode == False, "❌ voice_mode 应为 False"
    assert session._agent.voice_mode == False, "❌ agent.voice_mode 应为 False"
    assert not hasattr(session._agent, 'voice_feedback'), "❌ voice_feedback 不应初始化"
    
    print(f"{Fore.GREEN}✅ 不启用 voice_mode 测试通过")
    print(f"   - session.voice_mode: {session.voice_mode}")
    print(f"   - agent.voice_mode: {session._agent.voice_mode}")
    print(f"   - has voice_feedback: {hasattr(session._agent, 'voice_feedback')}\n")
    
    # 测试工具调用（不应播放音效）
    print(f"{Fore.CYAN}发送测试问题：'现在几点了'\n")
    print(f"{Fore.YELLOW}🔇 不应听到音效...\n")
    
    result = session.chat("现在几点了")
    
    print(f"\n{Fore.GREEN}✅ 无音效测试完成")
    print(f"   - 使用了 {result.tool_calls} 个工具")
    print(f"   - 回复: {result.response}")
    print(f"{Fore.YELLOW}💡 请确认你没有听到音效！\n")
    
    session.end()


if __name__ == "__main__":
    print(f"\n{Fore.MAGENTA}{'='*70}")
    print(f"{Fore.MAGENTA}🎵 语音模式和工具调用音效测试")
    print(f"{Fore.MAGENTA}{'='*70}\n")
    
    try:
        test_voice_mode_parameter()
        test_tool_call_with_sound()
        test_without_voice_mode()
        
        print(f"\n{Fore.GREEN}{'='*70}")
        print(f"{Fore.GREEN}✅ 所有测试通过！")
        print(f"{Fore.GREEN}{'='*70}\n")
    
    except Exception as e:
        print(f"\n{Fore.RED}❌ 测试失败: {e}\n")
        import traceback
        traceback.print_exc()

