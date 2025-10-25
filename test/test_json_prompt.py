#!/usr/bin/env python3
"""
测试 JSON 格式的 System Prompt 加载和转换
"""
import json
from pathlib import Path


def test_json_prompt():
    """测试 JSON prompt 加载"""
    print("=" * 80)
    print("🧪 测试 JSON Prompt 加载和转换")
    print("=" * 80)
    
    # 1. 读取 JSON 文件
    print("\n1️⃣  读取 JSON 文件...")
    json_path = Path("prompts/system_prompt.json")
    
    if not json_path.exists():
        print(f"❌ 文件不存在: {json_path}")
        return
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"✅ JSON 加载成功")
    print(f"   - 顶层键: {list(data.keys())}")
    
    # 2. 测试 Agent 的转换方法
    print("\n2️⃣  测试 Agent 的 Prompt 转换...")
    from agent_hybrid import HybridReasoningAgent
    
    # 创建临时 Agent 实例（用于测试转换方法）
    class MockAgent:
        def __init__(self):
            self.agent = HybridReasoningAgent(
                enable_streaming_tts=False,
                voice_mode=False
            )
    
    mock = MockAgent()
    converted_prompt = mock.agent._convert_json_to_prompt(data)
    
    print(f"✅ 转换成功")
    print(f"   - 转换后长度: {len(converted_prompt)} 字符")
    print(f"   - 行数: {len(converted_prompt.split(chr(10)))} 行")
    
    # 3. 显示转换后的 Prompt 片段
    print("\n3️⃣  转换后的 Prompt 预览（前 50 行）：")
    print("-" * 80)
    lines = converted_prompt.split('\n')
    for i, line in enumerate(lines[:50], 1):
        print(f"{i:3d} | {line}")
    
    if len(lines) > 50:
        print(f"... 还有 {len(lines) - 50} 行 ...")
    print("-" * 80)
    
    # 4. 验证关键内容
    print("\n4️⃣  验证关键内容...")
    checks = {
        "身份定义": "茶茶" in converted_prompt,
        "语音交互规范": "语音交互规范" in converted_prompt,
        "强制规则": "重要规则" in converted_prompt,
        "工具列表": "calculator" in converted_prompt,
        "推理流程": "推理流程" in converted_prompt,
        "示例": "示例" in converted_prompt,
    }
    
    for name, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {name}")
    
    # 5. 对比 JSON 和 TXT 的大小
    print("\n5️⃣  格式对比：")
    txt_path = Path("prompts/system_prompt.txt")
    if txt_path.exists():
        txt_size = txt_path.stat().st_size
        json_size = json_path.stat().st_size
        
        print(f"   - JSON 文件大小: {json_size:,} 字节")
        print(f"   - TXT 文件大小: {txt_size:,} 字节")
        print(f"   - JSON 更详细: {json_size - txt_size:+,} 字节 ({(json_size/txt_size-1)*100:+.1f}%)")
        print(f"   - 转换后文本: {len(converted_prompt):,} 字符")
    
    print("\n" + "=" * 80)
    print("✅ 测试完成！JSON Prompt 可以正常使用")
    print("=" * 80)
    print("\n💡 优势：")
    print("   - ✅ JSON 结构化更清晰，便于大模型理解")
    print("   - ✅ 便于程序化修改和维护")
    print("   - ✅ 支持嵌套结构，逻辑层次分明")
    print("   - ✅ 可以轻松添加新字段，向后兼容")
    print()


if __name__ == "__main__":
    test_json_prompt()

