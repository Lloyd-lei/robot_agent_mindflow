# 架构设计文档

## 概述

本项目采用 **分层架构 + 领域驱动设计(DDD)** 的思想,实现了一个清晰、可维护、易扩展的AI Agent框架。

## 核心设计原则

### 1. 分层架构

```
┌─────────────────────────────────────┐
│        Examples / Applications      │  ← 应用层
├─────────────────────────────────────┤
│           Tools Layer               │  ← 工具层
├─────────────────────────────────────┤
│         Services Layer              │  ← 服务层
├─────────────────────────────────────┤
│           Core Layer                │  ← 核心层
└─────────────────────────────────────┘
```

### 2. 依赖倒置原则

- **核心层**定义接口,其他层实现接口
- 高层模块不依赖低层模块,都依赖抽象

### 3. 单一职责原则

每个模块只负责一个职责:
- `Agent` - 推理和决策
- `TTS Service` - 语音合成
- `Tool` - 工具执行

### 4. 开闭原则

对扩展开放,对修改关闭:
- 新增工具: 继承 `BaseTool`
- 新增 Agent: 继承 `BaseAgent`
- 新增 TTS: 实现 `BaseTTS`

---

## 目录结构

```
robot_agent_mindflow/
├── src/                              # 源代码
│   ├── core/                         # 核心层
│   │   ├── agents/                   # Agent 引擎
│   │   │   ├── base.py              # Agent 抽象基类
│   │   │   └── hybrid_agent.py      # 混合架构 Agent
│   │   ├── llm/                      # LLM 接口层(待实现)
│   │   ├── tools/                    # 工具基础设施
│   │   │   ├── base.py              # 工具基类
│   │   │   └── registry.py          # 工具注册表
│   │   └── config/                   # 配置管理
│   │       └── settings.py          # 配置类
│   ├── services/                     # 服务层
│   │   ├── tts/                      # TTS 服务
│   │   ├── voice/                    # 语音反馈
│   │   └── reception/                # 前台接待业务(示例)
│   ├── tools/                        # 工具层
│   │   ├── basic/                    # 基础工具
│   │   ├── reception/                # 前台接待工具
│   │   ├── system/                   # 系统工具
│   │   └── loader.py                 # 工具加载器
│   └── utils/                        # 工具类
├── tests/                            # 测试
├── examples/                         # 示例
├── docs/                             # 文档
└── config/                           # 配置文件
```

---

## 核心模块说明

### Core 层

#### 1. Agents (`src/core/agents/`)

**BaseAgent** - Agent 抽象基类

```python
from src.core import BaseAgent, AgentResponse

class MyAgent(BaseAgent):
    def run(self, user_input: str) -> AgentResponse:
        # 实现推理逻辑
        pass
```

**HybridReasoningAgent** - 混合架构 Agent

- 使用 OpenAI 原生 API
- 支持 LangChain 工具
- KV Cache 优化

#### 2. Tools (`src/core/tools/`)

**BaseTool** - 工具抽象基类

```python
from src.core.tools import BaseTool

class MyTool(BaseTool):
    name = "my_tool"
    description = "我的工具"
    category = "basic"

    def execute(self, **kwargs):
        # 实现工具逻辑
        return "result"
```

**ToolRegistry** - 工具注册表

```python
from src.core.tools import tool_registry

# 注册工具
tool_registry.register(MyTool())

# 获取工具
tool = tool_registry.get('my_tool')
```

#### 3. Config (`src/core/config/`)

**Settings** - 配置管理

```python
from src.core.config import settings

api_key = settings.openai_api_key
model = settings.llm_model
```

配置优先级: 环境变量 > .env 文件 > 默认值

---

### Services 层

#### TTS 服务 (`src/services/tts/`)

- **TTS Interface**: 统一的 TTS 接口(Edge/Azure/OpenAI)
- **Text Optimizer**: 文本优化和分句
- **Audio Manager**: 音频播放管理

```python
from src.services.tts import TTSFactory, TTSProvider, TTSOptimizer

# 创建 TTS
tts = TTSFactory.create_tts(
    provider=TTSProvider.EDGE,
    voice="zh-CN-XiaoxiaoNeural"
)

# 使用优化器
optimizer = TTSOptimizer(tts_engine=tts)
optimizer.optimize_and_play("你好")
```

#### Voice 服务 (`src/services/voice/`)

语音等待反馈

```python
from src.services.voice import VoiceWaitingFeedback

feedback = VoiceWaitingFeedback(mode='text')
feedback.start('thinking')
# ... 执行任务 ...
feedback.stop()
```

