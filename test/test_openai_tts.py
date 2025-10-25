#!/usr/bin/env python3
"""
测试 OpenAI TTS 功能
"""
import asyncio
from colorama import Fore, Style, init
from tts_interface import TTSFactory, TTSProvider
import config

init(autoreset=True)

async def test_openai_tts():
    """测试 OpenAI TTS"""
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}🧪 测试 OpenAI TTS")
    print(f"{Fore.CYAN}{'='*70}\n")
    
    # 检查 API Key
    if not config.OPENAI_API_KEY or config.OPENAI_API_KEY == "":
        print(f"{Fore.RED}❌ 错误：未设置 OPENAI_API_KEY！")
        print(f"{Fore.YELLOW}请在 .env 文件中设置：")
        print(f"{Fore.WHITE}OPENAI_API_KEY=sk-your-key-here")
        return False
    
    print(f"{Fore.GREEN}✅ OpenAI API Key 已配置")
    print(f"{Fore.YELLOW}API Key: {config.OPENAI_API_KEY[:20]}...{config.OPENAI_API_KEY[-4:]}")
    
    # 测试所有 6 种语音
    voices = {
        "alloy": "中性、清晰",
        "echo": "男声、专业",
        "fable": "英式、优雅",
        "onyx": "深沉男声",
        "nova": "女声、活泼 ⭐",
        "shimmer": "女声、温柔 ⭐"
    }
    
    test_text = "你好，我是茶茶，一个AI语音助手。"
    
    print(f"\n{Fore.CYAN}🎤 可用语音：")
    for voice, desc in voices.items():
        print(f"  • {voice}: {desc}")
    
    print(f"\n{Fore.YELLOW}测试文本: {test_text}")
    print(f"{Fore.CYAN}\n开始测试...\n")
    
    success_count = 0
    for voice, desc in voices.items():
        try:
            print(f"{Fore.MAGENTA}[{voice}] {desc}")
            
            # 创建 TTS 实例
            tts = TTSFactory.create_tts(
                provider=TTSProvider.OPENAI,
                api_key=config.OPENAI_API_KEY,
                model="tts-1",  # 使用标准模型（更便宜）
                voice=voice
            )
            
            # 合成语音
            audio_data = await tts.synthesize(test_text)
            
            if audio_data and len(audio_data) > 0:
                print(f"{Fore.GREEN}✅ 合成成功！音频大小: {len(audio_data)} 字节")
                success_count += 1
                
                # 保存示例音频
                output_file = f"test/outputs/openai_tts_{voice}_sample.mp3"
                import os
                os.makedirs("test/outputs", exist_ok=True)
                with open(output_file, "wb") as f:
                    f.write(audio_data)
                print(f"{Fore.CYAN}💾 已保存到: {output_file}")
            else:
                print(f"{Fore.RED}❌ 音频数据为空")
                
        except Exception as e:
            print(f"{Fore.RED}❌ 失败: {str(e)}")
        
        print()
    
    print(f"{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}📊 测试总结")
    print(f"{Fore.CYAN}{'='*70}")
    print(f"成功: {Fore.GREEN}{success_count}{Fore.WHITE}/{len(voices)}")
    
    if success_count == len(voices):
        print(f"\n{Fore.GREEN}🎉 所有语音测试通过！")
        print(f"\n{Fore.CYAN}💡 推荐使用：")
        print(f"{Fore.WHITE}  • nova（女声，活泼友好）- 适合日常对话")
        print(f"{Fore.WHITE}  • shimmer（女声，温柔）- 适合语音助手")
        print(f"{Fore.WHITE}  • alloy（中性）- 适合通用场景")
        return True
    else:
        print(f"\n{Fore.RED}❌ 部分测试失败，请检查错误信息")
        return False

if __name__ == "__main__":
    print(f"\n{Fore.MAGENTA}{'#'*80}")
    print(f"{Fore.MAGENTA}# OpenAI TTS 功能测试 #")
    print(f"{Fore.MAGENTA}{'#'*80}\n")
    
    result = asyncio.run(test_openai_tts())
    
    if result:
        print(f"\n{Fore.GREEN}✅ 测试完成！可以使用 OpenAI TTS 了。")
        print(f"\n{Fore.CYAN}🚀 启动程序：")
        print(f"{Fore.WHITE}python main.py")
        print(f"\n{Fore.YELLOW}💡 提示：音频文件已保存在 test/outputs/ 目录，可以播放试听。")
    else:
        print(f"\n{Fore.RED}❌ 测试失败！请检查配置。")
    
    print()

