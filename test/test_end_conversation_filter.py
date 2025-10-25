#!/usr/bin/env python3
"""
测试 (END_CONVERSATION) 过滤逻辑

验证修复：
1. Markdown 清理不会破坏特殊标记检测
2. 多种变体都能被正确过滤
3. 流式输入不会导致标记泄露
"""

import re
from colorama import Fore, Style, init

init(autoreset=True)

def test_filter_logic(content_piece: str) -> bool:
    """
    测试过滤逻辑（与 agent_hybrid.py 中的逻辑一致）
    
    Returns:
        True: 应该被过滤（不送入 TTS）
        False: 可以送入 TTS
    """
    # 第一步：清理 Markdown 符号
    cleaned_piece = content_piece.replace('**', '').replace('__', '')
    cleaned_piece = cleaned_piece.replace('*', '').replace('_', '')
    cleaned_piece = cleaned_piece.replace('```', '')
    cleaned_piece = cleaned_piece.replace('`', '')
    cleaned_piece = cleaned_piece.replace('#', '')
    
    # 第二步：检查特殊标记（多种变体）
    should_filter = any([
        "(END_CONVERSATION)" in cleaned_piece.upper(),
        "(ENDCONVERSATION)" in cleaned_piece.upper(),
        "END_CONVERSATION" in cleaned_piece.upper(),
        "ENDCONVERSATION" in cleaned_piece.upper(),
    ])
    
    return should_filter


def run_tests():
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}🧪 (END_CONVERSATION) 过滤逻辑测试")
    print(f"{Fore.CYAN}{'='*70}\n")
    
    test_cases = [
        # (输入, 应该被过滤?, 描述)
        ("你好，很高兴认识你", False, "普通文本"),
        ("这是**加粗**文本", False, "包含 Markdown 加粗"),
        ("这是__下划线__文本", False, "包含 Markdown 下划线"),
        ("(END_CONVERSATION)", True, "完整的特殊标记"),
        ("好的，再见 (END_CONVERSATION)", True, "文本后带标记"),
        ("(ENDCONVERSATION)", True, "无下划线变体"),
        ("END_CONVERSATION", True, "无括号变体"),
        ("ENDCONVERSATION", True, "无括号无下划线变体"),
        ("某些文字(END_", False, "流式输入 - 第1段（不完整）"),
        ("CONVERSATION)", False, "流式输入 - 第2段（不完整）"),
        ("好的(END_CONVER", False, "流式输入 - 中间截断"),
        ("SATION)再见", False, "流式输入 - 完成截断"),
        ("end_conversation", True, "小写变体"),
        ("(end_conversation)", True, "小写带括号"),
        ("End Conversation", True, "带空格变体"),
        ("用代码写`END_CONVERSATION`", True, "行内代码中的标记（下划线会被删除）"),
        ("**END**_CONVERSATION", True, "Markdown 格式混合（清理后会匹配）"),
    ]
    
    passed = 0
    failed = 0
    
    for i, (text, expected_filter, description) in enumerate(test_cases, 1):
        result = test_filter_logic(text)
        
        if result == expected_filter:
            print(f"{Fore.GREEN}✅ 测试 {i}: {description}")
            print(f"   输入: '{text}'")
            print(f"   预期: {'过滤' if expected_filter else '通过'} | 实际: {'过滤' if result else '通过'}\n")
            passed += 1
        else:
            print(f"{Fore.RED}❌ 测试 {i}: {description}")
            print(f"   输入: '{text}'")
            print(f"   预期: {'过滤' if expected_filter else '通过'} | 实际: {'过滤' if result else '通过'}")
            print(f"   {Fore.YELLOW}⚠️  这个文本可能会被 TTS 错误朗读！\n")
            failed += 1
    
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}📊 测试摘要")
    print(f"{Fore.CYAN}{'='*70}\n")
    print(f"{Fore.GREEN}✅ 通过: {passed}/{len(test_cases)}")
    if failed > 0:
        print(f"{Fore.RED}❌ 失败: {failed}/{len(test_cases)}")
        return False
    else:
        print(f"{Fore.GREEN}🎉 所有测试通过！")
        return True


def test_sentence_level_filter(sentence: str) -> bool:
    """
    测试句子级别的过滤（SmartSentenceSplitter 之后）
    这是最后一道防线
    """
    sentence_upper = sentence.upper()
    should_filter = any([
        "(END_CONVERSATION)" in sentence_upper,
        "(ENDCONVERSATION)" in sentence_upper,
        "END_CONVERSATION" in sentence_upper,
        "ENDCONVERSATION" in sentence_upper,
    ])
    return should_filter


def test_streaming_scenario():
    """测试流式输入场景 - 句子级别过滤"""
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}🔄 流式输入场景测试（句子级别）")
    print(f"{Fore.CYAN}{'='*70}\n")
    
    print(f"{Fore.YELLOW}说明：流式输入时，单个 chunk 可能不完整，无法在 chunk 级别过滤。")
    print(f"{Fore.YELLOW}真正的过滤发生在分句器（SmartSentenceSplitter）输出完整句子后。\n")
    
    # 模拟分句器输出的完整句子
    sentences = [
        "好的，再见。",
        "(END_CONVERSATION)",  # 这是LLM错误输出的标记
        "谢谢使用！",
    ]
    
    print(f"{Fore.YELLOW}模拟分句器输出的句子：\n")
    
    sent_to_tts = []
    for i, sentence in enumerate(sentences, 1):
        filtered = test_sentence_level_filter(sentence)
        status = f"{Fore.RED}🚫 过滤" if filtered else f"{Fore.GREEN}✅ 送入TTS"
        print(f"句子 {i}: '{sentence}' → {status}")
        if not filtered:
            sent_to_tts.append(sentence)
    
    print(f"\n{Fore.CYAN}最终送入 TTS 队列的句子: {Fore.WHITE}{sent_to_tts}")
    
    # 检查是否包含完整的特殊标记
    final_text = ''.join(sent_to_tts)
    if "END" in final_text.upper() and "CONVERSATION" in final_text.upper():
        print(f"{Fore.RED}❌ 失败：特殊标记泄露到 TTS！")
        return False
    else:
        print(f"{Fore.GREEN}✅ 成功：特殊标记被正确过滤")
        return True


if __name__ == "__main__":
    print(f"\n{Fore.MAGENTA}{'#'*80}")
    print(f"{Fore.MAGENTA}# (END_CONVERSATION) 过滤逻辑验证 #")
    print(f"{Fore.MAGENTA}{'#'*80}\n")
    
    test1 = run_tests()
    test2 = test_streaming_scenario()
    
    print(f"\n{Fore.MAGENTA}{'#'*80}")
    if test1 and test2:
        print(f"{Fore.GREEN}# ✅ 所有测试通过，过滤逻辑正确 #")
    else:
        print(f"{Fore.RED}# ❌ 测试失败，需要修复过滤逻辑 #")
    print(f"{Fore.MAGENTA}{'#'*80}\n")