---

### Tools 层

#### 基础工具 (`src/tools/basic/`)

- CalculatorTool - 数学计算
- TimeTool - 时间查询
- TextAnalysisTool - 文本分析
- UnitConversionTool - 单位转换
- ...

#### 前台接待工具 (`src/tools/reception/`)

- VisitorRegistrationTool - 访客登记
- MeetingRoomTool - 会议室管理
- EmployeeDirectoryTool - 员工通讯录
- ...

#### 系统工具 (`src/tools/system/`)

- ConversationEndDetector - 对话结束检测
- WebSearchTool - 网络搜索
- ...

---

## 使用示例

### 基础使用

```python
from src.core import HybridReasoningAgent
from src.tools import load_all_tools

# 加载工具
tools = load_all_tools()

# 创建 Agent
agent = HybridReasoningAgent(tools=tools)

# 执行推理
result = agent.run("计算sqrt(2)")

print(result.output)  # 最终回答
print(result.tool_calls)  # 工具调用次数
```

### 带 TTS 的使用

```python
from src.core import HybridReasoningAgent
from src.services.tts import TTSFactory, TTSProvider
from src.tools import load_all_tools

# 创建 TTS
tts = TTSFactory.create_tts(TTSProvider.EDGE)

# 创建 Agent (带 TTS)
tools = load_all_tools()
agent = HybridReasoningAgent(tools=tools)

# 执行
result = agent.run("现在几点?")

# 播放 TTS
from src.services.tts import TTSOptimizer
optimizer = TTSOptimizer(tts_engine=tts)
optimizer.optimize_and_play(result.output)
```

---

## 扩展指南

### 添加新工具

1. 创建工具类:

```python
# src/tools/basic/my_tool.py
from src.core.tools import BaseTool
from pydantic import BaseModel, Field

class MyToolInput(BaseModel):
    arg: str = Field(description="参数说明")

class MyTool(BaseTool):
    name = "my_tool"
    description = "我的工具"
    args_schema = MyToolInput
    category = "basic"

    def execute(self, arg: str):
        return f"处理: {arg}"
```

2. 注册工具:

```python
from src.core.tools import tool_registry
from src.tools.basic.my_tool import MyTool

tool_registry.register(MyTool())
```

### 添加新 Agent

```python
# src/core/agents/my_agent.py
from src.core.agents import BaseAgent, AgentResponse

class MyAgent(BaseAgent):
    def run(self, user_input: str) -> AgentResponse:
        # 实现自定义推理逻辑
        result = custom_reasoning(user_input)

        return AgentResponse(
            success=True,
            output=result
        )
```

---

## 配置说明

### 环境变量 (.env)

```bash
# OpenAI 配置
OPENAI_API_KEY=your-key-here
LLM_MODEL=gpt-4-turbo-preview
TEMPERATURE=0.0

# Agent 配置
ENABLE_CACHE=true
MAX_RETRIES=3
TIMEOUT=30

# TTS 配置
ENABLE_TTS=false
TTS_PROVIDER=edge
TTS_VOICE=zh-CN-XiaoxiaoNeural
TTS_RATE=+0%
TTS_VOLUME=+0%

# 日志配置
LOG_LEVEL=INFO
DEBUG=false

# 环境
ENVIRONMENT=development
```

---

## 性能优化

### KV Cache 优化

混合架构 Agent 自动利用 OpenAI 的 KV Cache:

1. **系统提示词缓存** - 节省 50% 成本
2. **对话历史缓存** - 多轮对话速度提升 3-5 倍

```python
# 启用缓存
agent = HybridReasoningAgent(
    tools=tools,
    enable_cache=True  # 默认启用
)

# 查看缓存统计
stats = agent.get_stats()
print(stats['estimated_cached_tokens'])
```

---

## 测试

```bash
# 运行单元测试
python -m pytest tests/unit

# 运行集成测试
python -m pytest tests/integration

# 运行示例
python examples/demo_new_architecture.py
```

---

## 未来改进

1. **完整的工具拆分**: 将所有工具从 tools.py 拆分到独立文件
2. **LLM 抽象层**: 支持多种 LLM (OpenAI/Azure/Claude)
3. **插件系统**: 动态加载工具插件
4. **异步支持**: 异步 Agent 和工具执行
5. **可观测性**: 日志、追踪、监控

---

## 贡献指南

欢迎贡献! 请遵循以下原则:

1. 遵守现有的架构设计
2. 每个 PR 只解决一个问题
3. 添加单元测试
4. 更新相关文档

---

## 许可证

MIT License
