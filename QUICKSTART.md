# 🚀 快速启动指南

## 30秒快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，设置你的 OpenAI API Key
# OPENAI_API_KEY=your-api-key-here
```

### 3. 启动语音Agent

```bash
python main.py
```

就这么简单！🎉

---

## 启动选项

### 交互式对话模式（默认）

```bash
python main.py
```

**功能:**
- ✅ 完整的对话交互
- ✅ 真实TTS语音播放
- ✅ 推理过程可视化
- ✅ KV Cache自动优化

### 禁用语音模式

```bash
python main.py --no-tts
```

适用于:
- 无扬声器环境
- 调试模式
- 快速测试

### 测试模式

```bash
python main.py --test
```

**功能:**
- 快速验证所有功能
- 自动运行3个测试用例
- 显示性能统计

---

## 使用示例

启动后，你会看到：

```
================================================================================
🚀 Robot Agent Mindflow - 语音交互版
================================================================================

✨ 核心优势:
  📊 OpenAI原生API - 100%可靠的工具调用
  🛠️  LangChain工具池 - 17个强大工具
  ⚡ KV Cache优化 - 多轮对话速度提升3-5倍
  🗣️  Edge TTS - 真实语音播放(晓晓语音)

💡 试试这些命令(会播放语音):
  1️⃣  现在几点了?(语音播报时间)
  2️⃣  计算sqrt(2)保留3位小数(听听计算结果)
  ...

💬 您: _
```

### 示例对话

```
💬 您: 现在几点了?

🧠 混合架构推理过程(OpenAI原生 + LangChain工具)
──────────────────────────────────────────────────────────
📡 调用OpenAI API进行推理...
──────────────────────────────────────────────────────────

✅ 模型决定调用工具(共1个)

📍 推理步骤 1
══════════════════════════════════════════════════════════
✅ 模型决策:
   → 选择工具: time_tool

📥 模型决定的参数:
──────────────────────────────────────────────────────────
   {
         "query_type": "current_time"
   }
──────────────────────────────────────────────────────────

📤 工具返回结果:
──────────────────────────────────────────────────────────
   14:30:25
──────────────────────────────────────────────────────────

💭 模型基于工具结果生成最终回答...
══════════════════════════════════════════════════════════
💬 最终回答
══════════════════════════════════════════════════════════
现在是下午2点30分25秒。
══════════════════════════════════════════════════════════

🎵 TTS音频播放
══════════════════════════════════════════════════════════
🔊 [播放 1/1] 现在是下午2点30分25秒。
   ⏰ 开始时间: 14:30:26.123
   音频播放耗时: 2.345s
✅ [完成 1]

⚡ 响应耗时: 3.21秒
📞 工具调用: 1次
🗣️  TTS分段: 1个
🔊 语音播放: ✅ 完成
```

---

## 可用命令

在对话中输入：

| 命令 | 功能 |
|------|------|
| `help` | 查看帮助 |
| `stats` | 查看缓存统计 |
| `clear` | 清除对话历史 |
| `q` 或 `quit` | 退出程序 |

---

## 常见问题

### Q: 没有语音输出？

**A:** 检查以下几点:
1. 确保扬声器已开启
2. 检查 `pip install pygame` 是否成功
3. 尝试 `python main.py --test` 测试

### Q: API Key错误？

**A:**
```bash
# 检查 .env 文件
cat .env

# 确保格式正确
OPENAI_API_KEY=sk-...
```

### Q: 导入错误？

**A:**
```bash
# 重新安装依赖
pip install -r requirements.txt

# 或使用新架构
pip install -e .
```

### Q: 如何禁用语音？

**A:**
```bash
# 方式1: 命令行参数
python main.py --no-tts

# 方式2: 环境变量
# 在 .env 中设置
ENABLE_TTS=false
```

---

## 进阶使用

### 使用新架构API

```python
from src.core import HybridReasoningAgent
from src.tools import load_all_tools
from src.services.tts import TTSFactory, TTSProvider

# 加载工具
tools = load_all_tools()

# 创建Agent
agent = HybridReasoningAgent(tools=tools)

# 执行推理
result = agent.run("现在几点?")
print(result.output)

# 播放TTS
from src.services.tts import TTSOptimizer
tts = TTSFactory.create_tts(TTSProvider.EDGE)
optimizer = TTSOptimizer(tts_engine=tts)
optimizer.optimize_and_play(result.output)
```

### 自定义配置

编辑 `.env` 文件:

```bash
# LLM配置
LLM_MODEL=gpt-4-turbo-preview
TEMPERATURE=0.0

# TTS配置
TTS_VOICE=zh-CN-XiaoxiaoNeural  # 晓晓(温柔女声)
TTS_RATE=+0%                     # 语速
TTS_VOLUME=+0%                   # 音量

# Agent配置
ENABLE_CACHE=true
MAX_RETRIES=3
```

可用的中文语音:
- `zh-CN-XiaoxiaoNeural` - 晓晓(温柔女声) ⭐推荐
- `zh-CN-XiaomoNeural` - 晓墨(知性女声)
- `zh-CN-YunxiNeural` - 云希(阳光男声) ⭐推荐
- `zh-CN-YunyangNeural` - 云扬(新闻男声)

---

## 目录结构

```
robot_agent_mindflow/
├── main.py                   # 🚀 主入口（从这里启动！）
├── src/                      # 源代码
│   ├── core/                 # 核心层
│   ├── services/             # 服务层
│   └── tools/                # 工具层
├── examples/                 # 示例代码
├── docs/                     # 文档
├── .env                      # 环境变量（需要创建）
└── requirements.txt          # 依赖列表
```

---

## 下一步

1. ✅ 启动成功后，试试各种对话
2. 📖 阅读 [架构文档](docs/architecture.md) 了解设计
3. 🔧 查看 [迁移指南](docs/migration_guide.md) 学习新架构
4. 💡 运行 [示例代码](examples/) 学习API使用

---

## 获取帮助

- 📖 完整文档: `docs/architecture.md`
- 💡 示例代码: `examples/`
- 🐛 问题反馈: GitHub Issues

---

**享受与AI的对话吧！🎉**
