#!/usr/bin/env python3
"""
测试外部 Prompt 文件加载功能
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from colorama import Fore, Style, init

init(autoreset=True)

def test_prompt_loading():
    """测试 prompt 文件加载"""
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}🧪 测试 System Prompt 外部文件加载")
    print(f"{Fore.CYAN}{'='*70}\n")
    
    # 正确的路径：从项目根目录访问 prompts/
    prompt_path = Path(__file__).parent.parent / "prompts" / "system_prompt.txt"
    
    # 检查文件是否存在
    if not prompt_path.exists():
        print(f"{Fore.RED}❌ 错误：Prompt 文件不存在！")
        print(f"{Fore.YELLOW}预期路径: {prompt_path}")
        return False
    
    print(f"{Fore.GREEN}✅ Prompt 文件存在: {prompt_path}")
    
    # 测试读取文件
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt = f.read().strip()
        
        if not prompt:
            print(f"{Fore.RED}❌ 错误：Prompt 文件为空！")
            return False
        
        print(f"{Fore.GREEN}✅ Prompt 文件读取成功")
        print(f"{Fore.YELLOW}文件大小: {len(prompt)} 字符")
        
        # 显示前 200 个字符作为预览
        preview = prompt[:200].replace('\n', ' ')
        print(f"\n{Fore.CYAN}📄 Prompt 预览:")
        print(f"{Fore.WHITE}{preview}...")
        
        # 检查关键内容
        key_phrases = [
            "茶茶",
            "语音交互规范",
            "多语言语音自动切换",
            "voiceSelector",
            "detectConversationEnd"
        ]
        
        print(f"\n{Fore.CYAN}🔍 检查关键内容:")
        all_found = True
        for phrase in key_phrases:
            if phrase in prompt:
                print(f"{Fore.GREEN}  ✅ 包含: {phrase}")
            else:
                print(f"{Fore.RED}  ❌ 缺失: {phrase}")
                all_found = False
        
        if all_found:
            print(f"\n{Fore.GREEN}🎉 所有检查通过！Prompt 文件完整且有效。")
            print(f"{Fore.YELLOW}💡 现在你可以直接编辑 prompts/system_prompt.txt 来修改 prompt")
            print(f"{Fore.YELLOW}💡 修改后重新运行 python main.py 即可生效（无需重启代码）")
            return True
        else:
            print(f"\n{Fore.RED}⚠️  Prompt 文件可能不完整，请检查内容")
            return False
            
    except Exception as e:
        print(f"{Fore.RED}❌ 读取 Prompt 文件失败: {e}")
        return False

def test_agent_loading():
    """测试 Agent 是否能正确加载 prompt"""
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}🧪 测试 Agent 加载 Prompt")
    print(f"{Fore.CYAN}{'='*70}\n")
    
    try:
        from agent_hybrid import HybridReasoningAgent
        
        print(f"{Fore.YELLOW}⏳ 正在初始化 Agent...")
        agent = HybridReasoningAgent(
            enable_cache=False,
            enable_tts=False,
            voice_mode=False
        )
        
        if agent.system_prompt:
            print(f"{Fore.GREEN}✅ Agent 成功加载 System Prompt")
            print(f"{Fore.YELLOW}Prompt 长度: {len(agent.system_prompt)} 字符")
            
            # 检查是否是从文件加载的
            if "茶茶" in agent.system_prompt:
                print(f"{Fore.GREEN}✅ Prompt 内容验证通过（包含'茶茶'）")
                return True
            else:
                print(f"{Fore.RED}❌ Prompt 内容异常")
                return False
        else:
            print(f"{Fore.RED}❌ Agent 的 system_prompt 为空")
            return False
            
    except Exception as e:
        print(f"{Fore.RED}❌ Agent 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print(f"\n{Fore.MAGENTA}{'#'*80}")
    print(f"{Fore.MAGENTA}# System Prompt 外部文件加载测试 #")
    print(f"{Fore.MAGENTA}{'#'*80}\n")
    
    # 测试 1：文件读取
    test1_passed = test_prompt_loading()
    
    # 测试 2：Agent 加载
    test2_passed = test_agent_loading()
    
    # 总结
    print(f"\n{Fore.MAGENTA}{'='*70}")
    print(f"{Fore.MAGENTA}📊 测试总结")
    print(f"{Fore.MAGENTA}{'='*70}")
    
    results = [
        ("Prompt 文件读取", test1_passed),
        ("Agent 加载 Prompt", test2_passed)
    ]
    
    for test_name, passed in results:
        status = f"{Fore.GREEN}✅ 通过" if passed else f"{Fore.RED}❌ 失败"
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print(f"\n{Fore.GREEN}🎉 全部测试通过！")
        print(f"\n{Fore.CYAN}📝 快速开始:")
        print(f"{Fore.WHITE}  1. 编辑 prompt: vim prompts/system_prompt.txt")
        print(f"{Fore.WHITE}  2. 查看说明: cat prompts/README.md")
        print(f"{Fore.WHITE}  3. 运行程序: python main.py")
    else:
        print(f"\n{Fore.RED}❌ 部分测试失败，请检查上述错误信息")
    
    print()

