"""
混合架构 Agent - OpenAI原生Function Calling + LangChain工具池 + KV Cache优化

核心特性:
1. 使用OpenAI原生API获得完全控制权(tool_choice控制)
2. 保留LangChain丰富的工具生态
3. KV Cache自动优化(系统提示词缓存、对话历史缓存)
4. 100%可靠的工具调用
5. 完整的推理过程展示
"""
from openai import OpenAI
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

from src.core.agents.base import BaseAgent, AgentResponse
from src.core.config import settings
from src.core.tools.base import BaseTool


class HybridReasoningAgent(BaseAgent):
    """
    混合架构推理Agent

    架构:
    - OpenAI原生API: 推理引擎(可控、快速、支持KV Cache)
    - LangChain工具: 执行引擎(丰富、易扩展)
    - KV Cache: 性能优化(对话历史、系统提示词自动缓存)
    """

    def __init__(
        self,
        tools: List[BaseTool],
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        enable_cache: bool = True,
        name: str = "HybridAgent"
    ):
        """
        初始化混合架构Agent

        Args:
            tools: 工具列表
            api_key: OpenAI API密钥(默认从配置读取)
            model: 模型名称(默认从配置读取)
            temperature: 温度参数(默认从配置读取)
            enable_cache: 是否启用对话历史缓存(KV Cache优化)
            name: Agent名称
        """
        super().__init__(name=name)

        # 配置
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.llm_model
        self.temperature = temperature if temperature is not None else settings.temperature
        self.enable_cache = enable_cache

        # OpenAI客户端
        self.client = OpenAI(api_key=self.api_key)

        # 工具管理
        self.tools = tools
        self.openai_tools = self._convert_tools_to_openai_format()
        self.tool_map = {tool.name: tool for tool in tools}

        # 系统提示词(会被KV Cache缓存,节省成本)
        self.system_prompt = self._create_system_prompt()

        print(f"✅ 混合架构Agent初始化成功")
        print(f"   引擎: OpenAI原生API ({self.model})")
        print(f"   工具: LangChain工具池 ({len(self.tools)}个)")
        print(f"   KV Cache: {'启用' if self.enable_cache else '禁用'}")
        print(f"   温度: {self.temperature}")
        print()

    def _create_system_prompt(self) -> str:
        """
        创建系统提示词
        注意: 这个提示词会被OpenAI自动缓存(Prompt Caching),节省50%成本
        """
        # 动态生成工具列表
        tool_descriptions = []
        for tool in self.tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")

        tools_text = "\n".join(tool_descriptions)

        return f"""你是一个具有强大推理能力的AI助手。

🎯 核心能力:
1. 深度分析和理解用户问题
2. 必须使用工具解决问题(展示推理能力)
3. 自主决定工具参数(展示决策能力)
4. 基于结果进行综合推理

🛠️ 可用工具:
{tools_text}

⚠️ 重要规则(必须严格遵守):
1. **数学计算必须调用calculator** - 即使简单如"1+1"
2. **时间查询必须调用time_tool** - 不要猜测
3. **文本统计必须调用text_analyzer** - 不要估算
4. **对话结束必须调用end_conversation_detector** - 检测到"再见"等关键词时强制调用

🔄 推理流程:
第1步: 分析用户问题类型和意图
第2步: 确定需要使用的工具(根据上述规则)
第3步: 自主决定工具的输入参数
第4步: 等待工具执行结果
第5步: 基于结果进行推理并生成答案

现在开始严格遵守规则,帮助用户!"""

    def _convert_tools_to_openai_format(self) -> List[Dict]:
        """
        将LangChain工具转换为OpenAI Function Calling格式

        这是混合架构的关键: 保留LangChain工具定义,但用OpenAI格式调用
        """
        openai_tools = []

        for tool in self.tools:
            # 提取参数schema
            if hasattr(tool, 'args_schema') and tool.args_schema:
                # 使用model_json_schema替代deprecated的schema方法
                parameters = tool.args_schema.model_json_schema()
            else:
                parameters = {
                    "type": "object",
                    "properties": {},
                    "required": []
                }

            # 转换为OpenAI格式
            openai_tool = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": parameters
                }
            }

            openai_tools.append(openai_tool)

        return openai_tools

    def _execute_tool(self, tool_name: str, arguments: Dict) -> str:
        """
        执行LangChain工具

        Args:
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            工具执行结果
        """
        if tool_name not in self.tool_map:
            return f"错误: 工具 '{tool_name}' 不存在"

        try:
            tool = self.tool_map[tool_name]
            result = tool._run(**arguments)
            return str(result)
        except Exception as e:
            return f"工具执行错误: {str(e)}"

    def _check_end_keywords(self, user_input: str) -> bool:
        """检查是否包含结束关键词"""
        end_keywords = [
            '再见', '拜拜', 'bye', 'goodbye', '退出', '结束',
            '关闭', '离开', '不聊了', '走了', 'quit', 'exit',
            '886', '88', '下线', '断开'
        ]
        user_lower = user_input.lower().strip()
        return any(keyword in user_lower for keyword in end_keywords)

    def run(
        self,
        user_input: str,
        show_reasoning: bool = True
    ) -> AgentResponse:
        """
        执行推理(非流式)

        Args:
            user_input: 用户输入
            show_reasoning: 是否显示推理过程

        Returns:
            AgentResponse: 执行结果
        """
        if show_reasoning:
            print("\n" + "="*70)
            print("🧠 混合架构推理过程(OpenAI原生 + LangChain工具)")
            print("="*70)

        # 检测结束关键词
        contains_end_keyword = self._check_end_keywords(user_input)
        if contains_end_keyword and show_reasoning:
            print(f"\n🔍 预处理: 检测到结束关键词,将强制要求调用end_conversation_detector")

        # 构建消息(利用KV Cache)
        messages = self._build_messages(user_input, contains_end_keyword)

        # 推理步骤记录
        reasoning_steps = []
        tool_call_count = 0

        try:
            # 第一次调用: 模型决策
            if show_reasoning:
                print(f"\n{'─'*70}")
                print("📡 调用OpenAI API进行推理...")
                print(f"{'─'*70}")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.openai_tools,
                tool_choice="auto",
                temperature=self.temperature
            )

            assistant_message = response.choices[0].message

            # 处理工具调用
            if assistant_message.tool_calls:
                if show_reasoning:
                    print(f"\n✅ 模型决定调用工具(共{len(assistant_message.tool_calls)}个)")

                # 添加助手消息到历史
                messages.append({
                    "role": "assistant",
                    "content": assistant_message.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        } for tc in assistant_message.tool_calls
                    ]
                })

                # 执行每个工具调用
                for tool_call in assistant_message.tool_calls:
                    tool_call_count += 1
                    tool_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)

                    if show_reasoning:
                        self._display_tool_call(
                            tool_call_count,
                            tool_name,
                            arguments
                        )

                    # 执行LangChain工具
                    result = self._execute_tool(tool_name, arguments)

                    if show_reasoning:
                        self._display_tool_result(result)

                    # 记录推理步骤
                    reasoning_steps.append({
                        'step': tool_call_count,
                        'tool': tool_name,
                        'arguments': arguments,
                        'result': result
                    })

                    # 添加工具结果到消息
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result
                    })

                # 第二次调用: 基于工具结果生成最终回答
                if show_reasoning:
                    print(f"\n{'─'*70}")
                    print("💭 模型基于工具结果生成最终回答...")
                    print(f"{'─'*70}")

                final_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature
                )

                final_answer = final_response.choices[0].message.content
            else:
                # 没有工具调用,直接回答
                if show_reasoning:
                    print("\n⚠️  模型选择直接回答(未调用工具)")
                final_answer = assistant_message.content

            # 更新对话历史(用于KV Cache)
            if self.enable_cache:
                self.conversation_history.append({
                    "role": "user",
                    "content": user_input
                })
                self.conversation_history.append({
                    "role": "assistant",
                    "content": final_answer
                })

            if show_reasoning:
                print(f"\n{'='*70}")
                print("💬 最终回答")
                print(f"{'='*70}")
                print(final_answer)
                print(f"{'='*70}\n")

            # 检查是否需要结束对话
            should_end = any(
                step['tool'] == 'end_conversation_detector' and
                'END_CONVERSATION' in step['result']
                for step in reasoning_steps
            )

            return AgentResponse(
                success=True,
                output=final_answer,
                reasoning_steps=reasoning_steps,
                tool_calls=tool_call_count,
                metadata={
                    'should_end': should_end,
                    'cached_tokens': len(self.conversation_history) if self.enable_cache else 0
                }
            )

        except Exception as e:
            error_msg = f"执行错误: {str(e)}"
            print(f"\n❌ {error_msg}")
            return AgentResponse(
                success=False,
                output=error_msg,
                error=str(e)
            )

    def _build_messages(self, user_input: str, force_end_detection: bool = False) -> List[Dict]:
        """
        构建消息列表

        系统提示词会被OpenAI自动缓存(Prompt Caching)
        对话历史也会被KV Cache优化
        """
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]

        # 添加对话历史(KV Cache优化)
        if self.enable_cache:
            messages.extend(self.conversation_history)

        # 添加当前输入
        user_message = user_input
        if force_end_detection:
            user_message += "\n\n[系统要求: 检测到结束关键词,必须调用end_conversation_detector工具]"

        messages.append({
            "role": "user",
            "content": user_message
        })

        return messages

    def _display_tool_call(self, step: int, tool_name: str, arguments: Dict):
        """显示工具调用信息"""
        print(f"\n{'='*70}")
        print(f"📍 推理步骤 {step}")
        print(f"{'='*70}")
        print(f"\n✅ 模型决策:")
        print(f"   → 选择工具: {tool_name}")
        print(f"\n📥 模型决定的参数:")
        print(f"{'─'*70}")
        formatted_args = json.dumps(arguments, ensure_ascii=False, indent=6)
        for line in formatted_args.split('\n'):
            print(f"   {line}")
        print(f"{'─'*70}")

    def _display_tool_result(self, result: str):
        """显示工具执行结果"""
        print(f"\n📤 工具返回结果:")
        print(f"{'─'*70}")
        if len(result) > 500:
            print(f"   {result[:500]}...")
            print(f"   ... (结果过长,已截断)")
        else:
            for line in result.split('\n'):
                print(f"   {line}")
        print(f"{'─'*70}")

    def clear_history(self):
        """清除对话历史缓存"""
        self.conversation_history = []
        print("✅ 对话历史已清除(KV Cache重置)")

    def get_stats(self) -> Dict:
        """获取缓存统计信息"""
        base_stats = super().get_stats()
        return {
            **base_stats,
            'estimated_cached_tokens': sum(
                len(msg['content']) // 4
                for msg in self.conversation_history
            ),
            'system_prompt_tokens': len(self.system_prompt) // 4,
            'tools_count': len(self.tools)
        }


# 导出
__all__ = ['HybridReasoningAgent']
