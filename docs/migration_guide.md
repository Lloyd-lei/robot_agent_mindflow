# 迁移指南

## 从旧架构迁移到新架构

本指南帮助你从旧的扁平结构迁移到新的模块化架构。

---

## 快速对比

### 旧架构 (根目录)

```
robot_agent_mindflow/
├── agent_hybrid.py          # Agent
├── tools.py                 # 所有工具(1000+行)
├── tts_optimizer.py         # TTS
├── tts_interface.py         # TTS接口
├── voice_feedback.py        # 语音反馈
├── config.py                # 配置
├── demo_hybrid.py           # 演示
└── ...
```

### 新架构 (src/)

```
robot_agent_mindflow/
├── src/
│   ├── core/                # 核心层
│   ├── services/            # 服务层
│   ├── tools/               # 工具层
│   └── utils/               # 工具类
├── examples/                # 示例
├── tests/                   # 测试
└── docs/                    # 文档
```

---

## 代码迁移对照表

### 1. 导入 Agent

**旧代码:**
```python
from agent_hybrid import HybridReasoningAgent
```

**新代码:**
```python
from src.core import HybridReasoningAgent
```

### 2. 导入工具

**旧代码:**
```python
from tools import CalculatorTool, TimeTool
```

**新代码:**
```python
# 方式1: 使用加载器(推荐,向后兼容)
from src.tools import load_all_tools
tools = load_all_tools()

# 方式2: 直接导入(新工具)
from src.tools.basic.calculator import CalculatorTool
from src.tools.basic.time_tool import TimeTool
```

### 3. 导入配置

**旧代码:**
```python
import config
api_key = config.OPENAI_API_KEY
```

**新代码:**
```python
from src.core.config import settings
api_key = settings.openai_api_key
```

### 4. 导入 TTS

**旧代码:**
```python
from tts_interface import TTSFactory, TTSProvider
from tts_optimizer import TTSOptimizer
```

**新代码:**
```python
from src.services.tts import TTSFactory, TTSProvider, TTSOptimizer
```

### 5. 导入语音反馈

**旧代码:**
```python
from voice_feedback import VoiceWaitingFeedback
```

**新代码:**
```python
from src.services.voice import VoiceWaitingFeedback
```

---

## 完整迁移示例

### 旧代码

```python
# demo_old.py
from agent_hybrid import HybridReasoningAgent
from tools import (
    CalculatorTool,
    TimeTool,
    ConversationEndDetector
)
import config

# 初始化工具
tools = [
    CalculatorTool(),
    TimeTool(),
    ConversationEndDetector()
]

# 创建Agent
agent = HybridReasoningAgent(
    api_key=config.OPENAI_API_KEY,
    model=config.LLM_MODEL,
    temperature=config.TEMPERATURE
)

# 执行
result = agent.run("计算sqrt(2)")
print(result['output'])
```

### 新代码

```python
# examples/demo_new.py
from src.core import HybridReasoningAgent
from src.tools import load_all_tools

# 加载所有工具
tools = load_all_tools()

# 创建Agent (自动从配置读取)
agent = HybridReasoningAgent(tools=tools)

# 执行
result = agent.run("计算sqrt(2)")
print(result.output)  # 注意: 使用属性而非字典
```

---

## 配置迁移

### 旧配置 (config.py)

```python
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4-turbo-preview")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0"))
```

### 新配置 (src/core/config/settings.py)

使用 Pydantic Settings,支持:
- ✅ 类型验证
- ✅ 默认值
- ✅ 环境变量
- ✅ 配置验证

```python
from src.core.config import settings

# 直接使用
api_key = settings.openai_api_key
model = settings.llm_model
temperature = settings.temperature

# 检查环境
if settings.is_production():
    # 生产环境逻辑
    pass
```

---

## 返回值变化

### Agent 返回值

**旧代码 (字典):**
```python
result = agent.run("query")

result['success']         # bool
result['output']          # str
result['tool_calls']      # int
result['reasoning_steps'] # list
```

