"""
多语言语音切换功能测试
测试 AI Agent 是否能自动检测语言并切换 TTS 语音
"""
import sys
import os
from colorama import Fore, Style, init

# 确保可以导入项目模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from conversation_session import ConversationSession
from logger_config import setup_logger

init(autoreset=True)
logger = setup_logger(name="test_multilingual", level="INFO")


def test_language_detection_and_switch():
    """测试语言检测和语音切换"""
    
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}🌍 多语言语音切换功能测试")
    print(f"{Fore.CYAN}{'='*70}\n")
    
    test_cases = [
        ("中文", "你好，现在几点了？", "zh-CN-XiaoxiaoNeural"),
        ("英文", "Hello, what time is it now?", "en-US-JennyNeural"),
        ("日文", "こんにちは、今何時ですか？", "ja-JP-NanamiNeural"),
        ("西班牙语", "Hola, ¿qué hora es?", "es-ES-ElviraNeural"),
        ("法语", "Bonjour, quelle heure est-il?", "fr-FR-DeniseNeural"),
        ("越南语", "Xin chào, bây giờ là mấy giờ?", "vi-VN-HoaiMyNeural"),
        ("切换回中文", "谢谢，再见", "zh-CN-XiaoxiaoNeural"),
    ]
    
    try:
        print(f"{Fore.YELLOW}⏳ 正在初始化会话...\n")
        
        with ConversationSession(
            tts_provider="edge",
            tts_voice="zh-CN-XiaoxiaoNeural",
            enable_cache=True,
            show_reasoning=False,  # 简化输出
            timeout=30,
            tts_wait_timeout=20
        ) as session:
            
            print(f"{Fore.GREEN}✅ 会话初始化完成\n")
            print(f"{Fore.CYAN}{'='*70}\n")
            
            for i, (language, user_input, expected_voice) in enumerate(test_cases, 1):
                print(f"{Fore.MAGENTA}【测试 {i}/{len(test_cases)}】{language} 测试")
                print(f"{Fore.CYAN}用户输入: {Fore.WHITE}{user_input}")
                
                # 执行对话
                result = session.chat(user_input)
                
                # 检查当前语音
                current_voice = session._agent.tts_engine.voice
                
                # 验证语音是否切换成功
                if current_voice == expected_voice:
                    print(f"{Fore.GREEN}✅ 语音切换成功: {current_voice}")
                else:
                    print(f"{Fore.RED}❌ 语音切换失败:")
                    print(f"   期望: {expected_voice}")
                    print(f"   实际: {current_voice}")
                
                print(f"{Fore.CYAN}Agent回复: {Fore.WHITE}{result.response[:100]}...")
                print(f"{Fore.GREEN}工具调用: {result.tool_calls}次")
                print(f"{Fore.GREEN}耗时: {result.duration:.2f}秒")
                print(f"{Fore.CYAN}{'='*70}\n")
            
            print(f"\n{Fore.GREEN}🎉 所有测试完成！")
            
    except Exception as e:
        print(f"\n{Fore.RED}❌ 测试失败: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def test_manual_voice_check():
    """手动验证语音切换（让用户听 TTS 播放）"""
    
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}🎧 手动语音验证测试（需要听音频）")
    print(f"{Fore.CYAN}{'='*70}\n")
    
    print(f"{Fore.YELLOW}请在听到 TTS 播放时验证语音是否正确切换\n")
    
    test_phrases = [
        ("中文", "你好，我叫茶茶"),
        ("英文", "Hello, my name is ChaCha"),
        ("日文", "こんにちは、私の名前はチャチャです"),
    ]
    
    try:
        print(f"{Fore.YELLOW}⏳ 正在初始化会话...\n")
        
        with ConversationSession(
            tts_provider="edge",
            tts_voice="zh-CN-XiaoxiaoNeural",
            enable_cache=True,
            show_reasoning=True,  # 显示完整推理
            timeout=30,
            tts_wait_timeout=20
        ) as session:
            
            print(f"{Fore.GREEN}✅ 会话初始化完成\n")
            
            for language, phrase in test_phrases:
                print(f"\n{Fore.MAGENTA}【{language}语音测试】")
                print(f"{Fore.YELLOW}请仔细听 TTS 播放的语音...\n")
                
                result = session.chat(phrase)
                
                current_voice = session._agent.tts_engine.voice
                print(f"\n{Fore.CYAN}当前语音: {current_voice}")
                
                # 等待用户确认
                confirmation = input(f"\n{Fore.YELLOW}语音是否正确？(y/n): {Style.RESET_ALL}").strip().lower()
                if confirmation == 'y':
                    print(f"{Fore.GREEN}✅ 用户确认语音正确\n")
                else:
                    print(f"{Fore.RED}❌ 用户认为语音不正确\n")
            
            print(f"\n{Fore.GREEN}🎉 手动验证完成！")
            
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️  用户中断测试")
    except Exception as e:
        print(f"\n{Fore.RED}❌ 测试失败: {str(e)}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print(f"\n{Fore.MAGENTA}{'#'*80}")
    print(f"{Fore.MAGENTA}# 多语言语音切换功能测试 #")
    print(f"{Fore.MAGENTA}{'#'*80}\n")
    
    # 测试1：自动语言检测和切换
    print(f"{Fore.CYAN}【测试1】自动语言检测和语音切换\n")
    auto_test_passed = test_language_detection_and_switch()
    
    if auto_test_passed:
        # 测试2：手动验证（可选）
        print(f"\n{Fore.CYAN}是否进行手动语音验证测试？(y/n): {Style.RESET_ALL}", end='')
        try:
            choice = input().strip().lower()
            if choice == 'y':
                test_manual_voice_check()
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}⚠️  跳过手动测试")
    
    print(f"\n{Fore.MAGENTA}{'#'*80}")
    print(f"{Fore.MAGENTA}# 测试完成 #")
    print(f"{Fore.MAGENTA}{'#'*80}\n")
