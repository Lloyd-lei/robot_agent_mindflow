# Waste / 归档目录

本目录存放已被替代或不再使用的旧版本文件。

## 目录结构

- `old_demos/` - 旧的演示程序
- `old_tests/` - 旧的测试程序
- `old_docs/` - 旧的文档
- `agent.py` - 旧版纯 LangChain Agent（保留作为性能对比基准）

## 说明

这些文件已被混合架构版本替代，但保留用于：

1. 历史记录
2. 性能对比
3. 参考旧功能实现

## 当前主要文件

请参考项目根目录的以下文件：

**核心系统：**

- `agent_hybrid.py` - 混合架构 Agent（主力）
- `tools.py` - 17 个工具
- `tts_optimizer.py` - TTS 优化系统
- `voice_feedback.py` - 语音反馈

**主程序：**

- `demo_hybrid.py` - 通用主程序 ⭐
- `demo_reception.py` - 前台接待演示
- `demo_tts_showcase.py` - TTS 演示

**测试：**

- `test_hybrid_vs_langchain.py` - 性能对比测试
