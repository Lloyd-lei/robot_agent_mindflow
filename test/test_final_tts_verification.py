#!/usr/bin/env python3
"""
最终TTS验证脚本 - 确认OpenAI TTS已正确集成
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from conversation_session import ConversationSession
from colorama import Fore, Style, init

init(autoreset=True)

print("=" * 80)
print(Fore.CYAN + Style.BRIGHT + "🔍 OpenAI TTS 最终验证")
print("=" * 80)

# 创建会话（和main.py完全相同的配置）
print(f"\n{Fore.YELLOW}⏳ 正在启动会话...")
session = ConversationSession(
    tts_provider="openai",
    tts_voice="nova",
    enable_cache=False,
    show_reasoning=False,
    timeout=60,
    tts_wait_timeout=60
)

session.start()

print(f"\n{Fore.GREEN}{'='*80}")
print(f"{Fore.GREEN}📊 TTS 配置验证报告")
print(f"{Fore.GREEN}{'='*80}")

# 1. Agent的TTS引擎
agent_tts = session._agent.tts_engine
print(f"\n{Fore.CYAN}1️⃣  Agent TTS 引擎:")
print(f"   类型: {Fore.WHITE}{type(agent_tts).__name__}")
print(f"   语音: {Fore.WHITE}{agent_tts.voice}")
if hasattr(agent_tts, 'model'):
    print(f"   模型: {Fore.WHITE}{agent_tts.model}")
    print(f"   API Key: {Fore.WHITE}{agent_tts.api_key[:25]}...")

# 2. StreamingTTSPipeline的TTS引擎
pipeline_tts = session._agent.streaming_pipeline.tts_engine
print(f"\n{Fore.CYAN}2️⃣  StreamingTTSPipeline TTS 引擎:")
print(f"   类型: {Fore.WHITE}{type(pipeline_tts).__name__}")
print(f"   语音: {Fore.WHITE}{pipeline_tts.voice}")
if hasattr(pipeline_tts, 'model'):
    print(f"   模型: {Fore.WHITE}{pipeline_tts.model}")
    print(f"   API Key: {Fore.WHITE}{pipeline_tts.api_key[:25]}...")

# 3. 检查引用是否一致
print(f"\n{Fore.CYAN}3️⃣  引用一致性检查:")
if agent_tts is pipeline_tts:
    print(f"   {Fore.GREEN}✅ Agent 和 Pipeline 使用的是同一个 TTS 实例")
else:
    print(f"   {Fore.RED}❌ 警告：Agent 和 Pipeline 使用的是不同的 TTS 实例！")

# 4. 最终结论
print(f"\n{Fore.GREEN}{'='*80}")
if (type(agent_tts).__name__ == 'OpenAITTS' and 
    type(pipeline_tts).__name__ == 'OpenAITTS' and
    agent_tts.voice == 'nova' and
    pipeline_tts.voice == 'nova'):
    print(f"{Fore.GREEN}✅✅✅ 验证通过！")
    print(f"{Fore.GREEN}   系统正在使用 OpenAI TTS - Nova 语音")
    print(f"{Fore.GREEN}   LLM: gpt-4o-mini | TTS: OpenAI Nova")
else:
    print(f"{Fore.RED}❌❌❌ 验证失败！")
    print(f"{Fore.RED}   请检查配置")

print(f"{Fore.GREEN}{'='*80}\n")

session.end()

print(f"{Fore.CYAN}💡 提示：现在可以运行 {Fore.WHITE}python main.py{Fore.CYAN} 开始对话！\n")

