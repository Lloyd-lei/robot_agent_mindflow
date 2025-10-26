# 🚀 Robot Agent Mindflow - 新架构版本

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> 混合架构AI Agent - OpenAI原生 + LangChain工具池 + KV Cache优化

---

## ✨ 新架构亮点

### 🏗️ 模块化设计

```
robot_agent_mindflow/
├── src/                   # 📦 源代码
│   ├── core/             # 🔧 核心层 (Agent, Tools, Config)
│   ├── services/         # 🎯 服务层 (TTS, Voice)
│   └── tools/            # 🛠️ 工具层 (Basic, Reception, System)
├── examples/             # 📚 示例代码
├── tests/                # ✅ 测试代码
└── docs/                 # 📖 文档
```

### 🎯 核心特性

- ✅ **分层架构** - 清晰的职责划分
- ✅ **依赖倒置** - 面向接口编程
- ✅ **单一职责** - 每个模块只做一件事
- ✅ **开闭原则** - 易于扩展,无需修改
- ✅ **向后兼容** - 完全兼容旧代码

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

可选:安装为包
```bash
pip install -e .
```

### 2. 配置环境

```bash
cp .env.example .env
# 编辑 .env,设置 OPENAI_API_KEY
```

### 3. 运行示例

```bash
# 新架构演示
python examples/demo_new_architecture.py

# 旧代码仍可运行
python demo_hybrid.py
```

---

## 📖 使用示例

### 基础使用

```python
from src.core import HybridReasoningAgent
from src.tools import load_all_tools

# 加载所有工具
tools = load_all_tools()

# 创建 Agent
agent = HybridReasoningAgent(tools=tools)

# 执行推理
result = agent.run("计算sqrt(2)保留3位小数")

print(f"回答: {result.output}")
print(f"工具调用: {result.tool_calls}次")
```

### 带 TTS 的使用

```python
from src.core import HybridReasoningAgent
from src.services.tts import TTSFactory, TTSProvider, TTSOptimizer
from src.tools import load_all_tools

# 创建 TTS
tts = TTSFactory.create_tts(
    provider=TTSProvider.EDGE,
    voice="zh-CN-XiaoxiaoNeural"
)

# 创建 Agent
tools = load_all_tools()
agent = HybridReasoningAgent(tools=tools)

# 执行推理
result = agent.run("现在几点了?")

# 播放语音
optimizer = TTSOptimizer(tts_engine=tts)
optimizer.optimize_and_play(result.output)
```

### 配置管理

```python
from src.core.config import settings

# 读取配置
print(settings.openai_api_key)
print(settings.llm_model)
print(settings.temperature)

# 检查环境
if settings.is_production():
    print("生产环境")
else:
    print("开发环境")
```

---

## 🛠️ 创建自定义工具

```python
from src.core.tools import BaseTool
from pydantic import BaseModel, Field

class MyToolInput(BaseModel):
    """工具输入"""
    arg: str = Field(description="参数说明")

class MyTool(BaseTool):
    """自定义工具"""

    name = "my_tool"
    description = "我的工具"
    args_schema = MyToolInput
    category = "basic"

    def execute(self, arg: str):
        """执行逻辑"""
        return f"处理结果: {arg}"

# 注册工具
from src.core.tools import tool_registry
tool_registry.register(MyTool())

# 使用工具
tools = tool_registry.get_all()
agent = HybridReasoningAgent(tools=tools)
```

---

## 📚 文档

- 📖 [架构设计文档](./docs/architecture.md)
- 🔄 [迁移指南](./docs/migration_guide.md)
- 🔧 [API文档](./docs/api.md) (待完善)

---

## 🧪 测试

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit

# 运行集成测试
pytest tests/integration
```

---

## 🎯 架构对比

### 旧架构

```python
# 所有代码在根目录,1000+行的单文件
from agent_hybrid import HybridReasoningAgent
from tools import CalculatorTool, TimeTool  # 1000+行
import config
```

**问题:**
- ❌ 代码组织混乱
- ❌ 职责不清晰
- ❌ 难以维护和扩展
- ❌ 测试困难

### 新架构

```python
# 模块化,分层清晰
from src.core import HybridReasoningAgent
from src.tools import load_all_tools
from src.core.config import settings
```

**优势:**
- ✅ 清晰的分层结构
- ✅ 单一职责原则
- ✅ 易于测试和扩展
- ✅ 向后兼容

---

## 🔄 迁移路径

```
旧代码 → 使用工具加载器 → 逐步迁移工具 → 完全迁移 → 新架构
```

详见 [迁移指南](./docs/migration_guide.md)

---

## 🌟 核心优势

### 1. 混合架构

- **OpenAI原生API** - 100%可靠的工具调用
- **LangChain工具池** - 17个强大工具
- **完美结合** - 兼得两者优势

### 2. KV Cache优化

- **系统提示词缓存** - 节省50%成本
- **对话历史缓存** - 速度提升3-5倍
- **自动优化** - 无需手动管理

### 3. TTS集成

- **Edge TTS** - 免费高质量语音
- **智能分句** - 自然流畅
- **防重叠播放** - 稳定可靠

### 4. 模块化设计

- **分层架构** - Core / Services / Tools
- **依赖倒置** - 面向接口编程
- **易于扩展** - 添加工具只需继承基类

---

## 📋 可用工具

### 基础工具 (8个)
- ✅ Calculator - 数学计算
- ✅ TimeTool - 时间查询
- ✅ TextAnalyzer - 文本分析
- ✅ UnitConverter - 单位转换
- ✅ DataComparison - 数据比较
- ✅ LogicReasoning - 逻辑推理
- ✅ LibraryManagement - 图书馆管理
- ✅ ConversationEnd - 对话结束检测

### 前台接待工具 (6个)
- ✅ VisitorRegistration - 访客登记
- ✅ MeetingRoom - 会议室管理
- ✅ EmployeeDirectory - 员工通讯录
- ✅ DirectionGuide - 路线指引
- ✅ PackageManagement - 包裹管理
- ✅ FAQ - 常见问题

### 系统工具 (3个)
- ✅ WebSearch - 网络搜索
- ✅ FileOperation - 文件操作
- ✅ Reminder - 提醒设置

---

## 🤝 贡献

欢迎贡献!请遵循:

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📝 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- OpenAI - GPT API
- LangChain - 工具生态
- Edge TTS - 免费TTS服务

---

## 📧 联系方式

- GitHub: [@Lloyd-lei](https://github.com/Lloyd-lei)
- Issues: [提交问题](https://github.com/Lloyd-lei/robot_agent_mindflow/issues)

---

**享受新架构带来的开发体验! 🎉**
