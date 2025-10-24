# TTS 配置说明

## ✅ 当前状态

已成功集成 **Edge TTS** 作为默认 TTS 服务！

- ✅ Edge TTS 合成成功
- ✅ pygame 音频播放成功  
- ✅ Agent 自动集成
- ✅ 范型接口支持

---

## 🎯 核心特性

### 1️⃣ **范型接口设计**
所有 TTS 服务统一接口，轻松切换：
```python
from tts_interface import TTSFactory, TTSProvider

# 创建 TTS 实例
tts = TTSFactory.create_tts(
    provider=TTSProvider.EDGE,  # 或 AZURE, OPENAI
    voice="zh-CN-XiaoxiaoNeural"
)

# 合成语音
audio = await tts.synthesize("你好，世界！")
```

### 2️⃣ **自动集成**
Agent 自动使用 Edge TTS，无需额外配置：
```python
from agent_hybrid import HybridReasoningAgent

agent = HybridReasoningAgent(
    enable_tts=True,      # 启用 TTS（自动使用 Edge TTS）
    voice_mode=True       # 启用语音反馈
)
```

---

## 🔧 支持的 TTS 服务

### 1. **Edge TTS**（当前默认）⭐

**优势**：
- ✅ 完全免费
- ✅ 音质优秀（与 Azure 同源）
- ✅ 无需 API 密钥
- ✅ 支持多种中文语音

**风险**：
- ⚠️ 非官方接口（可能失效）
- ⚠️ 不保证稳定性

**推荐场景**：开发测试、个人项目

**使用方法**：
```python
# 已自动启用，无需额外配置
agent = HybridReasoningAgent(enable_tts=True)
```

**可选语音**：
```python
from tts_interface import TTSFactory, TTSProvider

tts = TTSFactory.create_tts(
    provider=TTSProvider.EDGE,
    voice="zh-CN-XiaoxiaoNeural",  # 晓晓 - 温柔女声（默认）
    # voice="zh-CN-YunxiNeural",   # 云希 - 阳光男声
    # voice="zh-CN-XiaomoNeural",  # 晓墨 - 知性女声
    rate="+0%",    # 语速：-50% 到 +50%
    volume="+0%"   # 音量：-50% 到 +50%
)
```

---

### 2. **Azure TTS**（官方付费）

**优势**：
- ✅ 官方支持，稳定可靠
- ✅ 99.9% SLA 保证
- ✅ 商用合规
- ✅ 支持 SSML 高级控制

**成本**：
- 💰 免费额度：每月 50 万字符
- 💰 付费价格：$16/百万字符

**推荐场景**：生产环境、商业项目

**使用方法**：
```python
# 1. 安装依赖
# pip install azure-cognitiveservices-speech

# 2. 在 .env 中配置
AZURE_SPEECH_KEY=your_azure_key
AZURE_SPEECH_REGION=eastasia

# 3. 创建 TTS 实例
from tts_interface import TTSFactory, TTSProvider

tts = TTSFactory.create_tts(
    provider=TTSProvider.AZURE,
    api_key="your_azure_key",
    region="eastasia",
    voice="zh-CN-XiaoxiaoNeural"
)

# 4. 传给 Agent
agent = HybridReasoningAgent(
    enable_tts=True,
    tts_engine=tts
)
```

---

### 3. **OpenAI TTS**

**优势**：
- ✅ 集成简单（已有 OpenAI API）
- ✅ 支持流式合成
- ✅ 音质优秀

**成本**：
- 💰 $15/百万字符

**限制**：
- ❌ 中文语音较少（通用语音，非专门优化）

**推荐场景**：已使用 OpenAI 的项目

**使用方法**：
```python
from tts_interface import TTSFactory, TTSProvider

tts = TTSFactory.create_tts(
    provider=TTSProvider.OPENAI,
    api_key="your_openai_key",
    model="tts-1",      # tts-1-hd 质量更高
    voice="alloy"       # alloy, echo, fable, onyx, nova, shimmer
)

agent = HybridReasoningAgent(
    enable_tts=True,
    tts_engine=tts
)
```

---

## 📝 配置示例

### 示例 1：使用默认 Edge TTS

```python
from agent_hybrid import HybridReasoningAgent

# 最简单的方式 - 自动使用 Edge TTS
agent = HybridReasoningAgent(
    enable_tts=True,
    voice_mode=True
)

# 运行对话
result = agent.run_with_tts_demo("你好，现在几点了？")
```

### 示例 2：自定义 Edge TTS 语音

```python
from agent_hybrid import HybridReasoningAgent
from tts_interface import TTSFactory, TTSProvider

# 创建自定义 Edge TTS（男声）
tts = TTSFactory.create_tts(
    provider=TTSProvider.EDGE,
    voice="zh-CN-YunxiNeural",  # 云希男声
    rate="+10%",                 # 语速加快 10%
    volume="+5%"                 # 音量增加 5%
)

# 传给 Agent
agent = HybridReasoningAgent(
    enable_tts=True,
    voice_mode=True,
    tts_engine=tts
)
```

