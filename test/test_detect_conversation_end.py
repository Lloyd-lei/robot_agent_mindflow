#!/usr/bin/env python3
"""
测试 detectConversationEnd 工具修复

验证：
1. 工具名不含下划线，不会被 Markdown 清理破坏
2. 工具能正常被调用
3. 工具返回值不会被误过滤
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from colorama import Fore, Style, init
init(autoreset=True)

def test_tool_name_no_conflict():
    """测试工具名不会与过滤逻辑冲突"""
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}🧪 测试 1: 工具名与过滤逻辑不冲突")
    print(f"{Fore.CYAN}{'='*70}\n")
    
    tool_name = "detectConversationEnd"
    
    # 模拟 Markdown 清理
    cleaned_name = tool_name.replace('**', '').replace('__', '')
    cleaned_name = cleaned_name.replace('*', '').replace('_', '')
    cleaned_name = cleaned_name.replace('```', '')
    cleaned_name = cleaned_name.replace('`', '')
    cleaned_name = cleaned_name.replace('#', '')
    
    print(f"原始工具名: {tool_name}")
    print(f"Markdown 清理后: {cleaned_name}")
    
    # 检查是否会被特殊标记过滤匹配
    should_filter = any([
        "(END_CONVERSATION)" in cleaned_name.upper(),
        "(ENDCONVERSATION)" in cleaned_name.upper(),
        "END_CONVERSATION" in cleaned_name.upper(),
        "ENDCONVERSATION" in cleaned_name.upper(),
    ])
    
    if should_filter:
        print(f"{Fore.RED}❌ 失败：工具名会被误过滤！")
        return False
    else:
        print(f"{Fore.GREEN}✅ 成功：工具名不会被过滤")
        return True


def test_tool_loading():
    """测试工具是否能正常加载"""
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}🧪 测试 2: 工具能正常加载")
    print(f"{Fore.CYAN}{'='*70}\n")
    
    try:
        from tools import ConversationEndDetector
        tool = ConversationEndDetector()
        
        print(f"工具类: {tool.__class__.__name__}")
        print(f"工具名: {tool.name}")
        print(f"工具描述: {tool.description[:50]}...")
        
        if tool.name == "detectConversationEnd":
            print(f"{Fore.GREEN}✅ 成功：工具名正确")
            return True
        else:
            print(f"{Fore.RED}❌ 失败：工具名不正确（期望: detectConversationEnd，实际: {tool.name}）")
            return False
            
    except Exception as e:
        print(f"{Fore.RED}❌ 失败：无法加载工具 - {e}")
        return False


def test_tool_execution():
    """测试工具能正常执行"""
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}🧪 测试 3: 工具能正常执行")
    print(f"{Fore.CYAN}{'='*70}\n")
    
    try:
        from tools import ConversationEndDetector
        tool = ConversationEndDetector()
        
        # 测试结束关键词
        test_cases = [
            ("再见", True, "应检测到结束意图"),
            ("你好", False, "不应检测到结束意图"),
            ("谢谢，拜拜", True, "应检测到结束意图"),
        ]
        
        all_passed = True
        for message, should_detect_end, description in test_cases:
            result = tool._run(user_message=message)
            detected = "END_CONVERSATION" in result
            
            if detected == should_detect_end:
                print(f"{Fore.GREEN}✅ '{message}': {description} - 正确")
            else:
                print(f"{Fore.RED}❌ '{message}': {description} - 错误")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"{Fore.RED}❌ 失败：工具执行出错 - {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print(f"\n{Fore.MAGENTA}{'#'*80}")
    print(f"{Fore.MAGENTA}# detectConversationEnd 工具修复验证 #")
    print(f"{Fore.MAGENTA}{'#'*80}\n")
    
    test1 = test_tool_name_no_conflict()
    test2 = test_tool_loading()
    test3 = test_tool_execution()
    
    print(f"\n{Fore.MAGENTA}{'#'*80}")
    if test1 and test2 and test3:
        print(f"{Fore.GREEN}# ✅ 所有测试通过！工具修复成功！ #")
    else:
        print(f"{Fore.RED}# ❌ 部分测试失败，请检查修复 #")
    print(f"{Fore.MAGENTA}{'#'*80}\n")

