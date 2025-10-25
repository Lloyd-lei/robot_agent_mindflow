"""
Agent - OpenAI原生Function Calling + LangChain工具池 + KV Cache优化

没用openai的时候，可以切换到ollama，ollama没有tool_choice，但能用longchain

核心特性：
1. 使用OpenAI原生API获得完全控制权（tool_choice控制）
2. 保留LangChain丰富的工具生态
3. KV Cache自动优化（系统提示词缓存、对话历史缓存）
4. 100%可靠的工具调用
5. 完整的推理过程展示
"""

from openai import OpenAI
from typing import List, Dict, Any, Generator, Optional
import json
import re
from datetime import datetime

# 导入日志系统
from logger_config import get_logger

# 导入LangChain工具
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
    ReminderTool,
    VisitorRegistrationTool,
    MeetingRoomTool,
    EmployeeDirectoryTool,
    DirectionGuideTool,
    PackageManagementTool,
    FAQTool
) #真他妈长
import config

# 导入TTS优化和语音反馈
from tts_optimizer import TTSOptimizer # ttsoptimizer没有实现streaming pipline，所以好像没用上
from voice_feedback import VoiceWaitingFeedback # response空窗期播放声音，防止用户等待焦虑，但还没找到合适的音效
from tts_interface import TTSFactory, TTSProvider # ttsinterface是tts的范型接口，可以轻松切换tts服务，现在是edge tts，可以换openai或者自己的tts
from streaming_tts_pipeline import StreamingTTSPipeline, create_streaming_pipeline # streaming_tts_pipeline是流式tts的实现