### 示例 3：切换到 Azure TTS（生产环境）

```python
from agent_hybrid import HybridReasoningAgent
from tts_interface import TTSFactory, TTSProvider
import os

# 从环境变量读取密钥
azure_key = os.getenv("AZURE_SPEECH_KEY")
azure_region = os.getenv("AZURE_SPEECH_REGION", "eastasia")

# 创建 Azure TTS
tts = TTSFactory.create_tts(
    provider=TTSProvider.AZURE,
    api_key=azure_key,
    region=azure_region,
    voice="zh-CN-XiaoxiaoNeural"
)

# 传给 Agent
agent = HybridReasoningAgent(
    enable_tts=True,
    voice_mode=True,
    tts_engine=tts
)
```

---

## 🎵 可用语音列表

### Edge TTS / Azure TTS（中文）

| 语音名称 | 性别 | 特点 | 推荐场景 |
|---------|-----|------|---------|
| `zh-CN-XiaoxiaoNeural` | 女 | 温柔亲切 | 客服、助手（默认）|
| `zh-CN-XiaomoNeural` | 女 | 知性温和 | 教育、专业讲解 |
| `zh-CN-XiaoyiNeural` | 女 | 成熟稳重 | 商务、正式场合 |
| `zh-CN-YunxiNeural` | 男 | 阳光自然 | 客服、助手 |
| `zh-CN-YunyangNeural` | 男 | 新闻播报 | 播报、通知 |
| `zh-CN-YunjianNeural` | 男 | 体育解说 | 运动、激情场景 |

### OpenAI TTS

| 语音名称 | 特点 |
|---------|------|
| `alloy` | 中性，平衡 |
| `echo` | 男性，沉稳 |
| `fable` | 英式，优雅 |
| `onyx` | 男性，深沉 |
| `nova` | 女性，活泼 |
| `shimmer` | 女性，温柔 |

---

## 🔄 动态切换 TTS

可以运行时切换 TTS 服务：

```python
from tts_interface import TTSFactory, TTSProvider

class MultiTTSAgent:
    """支持动态切换 TTS 的 Agent"""
    
    def __init__(self):
        self.tts_providers = {
            'edge': TTSFactory.create_tts(
                provider=TTSProvider.EDGE,
                voice="zh-CN-XiaoxiaoNeural"
            ),
            'azure': TTSFactory.create_tts(
                provider=TTSProvider.AZURE,
                api_key="your_key",
                region="eastasia",
                voice="zh-CN-XiaoxiaoNeural"
            )
        }
        self.current_provider = 'edge'
    
    def switch_tts(self, provider: str):
        """切换 TTS 服务"""
        if provider in self.tts_providers:
            self.current_provider = provider
            print(f"✅ 已切换到 {provider.upper()} TTS")
        else:
            print(f"❌ 不支持的 TTS: {provider}")
    
    def synthesize(self, text: str):
        """使用当前 TTS 合成"""
        tts = self.tts_providers[self.current_provider]
        return asyncio.run(tts.synthesize(text))
```

---

## 🚀 快速测试

### 测试 Edge TTS
```bash
python test_tts_integration.py
```

### 测试 Agent + TTS
```bash
python demo_hybrid.py
```

输入示例：
- "现在几点了？"
- "计算 sqrt(2) 保留 3 位小数"
- "图书馆有关于 Python 的书吗？"

---

## 📦 依赖安装

```bash
# Edge TTS（必需）
pip install edge-tts>=7.0.0

# 音频播放（必需）
pip install pygame==2.5.2

# Azure TTS（可选）
pip install azure-cognitiveservices-speech

# 已在 requirements.txt 中
pip install -r requirements.txt
```

---

## ⚠️ 注意事项

1. **Edge TTS 稳定性**
   - 完全依赖微软服务
   - 可能会突然失效
   - 建议生产环境准备备用方案

2. **网络连接**
   - TTS 需要网络访问
   - 建议添加重试机制（已内置）

3. **音频格式**
   - Edge TTS: MP3
   - Azure TTS: WAV/MP3（可配置）
   - OpenAI TTS: MP3/WAV/FLAC/OPUS

4. **性能优化**
   - 使用异步调用
   - 并发生成音频分段
   - 边生成边播放（已实现）

---

## 🎉 总结

- ✅ **当前方案**：Edge TTS（免费、高质量）
- ✅ **推荐配置**：开发用 Edge TTS，生产用 Azure TTS
- ✅ **切换方便**：范型接口，一行代码切换
- ✅ **开箱即用**：默认配置已优化

需要帮助？查看：
- `test_tts_integration.py` - 测试脚本
- `tts_interface.py` - TTS 接口定义
- `demo_hybrid.py` - 完整示例

