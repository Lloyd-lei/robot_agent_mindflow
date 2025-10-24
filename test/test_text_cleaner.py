#!/usr/bin/env python
"""
文本清理功能测试脚本

功能：
- 测试 SmartSentenceSplitter 的文本清理功能
- 验证 markdown、代码、链接、缩写等的处理效果
"""

from colorama import Fore, Style, init
from streaming_tts_pipeline import SmartSentenceSplitter

init(autoreset=True)

def print_comparison(title: str, original: str, cleaned: str):
    """打印清理前后对比"""
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{title}")
    print(f"{'='*70}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}📝 原始文本:{Style.RESET_ALL}")
    print(f"   {original}")
    print(f"{Fore.GREEN}✨ 清理后:{Style.RESET_ALL}")
    print(f"   {cleaned}")


def test_markdown_cleaning():
    """测试 Markdown 格式清理"""
    print(f"\n{Fore.MAGENTA}{'='*70}")
    print("🧪 测试 1: Markdown 格式清理")
    print(f"{'='*70}{Style.RESET_ALL}")
    
    splitter = SmartSentenceSplitter()
    
    test_cases = [
        ("加粗文本", "这是**重要**的内容。", "这是重要的内容。"),
        ("斜体文本", "这是*强调*的内容。", "这是强调的内容。"),
        ("行内代码", "使用`print()`函数。", "使用print()函数。"),
        ("链接", "访问[官网](https://example.com)了解更多。", "访问官网了解更多。"),
        ("列表标记", "- 第一项\n- 第二项", "第一项\n第二项"),
        ("标题", "## 重要通知\n内容在这里", "重要通知\n内容在这里"),
        ("代码块", "这是代码：\n```python\nprint('hello')\n```\n结束。", "这是代码：\n[代码内容]\n结束。"),
    ]
    
    for name, original, expected in test_cases:
        cleaned = splitter._clean_text(original)
        status = "✅" if cleaned.strip() == expected.strip() else f"❌ (期望: {expected})"
        print(f"\n{status} {name}")
        print(f"   原始: {original}")
        print(f"   清理: {cleaned}")


def test_abbreviation_expansion():
    """测试英文缩写展开"""
    print(f"\n{Fore.MAGENTA}{'='*70}")
    print("🧪 测试 2: 英文缩写展开")
    print(f"{'='*70}{Style.RESET_ALL}")
    
    splitter = SmartSentenceSplitter()
    
    test_cases = [
        ("AI缩写", "AI技术发展很快。", "人工智能技术发展很快。"),
        ("TTS缩写", "使用TTS合成语音。", "使用文字转语音合成语音。"),
        ("API缩写", "调用API获取数据。", "调用A P I获取数据。"),
        ("LLM缩写", "LLM是大语言模型。", "大语言模型是大语言模型。"),
        ("混合使用", "AI和TTS技术。", "人工智能和文字转语音技术。"),
        ("不误替换", "MAIL不应该被替换。", "MAIL不应该被替换。"),
    ]
    
    for name, original, expected in test_cases:
        cleaned = splitter._clean_text(original)
        status = "✅" if cleaned.strip() == expected.strip() else f"❌ (期望: {expected})"
        print(f"\n{status} {name}")
        print(f"   原始: {original}")
        print(f"   清理: {cleaned}")


def test_real_world_examples():
    """测试真实场景示例"""
    print(f"\n{Fore.MAGENTA}{'='*70}")
    print("🧪 测试 3: 真实场景示例")
    print(f"{'='*70}{Style.RESET_ALL}")
    
    splitter = SmartSentenceSplitter()
    
    test_cases = [
        (
            "LLM回复（带markdown）",
            """好的，我来解释一下**AI**的原理。

## 核心概念
- 机器学习
- 深度学习
- 神经网络

详情请访问[AI Wiki](https://ai.wiki)。""",
        ),
        (
            "代码解释",
            """使用`Python`代码如下：
```python
def hello():
    print("Hello, AI!")
```
这段代码很简单。""",
        ),
        (
            "技术讨论",
            """**LLM**和**TTS**结合，可以实现AI语音助手。通过调用API实现功能。""",
        ),
    ]
    
    for name, original in test_cases:
        cleaned = splitter._clean_text(original)
        print_comparison(name, original, cleaned)


def test_streaming_flow():
    """测试流式分句（带清理）"""
    print(f"\n{Fore.MAGENTA}{'='*70}")
    print("🧪 测试 4: 流式分句 + 文本清理")
    print(f"{'='*70}{Style.RESET_ALL}")
    
    splitter = SmartSentenceSplitter(min_chunk_length=5, max_chunk_length=50)
    
    # 模拟 LLM 流式输出（带 markdown）
    llm_stream = [
        "这是一个**重要**的",
        "测试。使用`code`",
        "代码。访问[链接](http://test.com)",
        "了解更多。AI技术很好。",
    ]
    
    print(f"\n{Fore.YELLOW}📡 模拟 LLM 流式输出:{Style.RESET_ALL}")
    all_sentences = []
    for i, chunk in enumerate(llm_stream, 1):
        print(f"   Chunk {i}: {chunk}")
        sentences = splitter.add_text(chunk)
        if sentences:
            for s in sentences:
                all_sentences.append(s)
                print(f"   {Fore.GREEN}→ 输出句子: {s}{Style.RESET_ALL}")
    
    # 清空缓冲区
    last_sentence = splitter.flush()
    if last_sentence:
        all_sentences.append(last_sentence)
        print(f"   {Fore.GREEN}→ 输出句子: {last_sentence}{Style.RESET_ALL}")
    
    print(f"\n{Fore.CYAN}📊 最终结果:{Style.RESET_ALL}")
    print(f"   总共输出 {len(all_sentences)} 个句子")
    for i, s in enumerate(all_sentences, 1):
        print(f"   {i}. {s}")


def main():
    """主测试流程"""
    print(f"\n{Fore.GREEN}{'='*70}")
    print(f"  📋 SmartSentenceSplitter 文本清理功能测试")
    print(f"{'='*70}{Style.RESET_ALL}\n")
    
    try:
        # 运行所有测试
        test_markdown_cleaning()
        test_abbreviation_expansion()
        test_real_world_examples()
        test_streaming_flow()
        
        # 总结
        print(f"\n{Fore.GREEN}{'='*70}")
        print(f"  ✅ 所有测试完成！")
        print(f"{'='*70}{Style.RESET_ALL}\n")
        
        print(f"{Fore.CYAN}📝 说明：{Style.RESET_ALL}")
        print(f"   - 文本清理功能已集成到 SmartSentenceSplitter")
        print(f"   - 所有流式 TTS 输出都会自动清理 markdown 和特殊符号")
        print(f"   - 缩写会自动展开为 TTS 友好格式")
        print(f"   - 无需额外配置，开箱即用！")
        
    except Exception as e:
        print(f"\n{Fore.RED}❌ 测试失败: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)

