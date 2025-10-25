# 多语言 TTS 语音切换功能使用指南

**版本**: v1.3.0  
**日期**: 2025-10-25  
**功能**: AI Agent 自动检测语言并切换 TTS 语音

---

## 🎯 功能概述

Agent 现在支持 **6 种语言的智能语音切换**！当用户切换语言时，AI 会自动检测并切换到对应语言的 TTS 语音，提供更自然的多语言交互体验。

---

## 🌍 支持的语言

| 语言        | 默认语音              | 性别 | 说明             |
| ----------- | --------------------- | ---- | ---------------- |
| 🇨🇳 中文     | 晓晓 (XiaoxiaoNeural) | 女声 | 温柔亲切 ⭐ 默认 |
| 🇺🇸 英文     | Jenny (JennyNeural)   | 女声 | 友好自然（美式） |
| 🇯🇵 日文     | Nanami (NanamiNeural) | 女声 | 温柔甜美         |
| 🇪🇸 西班牙语 | Elvira (ElviraNeural) | 女声 | 热情活泼         |
| 🇫🇷 法语     | Denise (DeniseNeural) | 女声 | 优雅知性         |
| 🇻🇳 越南语   | HoaiMy (HoaiMyNeural) | 女声 | 亲切自然         |

### 可选语音

每种语言还提供了 2-3 个备选语音（不同性别/风格），详见 `tts_interface.py` 中的 `EDGE_TTS_VOICES` 配置。

---

## 🚀 使用方式

### 方式 1：自动检测（推荐）⭐

AI Agent 会自动检测用户输入的语言并切换语音，无需手动操作：

```
用户: "Hello, what's your name?"
Agent: [自动切换到英文语音]
       "My name is ChaCha. How can I help you today?"

用户: "你好，现在几点了？"
Agent: [自动切换回中文语音]
       "现在是下午3点15分。"
```

### 方式 2：显式请求

用户也可以明确要求切换语音：

```
用户: "请用英文语音说话"
Agent: [切换到英文语音]
       "Sure, I will speak in English from now on."

用户: "用日语语音介绍一下日本"
Agent: [切换到日文语音]
       "日本は東アジアに位置する島国です..."
```

---

## 💡 使用场景

### 场景 1：多语言客服

```
用户: "你好，我想咨询一下业务"
Agent: [中文语音] "您好，我是茶茶，很高兴为您服务！"

外国客户: "Hello, I need some help"
Agent: [自动切换到英文语音] "Sure! How can I assist you today?"

用户: "谢谢，再见"
Agent: [切换回中文语音] "好的，再见！"
```

### 场景 2：语言学习

```
用户: "教我一些日语日常用语"
Agent: [切换到日文语音]
       "こんにちは (你好)"
       "ありがとう (谢谢)"
       "さようなら (再见)"

用户: "用法语说'我爱你'"
Agent: [切换到法语语音] "Je t'aime"
```

### 场景 3：文化介绍

```
用户: "给我讲讲法国美食"
Agent: [切换到法语语音]
       "法国美食世界闻名，比如 Croissant（羊角包）..."

用户: "介绍一下日本樱花"
Agent: [切换到日文语音]
       "桜（さくら）是日本的国花..."
```

---

## 🔧 技术实现

### 核心组件

1. **`VoiceSelector` 工具** (`tools.py`)

   - LangChain BaseTool 实现
   - 支持 6 种语言的语音切换
   - 智能语言检测和映射

2. **语音配置** (`tts_interface.py`)

   - `EDGE_TTS_VOICES`: 完整的语音库
   - `LANGUAGE_TO_DEFAULT_VOICE`: 语言到默认语音的映射

3. **Agent 集成** (`agent_hybrid.py`)
   - 工具注入：`VoiceSelector` 注入 Agent 实例
   - System Prompt：指导 LLM 何时切换语音
   - 状态管理：语音状态持久化

### 切换流程

```
用户输入 → LLM检测语言 → 调用voiceSelector工具
→ 切换TTS语音 → 用新语音回复 → 状态保持
```

---

## 📊 性能特点

| 特性          | 说明                                 |
| ------------- | ------------------------------------ |
| ✅ 无延迟切换 | `set_voice()` 方法无需重新初始化 TTS |
| ✅ 状态持久化 | 语音状态自动保存，断线重连后保持     |
| ✅ 智能检测   | LLM 自动识别语言，无需用户指定       |
| ✅ 流式支持   | 与 Streaming TTS Pipeline 完美集成   |
| ✅ 零成本     | 使用免费的 Edge TTS 服务             |

---

## 🧪 测试方法

### 运行自动化测试

```bash
cd /Users/yudonglei/Desktop/agent_mvp
python test/test_multilingual_voice.py
```

测试内容：

- ✅ 6 种语言的自动检测
- ✅ 语音切换的准确性
- ✅ 状态持久化
- ✅ 手动语音验证（可选）

### 手动测试示例

启动主程序：

```bash
python main.py
```

测试对话：

```
用户: "Hello, how are you?"
→ 验证：语音是否切换到英文

用户: "こんにちは"
→ 验证：语音是否切换到日文

用户: "你好"
→ 验证：语音是否切换回中文
```

---

## 🎨 自定义语音

### 修改默认语音

编辑 `tts_interface.py` 中的 `LANGUAGE_TO_DEFAULT_VOICE`：

```python
LANGUAGE_TO_DEFAULT_VOICE = {
    "中文": "zh-CN-XiaomoNeural",  # 改为晓墨（知性女声）
    "英文": "en-GB-SoniaNeural",   # 改为英式英语
    # ...
}
```

### 添加新语言

1. 在 `EDGE_TTS_VOICES` 中添加新语音：

```python
"ko-KR-SunHiNeural": "SunHi - 亲切女声（韩语）",
```

2. 在 `LANGUAGE_TO_DEFAULT_VOICE` 中添加映射：

```python
"韩语": "ko-KR-SunHiNeural",
"korean": "ko-KR-SunHiNeural",
```

3. 更新 `VoiceSelector` 工具的描述（`tools.py`）

4. 更新 System Prompt（`agent_hybrid.py`）

---

## ⚠️ 注意事项

### 1. 语音质量

- Edge TTS 的语音质量非常高，接近真人
- 不同语言的语音质量可能略有差异
- 建议在实际使用前测试各语言的效果

### 2. 网络依赖

- Edge TTS 需要联网才能工作
- 网络不稳定可能导致 TTS 生成失败
- 建议在生产环境配置网络重试机制

### 3. LLM 语言检测

- Ollama Qwen2.5 对多语言的支持较好
- 如果使用其他 LLM，可能需要调整 System Prompt
- 复杂的混合语言可能导致误判

### 4. 性能影响

- 语音切换本身**无性能损耗**（<1ms）
- 但 LLM 语言检测会增加一次工具调用（+0.5-1 秒）
- 可以在 System Prompt 中优化检测逻辑

---

## 🔗 相关文档

- [ConversationSession API](./ConversationSession_API.md)
- [TTS 配置说明](./TTS配置说明.md)
- [Edge TTS 官方文档](https://github.com/rany2/edge-tts)

---

## 📝 更新日志

### v1.3.0 (2025-10-25)

- ✨ 新增多语言 TTS 语音切换功能
- 🌍 支持中、英、日、西、法、越 6 种语言
- 🤖 AI 自动检测语言并切换语音
- ⚡ 零延迟切换，状态持久化
- 🧪 完整的自动化测试套件

---

**维护者**: Lloyd  
**最后更新**: 2025-10-25