class HybridReasoningAgent:
    """
    混合架构推理Agent
    
    架构：
    - OpenAI原生API：推理引擎（可控、快速、支持KV Cache）
    - LangChain工具：执行引擎（丰富、易扩展）
    - KV Cache：性能优化（对话历史、系统提示词自动缓存）
    """
    
    def __init__(
        self,
        api_key: str = None,
        model: str = None,
        temperature: float = None,
        enable_cache: bool = True,
        enable_tts: bool = False,
        voice_mode: bool = False,
        tts_engine: Optional[callable] = None,
        enable_streaming_tts: bool = False
    ):
        """
        初始化混合架构Agent
        
        Args:
            api_key: OpenAI API密钥
            model: 模型名称
            temperature: 温度参数
            enable_cache: 是否启用对话历史缓存（KV Cache优化）
            enable_tts: 是否启用TTS优化（传统批量模式）
            voice_mode: 是否启用语音等待反馈
            tts_engine: TTS引擎函数（可选）
            enable_streaming_tts: 是否启用流式TTS（推荐，更低延迟）
        """
        self.api_key = api_key or config.LLM_API_KEY
        self.model = model or config.LLM_MODEL
        self.temperature = temperature if temperature is not None else config.TEMPERATURE
        self.enable_cache = enable_cache
        self.enable_tts = enable_tts
        self.voice_mode = voice_mode
        self.enable_streaming_tts = enable_streaming_tts
        
        # 日志系统
        self.logger = get_logger(self.__class__.__name__)
        
        # OpenAI客户端（兼容Ollama）
        if config.LLM_BASE_URL:
            # 使用自定义base_url（Ollama或其他兼容服务）
            self.client = OpenAI(api_key=self.api_key, base_url=config.LLM_BASE_URL)
        else:
            # 使用OpenAI官方服务
            self.client = OpenAI(api_key=self.api_key)
        
        # LangChain工具池
        self.langchain_tools = self._init_langchain_tools()
        
        # 转换为OpenAI格式
        self.openai_tools = self._convert_tools_to_openai_format()
        
        # 工具名称映射
        self.tool_map = {tool.name: tool for tool in self.langchain_tools}
        
        # 对话历史（KV Cache会自动缓存）
        self.conversation_history = []
        
        # 系统提示词（会被KV Cache缓存，节省成本）
        self.system_prompt = self._create_system_prompt()
        
        # TTS引擎（共享）
        self.tts_engine = tts_engine
        if (self.enable_tts or self.enable_streaming_tts) and tts_engine is None:
            print(f"🎵 使用 Edge TTS（晓晓语音，语速 +15%）...")
            self.tts_engine = TTSFactory.create_tts(
                provider=TTSProvider.EDGE,
                voice="zh-CN-XiaoxiaoNeural",  # 晓晓 - 温柔女声 # 还有别的声音，可以换
                rate="+15%",    # 🔧 语速加快 15%（更自然）
                volume="+10%"   # 🔧 音量稍大
            )
        
        # TTS优化器（传统批量模式）
        if self.enable_tts:
            self.tts_optimizer = TTSOptimizer(
                tts_engine=self.tts_engine,
                max_chunk_length=100,
                max_retries=3,
                timeout_per_chunk=10,
                buffer_size=3
            )
        
        # 流式TTS管道（推荐模式）
        """
        最大程度保证没有背压
        
        根据内存和安全性大小，可以重新配置

        参数说明：
        - text_queue_size: 文本队列大小
        - audio_queue_size: 音频队列大小
        - max_tasks: 最大任务数
        - generation_timeout: 生成超时时间
        - playback_timeout: 播放超时时间
        - min_chunk_length: 最小句子长度
        - max_chunk_length: 最大句子长度
        """
        self.streaming_pipeline = None
        if self.enable_streaming_tts:
            self.streaming_pipeline = create_streaming_pipeline(
                tts_engine=self.tts_engine,
                text_queue_size=15,
                audio_queue_size=10,
                max_tasks=50,
                generation_timeout=15.0,
                playback_timeout=30.0,
                min_chunk_length=3, # 最小句子长度
                max_chunk_length=150, # 最大句子长度
                verbose=True
            )
            print(f"流式TTS管道已创建")
        
        # 语音反馈
        if self.voice_mode:
            self.voice_feedback = VoiceWaitingFeedback(mode='text')
        
        print(f"   混合架构Agent初始化成功")
        print(f"   引擎: OpenAI原生API ({self.model})")
        print(f"   工具: LangChain工具池 ({len(self.langchain_tools)}个)")
        print(f"   KV Cache: {'启用' if self.enable_cache else '禁用'}")
        print(f"   TTS优化: {'启用' if self.enable_tts else '禁用'}")
        print(f"   流式TTS: {'启用 ⚡' if self.enable_streaming_tts else '禁用'}")
        print(f"   语音模式: {'启用' if self.voice_mode else '禁用'}")
        print(f"   温度: {self.temperature}")
        print()
    
    def _init_langchain_tools(self) -> List:
        """初始化LangChain工具池"""
        return [
            # 基础工具
            CalculatorTool(),
            TimeTool(),
            TextAnalysisTool(),
            UnitConversionTool(),
            ComparisonTool(),
            LogicReasoningTool(),
            LibraryManagementTool(),
            ConversationEndDetector(),
            WebSearchTool(),
            FileOperationTool(),
            ReminderTool(),
            # 前台接待工具
            VisitorRegistrationTool(),
            MeetingRoomTool(),
            EmployeeDirectoryTool(),
            DirectionGuideTool(),
            PackageManagementTool(),
            FAQTool(),
        ]
    
    def _create_system_prompt(self) -> str:
        """
        创建系统提示词
        注意：这个提示词会被OpenAI自动缓存（Prompt Caching），节省50%成本
        """
        return """你是一个具有强大推理能力的AI语音助手。你叫茶茶。你的回答必须为tts优化，不能出现表情包和特殊符号。

核心能力：
1. 深度分析和理解用户问题
2. 必须使用工具解决问题（展示推理能力）
3. 自主决定工具参数（展示决策能力）
4. 基于结果进行综合推理

可用工具：
- calculator: 数学计算（sqrt、三角函数、复杂运算）
- time_tool: 时间查询（当前时间、日期、星期）
- text_analyzer: 文本分析（字数统计、句子分析）
- unit_converter: 单位转换（温度、长度等）
- data_comparison: 数据比较（最大最小值、排序）
- logic_reasoning: 逻辑推理辅助
- library_system: 图书馆管理系统（JSON查询）
- end_conversation_detector: 对话结束检测
- web_search: 网络搜索（模型自主决定搜索词）
- file_operation: 文件操作（模型自主决定操作类型）
- set_reminder: 提醒设置（模型自主提取任务和时间）

⚠️ 重要规则（必须严格遵守）：
1. **数学计算必须调用calculator** - 即使简单如"1+1"
2. **时间查询必须调用time_tool** - 不要猜测
3. **文本统计必须调用text_analyzer** - 不要估算
4. **单位转换必须调用unit_converter** - 不要心算
5. **对话结束必须调用end_conversation_detector** - 检测到"再见"等关键词时强制调用

🔄 推理流程：
第1步：分析用户问题类型和意图
第2步：确定需要使用的工具（根据上述规则）
第3步：自主决定工具的输入参数
第4步：等待工具执行结果
第5步：基于结果进行推理并生成答案

💡 示例：
用户："计算sqrt(2)保留3位小数"
→ 分析：这是数学计算问题
→ 决策：必须使用calculator工具
→ 参数：expression="round(sqrt(2), 3)"
→ 执行：调用工具
→ 回答：基于结果回答用户

用户："再见"
→ 分析：包含结束关键词或者相关结束词
→ 决策：必须调用end_conversation_detector
→ 参数：user_message="再见"
→ 执行：检测结果
→ 回答：告别语

现在开始严格遵守规则，帮助用户！"""
    
    def _convert_tools_to_openai_format(self) -> List[Dict]:
        """
        将LangChain工具转换为OpenAI Function Calling格式
        
        这是混合架构的关键：保留LangChain工具定义，但用OpenAI格式调用
        """
        openai_tools = []
        
        for tool in self.langchain_tools:
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
            return f"错误：工具 '{tool_name}' 不存在"
        
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
    
    def run(self, user_input: str, show_reasoning: bool = True) -> Dict[str, Any]:
        """
        执行推理（非流式）
        
        Args:
            user_input: 用户输入
            show_reasoning: 是否显示推理过程
            
        Returns:
            执行结果
        """
        if show_reasoning:
            print("\n" + "="*70)
            print("混合架构推理过程（OpenAI原生 + LangChain工具）")
            print("="*70)
        
        # 检测结束关键词
        contains_end_keyword = self._check_end_keywords(user_input)
        if contains_end_keyword and show_reasoning:
            print(f"\n预处理：检测到结束关键词，将强制要求调用end_conversation_detector")
        
        # 构建消息（利用KV Cache）
        messages = self._build_messages(user_input, contains_end_keyword)
        
        # 推理步骤记录
        reasoning_steps = []
        tool_call_count = 0
        
        try:
            # 第一次调用：模型决策
            if show_reasoning:
                print(f"\n{'─'*70}")
                print("调用OpenAI API进行推理...")
                print(f"{'─'*70}")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.openai_tools,
                tool_choice="auto",  # 可以改为"required"强制调用工具
                temperature=self.temperature
            )
            
            assistant_message = response.choices[0].message
            
            # 处理工具调用
            if assistant_message.tool_calls:
                if show_reasoning:
                    print(f"\n✅ 模型决定调用工具（共{len(assistant_message.tool_calls)}个）")
                
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
                
                # 第二次调用：基于工具结果生成最终回答
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
                # 没有工具调用，直接回答
                if show_reasoning:
                    print("\n⚠️  模型选择直接回答（未调用工具）")
                final_answer = assistant_message.content
            
            # 更新对话历史（用于KV Cache）
            if self.enable_cache:
                self.conversation_history.append({
                    "role": "user",
                    "content": user_input
                })
                self.conversation_history.append({
                    "role": "assistant",
                    "content": final_answer
                })
            
            # 分割句子（为TTS准备）
            sentences = self._split_sentences(final_answer)
            
            if show_reasoning:
                print(f"\n{'='*70}")
                print("💬 最终回答（已分句）")
                print(f"{'='*70}")
                for i, sent in enumerate(sentences, 1):
                    print(f"{i}. {sent}")
                print(f"{'='*70}\n")
            
            # 检查是否需要结束对话
            should_end = any(
                step['tool'] == 'end_conversation_detector' and 
                'END_CONVERSATION' in step['result']
                for step in reasoning_steps
            )
            
            return {
                'success': True,
                'output': final_answer,
                'sentences': sentences,
                'reasoning_steps': reasoning_steps,
                'tool_calls': tool_call_count,
                'should_end': should_end,
                'cached_tokens': len(self.conversation_history) if self.enable_cache else 0
            }
            
        except Exception as e:
            error_msg = f"执行错误: {str(e)}"
            print(f"\n❌ {error_msg}")
            return {
                'success': False,
                'output': error_msg,
                'error': str(e)
            }
    
    def _build_messages(self, user_input: str, force_end_detection: bool = False) -> List[Dict]:
        """
        构建消息列表
        
        系统提示词会被OpenAI自动缓存（Prompt Caching）
        对话历史也会被KV Cache优化
        """
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        # 添加对话历史（KV Cache优化）
        if self.enable_cache:
            messages.extend(self.conversation_history)
        
        # 添加当前输入
        user_message = user_input
        if force_end_detection:
            user_message += "\n\n[系统要求：检测到结束关键词，必须调用end_conversation_detector工具]"
        
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
            print(f"   ... (结果过长，已截断)")
        else:
            for line in result.split('\n'):
                print(f"   {line}")
        print(f"{'─'*70}")
    
    def _split_sentences(self, text: str) -> List[str]:
        """按句子分割文本（为TTS准备）"""
        pattern = r'([^。！？.!?]+[。！？.!?]+)'
        sentences = re.findall(pattern, text)
        
        if not sentences:
            pattern = r'([^，,;；]+[，,;；]+)'
            sentences = re.findall(pattern, text)
        
        if not sentences:
            sentences = [text]
        
        return [s.strip() for s in sentences if s.strip()]
    
    def _is_json_result(self, result: str) -> bool:
        """检查结果是否是JSON格式"""
        try:
            json.loads(result)
            return True
        except:
            return False
    
    def run_with_tts(self, 
                     user_input: str, 
                     show_reasoning: bool = True,
                     simulate_mode: bool = True) -> Dict[str, Any]:
        """
        执行推理并播放TTS音频
        
        Args:
            user_input: 用户输入
            show_reasoning: 是否显示推理过程
            simulate_mode: 是否模拟模式（无真实TTS引擎时）
            
        Returns:
            包含 raw_output, tts_chunks, playback_success 的字典
        """
        if not self.enable_tts:
            print("⚠️  TTS未启用，使用普通模式")
            return self.run(user_input, show_reasoning)
        
        # 语音反馈：开始思考
        if self.voice_mode:
            self.voice_feedback.start('thinking')
        
        # 执行推理
        result = self.run(user_input, show_reasoning)
        
        # 停止语音反馈
        if self.voice_mode:
            self.voice_feedback.stop()
        
        if not result['success']:
            return result
        
        # TTS优化并播放
        print(f"\n{'='*70}")
        print("🎵 TTS音频播放")
        print(f"{'='*70}\n")
        
        tts_result = self.tts_optimizer.optimize_and_play(
            text=result['output'],
            simulate_mode=simulate_mode
        )
        
        # 合并结果
        result.update({
            'tts_chunks': tts_result.get('tts_chunks', []),
            'tts_success': tts_result.get('success', False),
            'total_tts_chunks': tts_result.get('total_chunks', 0)
        })
        
        return result
    
    def run_with_tts_demo(self, 
                          user_input: str,
                          show_text_and_tts: bool = True) -> Dict[str, Any]:
        """
        演示模式：同时显示文本输出和TTS结构
        
        Args:
            user_input: 用户输入
            show_text_and_tts: 是否显示双轨输出
            
        Returns:
            完整结果字典
        """
        if not self.enable_tts:
            print("⚠️  TTS未启用")
            return self.run(user_input, show_reasoning=True)
        
        # 语音反馈
        if self.voice_mode:
            self.voice_feedback.start('thinking')
        
        # 执行推理
        result = self.run(user_input, show_reasoning=True)
        
        # 停止语音反馈
        if self.voice_mode:
            self.voice_feedback.stop()
        
        if not result['success']:
            return result
        
        # TTS优化（仅优化文本，不播放）
        tts_chunks = self.tts_optimizer.optimize_text_only(result['output'])
        
        if show_text_and_tts:
            # 显示双轨输出
            print(f"\n{'='*70}")
            print("📝 LLM原始文本输出")
            print(f"{'='*70}")
            print(result['output'])
            
            if tts_chunks:
                print(f"\n{'='*70}")
                print("🗣️  TTS优化输出结构")
                print(f"{'='*70}\n")
                
                for chunk in tts_chunks:
                    print(f"[Chunk {chunk['chunk_id']}]")
                    print(f"  文本: {chunk['text']}")
                    print(f"  长度: {chunk['length']} 字符")
                    print(f"  停顿: {chunk['pause_after']}ms")
                    print()
                
                print(f"{'='*70}")
                print(f"📊 TTS统计: 共{len(tts_chunks)}个分段")
                total_pause = sum(c['pause_after'] for c in tts_chunks)
                print(f"   预计播放时长: ~{total_pause/1000:.1f}秒（不含语音）")
                print(f"{'='*70}\n")
        
        result['tts_chunks'] = tts_chunks
        result['total_tts_chunks'] = len(tts_chunks)
        
        return result
    
    def run_with_streaming_tts(self,
                                user_input: str,
                                show_reasoning: bool = True,
                                tts_wait_timeout: int = 30) -> Dict[str, Any]:
        """
        流式TTS模式：LLM流式输出 → 实时TTS播放
        
        架构：
            LLM Streaming → Smart Splitter → TTS Generator → Audio Player
                              ↓ 背压           ↓ 背压          ↓
                           文本队列          音频队列        播放队列
        
        特点：
        1. 更低延迟 - 边生成边播放
        2. 资源可控 - 有界队列防止爆炸
        3. 自动背压 - 保护系统稳定
        
        Args:
            user_input: 用户输入
            show_reasoning: 是否显示推理过程
            
        Returns:
            完整结果字典
        """
        if not self.enable_streaming_tts:
            print("⚠️  流式TTS未启用，使用普通模式")
            return self.run(user_input, show_reasoning=show_reasoning)
        
        print(f"\n{'='*70}")
        print("⚡ 流式TTS模式")
        print(f"{'='*70}\n")
        
        # 启动流式管道
        self.streaming_pipeline.start()
        
        # 语音反馈
        if self.voice_mode:
            self.voice_feedback.start('thinking')
        
        try:
            # === 阶段1：LLM推理（使用OpenAI Stream API）===
            print(f"🧠 LLM推理中...\n")
            
            # 构建消息
            messages = [
                {"role": "system", "content": self.system_prompt},
                *self.conversation_history,
                {"role": "user", "content": user_input}
            ]
            
            # 调用OpenAI流式API
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.openai_tools,
                tool_choice="auto",
                temperature=self.temperature,
                stream=True  # 启用流式输出
            )
            
            # 累积变量
            full_response = ""
            tool_calls_buffer = []
            current_tool_call = None
            
            # === 阶段2：流式处理LLM输出 ===
            for chunk in stream:
                delta = chunk.choices[0].delta
                
                # 处理文本内容
                if delta.content:
                    content_piece = delta.content
                    full_response += content_piece
                    
                    # 实时送入TTS管道（智能分句会自动处理）
                    self.streaming_pipeline.add_text_from_llm(content_piece)
                    
                    if show_reasoning:
                        print(content_piece, end='', flush=True)
                
                # 处理工具调用
                if delta.tool_calls:
                    for tool_call_delta in delta.tool_calls:
                        if tool_call_delta.index is not None:
                            # 新的工具调用
                            if current_tool_call is None or \
                               tool_call_delta.index != current_tool_call.get('index'):
                                if current_tool_call:
                                    tool_calls_buffer.append(current_tool_call)
                                current_tool_call = {
                                    'index': tool_call_delta.index,
                                    'id': tool_call_delta.id or '',
                                    'type': 'function',
                                    'function': {
                                        'name': tool_call_delta.function.name or '',
                                        'arguments': tool_call_delta.function.arguments or ''
                                    }
                                }
                            else:
                                # 累积工具调用参数
                                if tool_call_delta.function.arguments:
                                    current_tool_call['function']['arguments'] += \
                                        tool_call_delta.function.arguments
            
            # 添加最后一个工具调用
            if current_tool_call:
                tool_calls_buffer.append(current_tool_call)
            
            # 停止语音反馈
            if self.voice_mode:
                self.voice_feedback.stop()
            
            print(f"\n")
            
            # === 阶段3：处理工具调用 ===
            should_end = False  # 检测对话结束
            
            if tool_calls_buffer:
                if show_reasoning:
                    print(f"\n{'='*70}")
                    print("🛠️  工具调用")
                    print(f"{'='*70}\n")
                
                tool_messages = []
                for tool_call in tool_calls_buffer:
                    tool_name = tool_call['function']['name']
                    tool_args_str = tool_call['function']['arguments']
                    
                    # 解析参数（修复bug：必须转为字典）
                    try:
                        tool_args = json.loads(tool_args_str)
                    except json.JSONDecodeError as e:
                        tool_args = {}
                        print(f"⚠️  工具参数解析失败: {e}")
                    
                    if show_reasoning:
                        print(f"📌 调用工具: {tool_name}")
                        print(f"   参数: {tool_args_str}\n")
                    
                    # 执行工具（传字典，不是字符串！）
                    tool_result = self._execute_tool(tool_name, tool_args)
                    
                    # 检测对话结束
                    if tool_name == 'end_conversation_detector' and 'END_CONVERSATION' in tool_result:
                        should_end = True
                    
                    if show_reasoning:
                        print(f"   结果: {tool_result}\n")
                    
                    # 构建工具消息
                    tool_messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call['id'],
                        "content": str(tool_result)
                    })
                
                # === 阶段4：获取最终回复（带工具结果）===
                print(f"{'='*70}")
                print("💬 最终回复")
                print(f"{'='*70}\n")
                
                # 构建包含工具结果的消息
                messages_with_tools = messages + [
                    {
                        "role": "assistant",
                        "content": full_response or None,
                        "tool_calls": [
                            {
                                "id": tc['id'],
                                "type": "function",
                                "function": {
                                    "name": tc['function']['name'],
                                    "arguments": tc['function']['arguments']
                                }
                            } for tc in tool_calls_buffer
                        ]
                    }
                ] + tool_messages
                
                # 再次调用（流式）
                final_stream = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages_with_tools,
                    temperature=self.temperature,
                    stream=True
                )
                
                final_response = ""
                for chunk in final_stream:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        content_piece = delta.content
                        final_response += content_piece
                        
                        # 实时送入TTS管道
                        self.streaming_pipeline.add_text_from_llm(content_piece)
                        
                        if show_reasoning:
                            print(content_piece, end='', flush=True)
                
                print(f"\n")
                full_response = final_response
            
            # === 阶段5：刷新TTS管道，处理剩余文本 ===
            self.streaming_pipeline.flush_remaining_text()
            
            # === 阶段6：等待所有音频播放完成 ===
            print(f"\n{'='*70}")
            print("🎵 等待音频播放完成...")
            print(f"{'='*70}\n")
            
            import time
            start_wait = time.time()
            
            while True:
                stats = self.streaming_pipeline.get_stats()
                
                # 🔧 日志：显示当前状态
                self.logger.debug(
                    f"⏳ TTS状态 - 文本队列:{stats.text_queue_size} "
                    f"音频队列:{stats.audio_queue_size} "
                    f"活跃任务:{stats.active_tasks} "
                    f"播放中:{stats.is_playing}"
                )
                
                # 检查所有条件（关键：包括 is_playing）
                all_done = (
                    stats.text_queue_size == 0 and 
                    stats.audio_queue_size == 0 and 
                    stats.active_tasks == 0 and
                    not stats.is_playing  # 关键：确保没有音频正在播放！
                )
                
                if all_done:
                    self.logger.info("✅ TTS 播放完成")
                    break
                
                # 🔧 超时保护
                elapsed = time.time() - start_wait
                if elapsed > tts_wait_timeout:
                    self.logger.warning(
                        f"⚠️  TTS 等待超时 ({tts_wait_timeout}秒)，强制继续\n"
                        f"   状态: 文本队列={stats.text_queue_size}, "
                        f"音频队列={stats.audio_queue_size}, "
                        f"活跃任务={stats.active_tasks}, "
                        f"播放中={stats.is_playing}"
                    )
                    break
                
                time.sleep(0.5)
            
            # 停止管道（🔧 注释掉，保持管道运行以支持多轮对话）
            # self.streaming_pipeline.stop(wait=True, timeout=5.0)
            
            # === 阶段7：更新对话历史 ===
            if self.enable_cache:
                self.conversation_history.append({"role": "user", "content": user_input})
                self.conversation_history.append({"role": "assistant", "content": full_response})
            
            # 返回结果
            return {
                'success': True,
                'input': user_input,
                'output': full_response,
                'tool_calls': len(tool_calls_buffer) if tool_calls_buffer else 0,
                'streaming_stats': self.streaming_pipeline.get_stats().to_dict(),
                'should_end': should_end  # 添加对话结束标志
            }
            
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            import traceback
            traceback.print_exc()
            
            # 确保管道停止
            if self.streaming_pipeline:
                self.streaming_pipeline.stop(wait=False)
            
            return {
                'success': False,
                'error': str(e),
                'input': user_input
            }
    
    def clear_cache(self):
        """清除对话历史缓存"""
        self.conversation_history = []
        print("✅ 对话历史已清除（KV Cache重置）")
    
    def get_cache_stats(self) -> Dict:
        """获取缓存统计信息"""
        return {
            'conversation_turns': len(self.conversation_history) // 2,
            'total_messages': len(self.conversation_history),
            'estimated_cached_tokens': sum(
                len(msg['content']) // 4 
                for msg in self.conversation_history
            ),
            'system_prompt_tokens': len(self.system_prompt) // 4
        }


# 快速测试
if __name__ == "__main__":
    print("\n" + "="*80)
    print("🚀 混合架构Agent测试")
    print("="*80)
    
    agent = HybridReasoningAgent()
    
    # 测试1：数学计算
    print("\n【测试1】数学计算")
    result1 = agent.run("计算sqrt(2)保留3位小数")
    
    # 测试2：对话结束
    print("\n【测试2】对话结束检测")
    result2 = agent.run("好的，再见！")
    
    # 缓存统计
    print("\n【缓存统计】")
    stats = agent.get_cache_stats()
    print(f"对话轮次: {stats['conversation_turns']}")
    print(f"缓存tokens估计: ~{stats['estimated_cached_tokens']}")
    print(f"系统提示词tokens: ~{stats['system_prompt_tokens']} (已缓存)")

