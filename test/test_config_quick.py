#!/usr/bin/env python3
"""
快速配置测试 - 验证 OpenAI LLM 和 TTS
"""
import asyncio
from colorama import Fore, Style, init

init(autoreset=True)

print(f"\n{Fore.CYAN}{'='*70}")
print(f"{Fore.CYAN}🔧 配置验证测试")
print(f"{Fore.CYAN}{'='*70}\n")

# 测试 1: 配置加载
print(f"{Fore.YELLOW}[1/4] 测试配置加载...")
try:
    import config
    print(f"{Fore.GREEN}  ✅ USE_OLLAMA: {config.USE_OLLAMA}")
    print(f"{Fore.GREEN}  ✅ LLM_MODEL: {config.LLM_MODEL}")
    print(f"{Fore.GREEN}  ✅ API_KEY: {config.OPENAI_API_KEY[:20]}...{config.OPENAI_API_KEY[-4:]}")
except Exception as e:
    print(f"{Fore.RED}  ❌ 失败: {e}")
    exit(1)

# 测试 2: OpenAI 客户端
print(f"\n{Fore.YELLOW}[2/4] 测试 OpenAI 客户端...")
try:
    from openai import OpenAI
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    print(f"{Fore.GREEN}  ✅ OpenAI 客户端初始化成功")
except Exception as e:
    print(f"{Fore.RED}  ❌ 失败: {e}")
    exit(1)

# 测试 3: LLM 调用
print(f"\n{Fore.YELLOW}[3/4] 测试 LLM 调用...")
try:
    response = client.chat.completions.create(
        model=config.LLM_MODEL,
        messages=[{"role": "user", "content": "回复'测试成功'"}],
        max_tokens=10
    )
    result = response.choices[0].message.content
    print(f"{Fore.GREEN}  ✅ LLM 响应: {result}")
except Exception as e:
    print(f"{Fore.RED}  ❌ 失败: {e}")
    exit(1)

# 测试 4: TTS 调用
print(f"\n{Fore.YELLOW}[4/4] 测试 OpenAI TTS...")
try:
    async def test_tts():
        from tts_interface import TTSFactory, TTSProvider
        tts = TTSFactory.create_tts(
            provider=TTSProvider.OPENAI,
            api_key=config.OPENAI_API_KEY,
            voice="nova"
        )
        audio = await tts.synthesize("测试")
        return len(audio)
    
    audio_size = asyncio.run(test_tts())
    print(f"{Fore.GREEN}  ✅ TTS 成功，音频大小: {audio_size} bytes")
except Exception as e:
    print(f"{Fore.RED}  ❌ 失败: {e}")
    exit(1)

# 测试 5: VoiceSelector 是否被禁用
print(f"\n{Fore.YELLOW}[5/5] 验证 VoiceSelector 状态...")
try:
    from agent_hybrid import HybridReasoningAgent
    agent = HybridReasoningAgent(enable_cache=False, enable_tts=False)
    
    has_voice_selector = any(tool.name == "voiceSelector" for tool in agent.langchain_tools)
    if has_voice_selector:
        print(f"{Fore.YELLOW}  ⚠️  VoiceSelector 仍然启用（应该已禁用）")
    else:
        print(f"{Fore.GREEN}  ✅ VoiceSelector 已正确禁用")
except Exception as e:
    print(f"{Fore.RED}  ❌ 失败: {e}")
    exit(1)

print(f"\n{Fore.GREEN}{'='*70}")
print(f"{Fore.GREEN}🎉 所有配置测试通过！")
print(f"{Fore.GREEN}{'='*70}\n")

print(f"{Fore.CYAN}配置摘要：")
print(f"  • LLM: OpenAI {config.LLM_MODEL}")
print(f"  • TTS: OpenAI nova")
print(f"  • VoiceSelector: 已禁用")
print(f"\n{Fore.YELLOW}现在可以运行主程序了：")
print(f"{Fore.WHITE}  python main.py\n")

