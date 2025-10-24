"""
Agent核心模块 - 实现具有推理能力和自主函数调用的LLM架构

核心特性：
1. 使用OpenAI的Function Calling能力
2. 基于ReAct模式（Reasoning + Acting）
3. LLM自主决策何时调用工具
4. 解耦设计：LLM负责推理，工具负责执行
"""
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from typing import List, Dict, Any, Generator
from tools import (
    CalculatorTool,
    TimeTool,
    TextAnalysisTool,
    UnitConversionTool,
    ComparisonTool,
    LogicReasoningTool,
    LibraryManagementTool,
    ConversationEndDetector,
    WebSearchTool,
    FileOperationTool,
    ReminderTool
)
import config
import re


class ReasoningAgent:
    """
    推理Agent - 具有自主工具调用能力的LLM
    
    架构说明：
    - LLM: 作为"大脑"，负责理解问题、推理、决策
    - Tools: 作为"工具箱"，提供具体执行能力
    - Agent: 编排LLM和Tools，实现自主决策
    
    工作流程：
    1. 接收用户输入
    2. LLM分析问题，决定是否需要工具
    3. 如果需要，调用相应工具并获取结果
    4. LLM基于工具结果进行推理
    5. 生成最终答案
    """
    
    def __init__(
        self,
        api_key: str = None,
        model: str = None,
        temperature: float = None,
        verbose: bool = True
    ):
        """
        初始化Agent
        
        Args:
            api_key: OpenAI API密钥
            model: 使用的模型名称
            temperature: 温度参数（0-1），越低越确定
            verbose: 是否打印详细推理过程
        """
        # 使用配置或传入参数
        self.api_key = api_key or config.OPENAI_API_KEY
        self.model = model or config.LLM_MODEL
        self.temperature = temperature if temperature is not None else config.TEMPERATURE
        self.verbose = verbose
        
        # 初始化LLM（推理核心）
        self.llm = ChatOpenAI(
            model=self.model,
            api_key=self.api_key,
            temperature=self.temperature,
        )
        
        # 初始化工具列表（可扩展的工具箱）
        self.tools = self._init_tools()
        
        # 创建Agent
        self.agent = self._create_agent()
        
        # 创建Agent执行器
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=self.verbose,
            handle_parsing_errors=True,
            max_iterations=10,  # 最大推理步骤
            early_stopping_method="generate",  # 提前停止策略
        )
        
        if self.verbose:
            print(f"✅ Agent初始化成功")
            print(f"   模型: {self.model}")
            print(f"   温度: {self.temperature}")
            print(f"   可用工具: {[tool.name for tool in self.tools]}")
            print()
    
    def _init_tools(self) -> List:
        """
        初始化工具列表
        
        解耦设计：工具是独立的模块，可以轻松添加新工具
        
        Returns:
            工具列表
        """
        return [
            CalculatorTool(),              # 数学计算
            TimeTool(),                    # 时间日期
            TextAnalysisTool(),            # 文本分析
            UnitConversionTool(),          # 单位转换
            ComparisonTool(),              # 数据比较
            LogicReasoningTool(),          # 逻辑推理
            LibraryManagementTool(),       # 图书馆管理系统
            ConversationEndDetector(),     # 对话结束检测
            WebSearchTool(),               # 网络搜索（模型自主决定搜索词）
            FileOperationTool(),           # 文件操作（模型自主决定操作和参数）
            ReminderTool(),                # 提醒设置（模型自主提取任务和时间）
            # 未来可以轻松添加更多工具：
            # ImageAnalyzerTool(),
            # DatabaseQueryTool(),
        ]
    
    def _create_agent(self):
        """
        创建OpenAI Tools Agent
        
        使用ReAct模式：
        - Reasoning: LLM分析问题，思考解决方案
        - Acting: LLM决定调用哪个工具
        - Observing: LLM观察工具执行结果
        - 重复上述过程直到得到最终答案
        """
        
        # 定义Agent的系统提示词
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个具有强大推理能力的AI助手。

核心能力：
1. 理解和分析用户的问题
2. **必须使用工具解决问题**（不要直接回答）
3. 选择合适的工具并自主决定参数
4. 基于工具结果进行推理和总结

