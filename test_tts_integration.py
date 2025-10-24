"""
测试 TTS 集成
验证 Edge TTS + pygame 播放功能
"""
import asyncio
from tts_interface import TTSFactory, TTSProvider

def test_edge_tts():
    """测试 Edge TTS 合成和播放"""
    print("\n" + "="*70)
    print("🧪 测试 Edge TTS 集成")
    print("="*70)
    
    async def run_test():
        # 1. 创建 Edge TTS 实例
        print("\n1️⃣  创建 Edge TTS 实例...")
        tts = TTSFactory.create_tts(
            provider=TTSProvider.EDGE,
            voice="zh-CN-XiaoxiaoNeural",  # 晓晓
            rate="+0%"
        )
        print(f"   ✅ 成功！当前语音: {tts.voice}")
        
        # 2. 合成短文本
        print("\n2️⃣  合成测试文本...")
        test_text = "你好，这是 Edge TTS 集成测试。"
        print(f"   文本: {test_text}")
        
        audio_data = await tts.synthesize(test_text)
        print(f"   ✅ 合成成功！音频大小: {len(audio_data):,} 字节")
        
        # 3. 保存音频文件
        print("\n3️⃣  保存音频文件...")
        output_file = "test_output.mp3"
        with open(output_file, "wb") as f:
            f.write(audio_data)
        print(f"   ✅ 已保存到: {output_file}")
        
        # 4. 使用 pygame 播放
        print("\n4️⃣  使用 pygame 播放音频...")
        try:
            import pygame
            import io
            
            # 初始化 pygame
            pygame.mixer.init()
            
            # 加载音频
            audio_io = io.BytesIO(audio_data)
            pygame.mixer.music.load(audio_io)
            
            # 播放
            pygame.mixer.music.play()
            print(f"   🔊 正在播放...")
            
            # 等待播放完成
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            
            print(f"   ✅ 播放完成！")
            
        except ImportError:
            print(f"   ⚠️  pygame 未安装，跳过播放测试")
        except Exception as e:
            print(f"   ❌ 播放失败: {e}")
        
        # 5. 测试可用语音列表
        print("\n5️⃣  可用的中文语音:")
        voices = tts.get_available_voices()
        for i, voice in enumerate(voices[:6], 1):
            print(f"   {i}. {voice}")
        
        print("\n" + "="*70)
        print("✅ 测试完成！")
        print("="*70 + "\n")
    
    # 运行异步测试
    asyncio.run(run_test())


def test_with_agent():
    """测试 Agent 集成 TTS"""
    print("\n" + "="*70)
    print("🤖 测试 Agent + TTS 集成")
    print("="*70)
    
    from agent_hybrid import HybridReasoningAgent
    
    # 创建启用 TTS 的 Agent
    print("\n⏳ 初始化 Agent（启用 TTS）...")
    agent = HybridReasoningAgent(
        enable_cache=True,
        enable_tts=True,
        voice_mode=True
    )
    
    print("\n✅ Agent 初始化成功！")
    print(f"   TTS 优化器: {'已启用' if agent.enable_tts else '未启用'}")
    print(f"   语音模式: {'已启用' if agent.voice_mode else '未启用'}")
    
    # 测试简单对话
    print("\n📝 测试对话: '现在几点了？'")
    result = agent.run_with_tts_demo(
        "现在几点了？",
        show_text_and_tts=True
    )
    
    if result['success']:
        print(f"\n✅ 对话测试成功！")
        print(f"   工具调用: {result['tool_calls']}次")
        print(f"   TTS分段: {result.get('total_tts_chunks', 0)}个")
    else:
        print(f"\n❌ 对话测试失败: {result['output']}")
    
    print("\n" + "="*70)
    print("✅ Agent 测试完成！")
    print("="*70 + "\n")


if __name__ == "__main__":
    print("\n🚀 开始 TTS 集成测试...\n")
    
    # 测试 1: Edge TTS 基础功能
    try:
        test_edge_tts()
    except Exception as e:
        print(f"\n❌ Edge TTS 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试 2: Agent 集成
    try:
        test_with_agent()
    except Exception as e:
        print(f"\n❌ Agent 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🎉 所有测试完成！\n")