**新代码 (数据类):**
```python
result = agent.run("query")  # AgentResponse 对象

result.success            # bool
result.output             # str
result.tool_calls         # int
result.reasoning_steps    # list
result.metadata           # dict
result.error              # Optional[str]
```

---

## 工具开发变化

### 旧工具

```python
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

class MyTool(BaseTool):
    name = "my_tool"
    description = "..."

    def _run(self, **kwargs):
        # 直接实现逻辑
        return "result"
```

### 新工具

```python
from src.core.tools import BaseTool
from pydantic import BaseModel, Field

class MyTool(BaseTool):
    name = "my_tool"
    description = "..."
    category = "basic"  # 新增: 工具分类
    version = "1.0.0"    # 新增: 版本号

    def execute(self, **kwargs):
        # 实现核心逻辑
        return "result"

    # 可选: 钩子方法
    def before_run(self, **kwargs):
        # 执行前处理
        return kwargs

    def after_run(self, result):
        # 执行后处理
        return result
```

---

## 逐步迁移策略

### 阶段 1: 保持兼容(当前)

使用工具加载器,保持向后兼容:

```python
# 仍然使用旧的 tools.py
from src.tools import load_all_tools
tools = load_all_tools()
```

### 阶段 2: 逐步替换

逐个工具迁移到新结构:

```python
# 部分使用新工具,部分使用旧工具
from src.tools.basic.calculator import CalculatorTool
from src.tools import load_all_tools

new_tools = [CalculatorTool()]
old_tools = load_all_tools()
all_tools = new_tools + old_tools
```

### 阶段 3: 完全迁移

所有工具都迁移到新结构:

```python
# 全部使用新工具
from src.tools.basic import CalculatorTool, TimeTool
from src.tools.reception import VisitorRegistrationTool

tools = [
    CalculatorTool(),
    TimeTool(),
    VisitorRegistrationTool(),
    # ...
]
```

---

## 常见问题

### Q1: 旧代码还能用吗?

**A:** 可以! 工具加载器 (`src/tools/loader.py`) 会从旧的 `tools.py` 导入所有工具,保持100%向后兼容。

### Q2: 需要修改 .env 文件吗?

**A:** 不需要。新配置系统完全兼容旧的环境变量。

### Q3: 如何混合使用新旧代码?

**A:** 可以! 示例:

```python
# 使用新的 Agent
from src.core import HybridReasoningAgent

# 使用旧的工具
from src.tools import load_all_tools

tools = load_all_tools()
agent = HybridReasoningAgent(tools=tools)
```

### Q4: 性能有影响吗?

**A:** 没有。新架构只是重新组织了代码,核心逻辑完全一致。

### Q5: 如何迁移自定义工具?

**A:** 两种方式:

方式1: 继续放在 `tools.py` (简单)
```python
# tools.py 中添加你的工具
class CustomTool(BaseTool):
    ...
```

方式2: 迁移到新结构 (推荐)
```python
# src/tools/custom/my_tool.py
from src.core.tools import BaseTool

class CustomTool(BaseTool):
    ...
```

---

## 运行示例

### 旧演示

```bash
python demo_hybrid.py
```

### 新演示

```bash
# 使用新架构
python examples/demo_new_architecture.py

# 旧演示仍可运行
python demo_hybrid.py
```

---

## 检查清单

迁移到新架构时,请检查:

- [ ] 更新导入语句
- [ ] 修改返回值访问(字典 → 属性)
- [ ] 测试所有功能
- [ ] 更新文档
- [ ] 更新测试用例

---

## 获取帮助

- 📖 查看 [架构文档](./architecture.md)
- 💡 参考 [示例代码](../examples/)
- 🐛 提交 [Issue](https://github.com/your-repo/issues)

---

## 推荐迁移路径

```
当前 (旧架构)
    ↓
第1步: 使用新 Agent + 工具加载器
    ↓
第2步: 逐步迁移工具到新结构
    ↓
第3步: 使用新配置系统
    ↓
第4步: 迁移测试和文档
    ↓
完成! (新架构)
```

祝迁移顺利! 🚀