可用工具：
- calculator: 数学计算工具，支持各种数学运算和函数
- time_tool: 时间日期工具，获取当前时间、日期、星期等
- text_analyzer: 文本分析工具，统计字数、字符数、句子数
- unit_converter: 单位转换工具，支持长度、温度等单位转换
- data_comparison: 数据比较工具，比较数值大小、排序等
- logic_reasoning: 逻辑推理辅助工具，结构化分析逻辑问题
- library_system: 图书馆管理系统，查询图书信息、借阅状态
- end_conversation_detector: 对话结束检测，识别用户是否想结束对话

**重要规则（必须遵守）**：
1. **数学计算必须使用calculator工具** - 即使是简单计算也要调用工具
2. **时间查询必须使用time_tool工具** - 不要猜测时间
3. **文本统计必须使用text_analyzer工具** - 不要直接数
4. **单位转换必须使用unit_converter工具** - 不要直接计算
5. **图书查询必须使用library_system工具** - 不要编造
6. **检测到结束关键词（再见、bye、退出等）必须调用end_conversation_detector** - 这是强制性的

工作流程（一步步思考）：
第1步：分析用户问题的类型
第2步：判断需要使用哪个工具（参考上面的规则）
第3步：决定工具的输入参数（根据用户问题提取关键信息）
第4步：调用工具并等待结果
第5步：基于工具结果生成回答

示例思考过程：
【例1】用户："计算sqrt(2)保留3位小数"
→ 第1步：数学计算问题
→ 第2步：必须使用calculator工具
→ 第3步：参数应该是 "round(sqrt(2), 3)"
→ 第4步：调用calculator工具
→ 第5步：根据结果回答

【例2】用户："再见"
→ 第1步：包含结束关键词
→ 第2步：必须调用end_conversation_detector
→ 第3步：参数是用户原话 "再见"
→ 第4步：调用检测工具
→ 第5步：生成告别语

【例3】用户："现在几点"
→ 第1步：时间查询
→ 第2步：必须使用time_tool
→ 第3步：参数是查询类型
→ 第4步：调用时间工具
→ 第5步：告诉用户时间

现在，让我们严格遵守这些规则，开始帮助用户！"""),
            
            # 对话历史（如果有）
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            
            # 用户输入
            ("human", "{input}"),
            
            # Agent的推理过程记录
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # 创建OpenAI Tools Agent
        return create_openai_tools_agent(self.llm, self.tools, prompt)
    
    def run(self, user_input: str) -> Dict[str, Any]:
        """
        同步执行Agent推理
        
        Args:
            user_input: 用户输入的问题或任务
            
        Returns:
            包含结果的字典：
            {
                'success': bool,
                'output': str,  # 最终答案
                'intermediate_steps': list,  # 推理步骤
            }
        """
        try:
            if self.verbose:
                print("=" * 60)
                print(f"🤔 用户输入: {user_input}")
                print("=" * 60)
                print()
            
            # 执行Agent推理和工具调用
            result = self.agent_executor.invoke({
                "input": user_input
            })
            
            if self.verbose:
                print()
                print("=" * 60)
                print(f"✅ 最终答案: {result['output']}")
                print("=" * 60)
                print()
            
            return {
                'success': True,
                'output': result['output'],
                'intermediate_steps': result.get('intermediate_steps', []),
            }
            
        except Exception as e:
            error_msg = f"执行出错: {str(e)}"
            if self.verbose:
                print(f"\n❌ {error_msg}\n")
            
            return {
                'success': False,
                'output': error_msg,
                'error': str(e),
            }
    
    async def arun(self, user_input: str) -> Dict[str, Any]:
        """
        异步执行Agent推理
        
        Args:
            user_input: 用户输入的问题或任务
            
        Returns:
            包含结果的字典
        """
        try:
            if self.verbose:
                print("=" * 60)
                print(f"🤔 用户输入: {user_input}")
                print("=" * 60)
                print()
            
            # 异步执行
            result = await self.agent_executor.ainvoke({
                "input": user_input
            })
            
            if self.verbose:
                print()
                print("=" * 60)
                print(f"✅ 最终答案: {result['output']}")
                print("=" * 60)
                print()
            
            return {
                'success': True,
                'output': result['output'],
                'intermediate_steps': result.get('intermediate_steps', []),
            }
            
        except Exception as e:
            error_msg = f"执行出错: {str(e)}"
            if self.verbose:
                print(f"\n❌ {error_msg}\n")
            
            return {
                'success': False,
                'output': error_msg,
                'error': str(e),
            }
    
    def add_tool(self, tool):
        """
        动态添加新工具（体现解耦设计的灵活性）
        
        Args:
            tool: 新的工具实例
        """
        self.tools.append(tool)
        # 重新创建agent以包含新工具
        self.agent = self._create_agent()
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=self.verbose,
        )
        if self.verbose:
            print(f"✅ 已添加新工具: {tool.name}")
    
    def _split_by_punctuation(self, text: str) -> list:
        """
        按照中英文标点符号分割文本
        用于TTS友好的输出
        
        Args:
            text: 要分割的文本
            
        Returns:
            分割后的句子列表
        """
        # 匹配中英文句子结束符号
        pattern = r'([^。！？.!?]+[。！？.!?]+)'
        sentences = re.findall(pattern, text)
        
        # 如果没有标点符号，尝试按逗号和分号分割
        if not sentences:
            pattern = r'([^，,;；]+[，,;；]+)'
            sentences = re.findall(pattern, text)
        
        # 还是没有的话，就返回整段文本
        if not sentences:
            sentences = [text]
        
        return [s.strip() for s in sentences if s.strip()]
    
    def _check_end_keywords(self, user_input: str) -> bool:
        """检查是否包含结束关键词"""
        end_keywords = [
            '再见', '拜拜', 'bye', 'goodbye', '退出', '结束',
            '关闭', '离开', '不聊了', '走了', 'quit', 'exit',
            '886', '88', '下线', '断开'
        ]
        user_lower = user_input.lower().strip()
        return any(keyword in user_lower for keyword in end_keywords)
    
    def run_with_sentence_stream(self, user_input: str, show_reasoning: bool = True) -> Dict[str, Any]:
        """
        执行推理并返回按句子分割的结果（为TTS准备）
        
        Args:
            user_input: 用户输入
            show_reasoning: 是否显示推理过程
            
        Returns:
            包含分句输出和推理步骤的字典
        """
        try:
            # 收集推理步骤
            reasoning_steps = []
            
            # 显示推理过程开始
            if show_reasoning:
                print("\n" + "="*70)
                print("🧠 推理过程展示")
                print("="*70)
            
            # 【重要】检查是否包含结束关键词，如果有，强制添加提示
            contains_end_keyword = self._check_end_keywords(user_input)
            if contains_end_keyword and show_reasoning:
                print(f"\n🔍 预处理检测: 发现结束关键词，将强制要求模型调用end_conversation_detector")
                print("="*70)
            
            # 执行Agent推理
            # 如果包含结束关键词，在输入中添加强制指令
            actual_input = user_input
            if contains_end_keyword:
                actual_input = f"{user_input}\n\n[系统指令：用户消息包含结束关键词，你必须调用end_conversation_detector工具进行检测！]"
            
            result = self.agent_executor.invoke({"input": actual_input})
            
            # 提取推理步骤
            intermediate_steps = result.get('intermediate_steps', [])
            
            for i, (action, observation) in enumerate(intermediate_steps, 1):
                step_info = {
                    'step': i,
                    'tool': action.tool,
                    'tool_input': action.tool_input,
                    'output': observation,
                    'thought': getattr(action, 'log', '')  # LLM的思考过程
                }
                reasoning_steps.append(step_info)
                
                if show_reasoning:
                    print(f"\n{'='*70}")
                    print(f"📍 推理步骤 {i}")
                    print(f"{'='*70}")
                    
                    # 显示LLM的完整思考过程
                    if hasattr(action, 'log') and action.log:
                        print(f"\n💭 模型思考过程:")
                        print(f"{'─'*70}")
                        # 完整显示log内容
                        log_content = action.log.strip()
                        # 尝试提取结构化信息
                        if 'Action:' in log_content or 'Thought:' in log_content:
                            # 如果有结构化内容，按行显示
                            for line in log_content.split('\n'):
                                if line.strip():
                                    print(f"   {line.strip()}")
                        else:
                            # 否则显示前10行
                            lines = log_content.split('\n')
                            for line in lines[:10]:
                                if line.strip():
                                    print(f"   {line.strip()}")
                            if len(lines) > 10:
                                print(f"   ... (省略{len(lines)-10}行)")
                        print(f"{'─'*70}")
                    
                    print(f"\n✅ 模型决策:")
                    print(f"   → 选择工具: {action.tool}")
                    print(f"   → 原因: 分析用户需求后，确定需要使用此工具")
                    
                    print(f"\n📥 模型决定的Function Call参数:")
                    print(f"{'─'*70}")
                    import json
                    try:
                        # 显示工具名称
                        print(f"   工具名: {action.tool}")
                        print(f"   参数:")
                        formatted_input = json.dumps(action.tool_input, ensure_ascii=False, indent=6)
                        for line in formatted_input.split('\n'):
                            print(f"   {line}")
                    except:
                        print(f"   {action.tool_input}")
                    print(f"{'─'*70}")
                    
                    print(f"\n📤 Function Call 返回结果:")
                    print(f"{'─'*70}")
                    # 格式化输出
                    output_str = str(observation)
                    if len(output_str) > 500:
                        # 如果是JSON，尝试格式化
                        try:
                            import json
                            json_obj = json.loads(output_str)
                            formatted = json.dumps(json_obj, ensure_ascii=False, indent=6)
                            print(f"   {formatted[:500]}...")
                            print(f"   ... (结果过长，已截断)")
                        except:
                            print(f"   {output_str[:500]}...")
                            print(f"   ... (结果过长，已截断)")
                    else:
                        # 尝试JSON格式化
                        try:
                            import json
                            json_obj = json.loads(output_str)
                            formatted = json.dumps(json_obj, ensure_ascii=False, indent=6)
                            for line in formatted.split('\n'):
                                print(f"   {line}")
                        except:
                            for line in output_str.split('\n'):
                                print(f"   {line}")
                    print(f"{'─'*70}")
                    
                    print(f"\n✨ 模型基于此结果继续思考...")
            
            # 获取最终输出
            final_output = result['output']
            
            # 按句子分割输出
            sentences = self._split_by_punctuation(final_output)
            
            if show_reasoning:
                print("\n" + "="*70)
                print("💬 生成回答（句子分割 - TTS友好）")
                print("="*70)
                for i, sentence in enumerate(sentences, 1):
                    print(f"{i}. {sentence}")
                print("="*70 + "\n")
            
            return {
                'success': True,
                'output': final_output,
                'sentences': sentences,  # 分句列表，可直接用于TTS
                'reasoning_steps': reasoning_steps,  # 推理步骤详情
                'step_count': len(reasoning_steps)
            }
            
        except Exception as e:
            return {
                'success': False,
                'output': str(e),
                'sentences': [str(e)],
                'reasoning_steps': [],
                'step_count': 0,
                'error': str(e)
            }
    
    def stream_output_for_tts(self, user_input: str) -> Generator[Dict, None, None]:
        """
        生成器版本 - 逐句yield输出，适合实时TTS
        
        Args:
            user_input: 用户输入
            
        Yields:
            每次yield一个字典，包含类型和内容
        """
        result = self.run_with_sentence_stream(user_input, show_reasoning=False)
        
        # 先yield推理步骤信息
        yield {
            'type': 'reasoning',
            'steps': result['reasoning_steps'],
            'step_count': result['step_count']
        }
        
        # 逐句yield输出内容
        for i, sentence in enumerate(result['sentences'], 1):
            yield {
                'type': 'sentence',
                'index': i,
                'content': sentence,
                'is_last': i == len(result['sentences'])
            }


# 演示代码
if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🤖 推理Agent演示 - 具有自主函数调用能力的LLM")
    print("=" * 70)
    print()
    
    # 创建Agent实例
    agent = ReasoningAgent(verbose=True)
    
    # 测试案例1: 计算sqrt(2)保留3位小数
    print("\n【测试案例1】计算sqrt(2)保留3位小数")
    result1 = agent.run("计算sqrt(2)保留3位小数")
    
    # 测试案例2: 复杂数学运算
    print("\n【测试案例2】复杂运算")
    result2 = agent.run("计算(3+5)*2-1等于多少？")
    
    # 测试案例3: 普通对话（测试Agent是否能正确判断不需要工具）
    print("\n【测试案例3】普通对话")
    result3 = agent.run("你好，介绍一下你自己")
    
    print("\n" + "=" * 70)
    print("演示完成！")
    print("=" * 70)

