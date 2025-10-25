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
    # VoiceSelector,  # 🔧 已禁用：OpenAI TTS 原生支持多语言，无需切换
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
        
        # 🔧 为 VoiceSelector 注入 Agent 实例（已禁用：OpenAI TTS 原生支持多语言）
        # for tool in self.langchain_tools:
        #     if tool.name == "voiceSelector":
        #         tool.agent_instance = self
        #         self.logger.info("✅ VoiceSelector 已注入 Agent 实例")
        #         break
        
        # 对话历史（KV Cache会自动缓存）
        self.conversation_history = []
        
        # 系统提示词（会被KV Cache缓存，节省成本）
        self.system_prompt = self._create_system_prompt()
        
        # TTS引擎（共享）
        self.tts_engine = tts_engine
        if (self.enable_tts or self.enable_streaming_tts) and tts_engine is None:
            # 🔧 Fallback：如果没有传入TTS引擎，使用Edge TTS（免费）
            self.logger.warning("⚠️  未传入 TTS 引擎，使用 Edge TTS 作为 fallback")
            self.tts_engine = TTSFactory.create_tts(
                provider=TTSProvider.EDGE,
                voice="zh-CN-XiaoxiaoNeural",  # 晓晓 - 温柔女声
                rate="+15%",    # 语速加快 15%
                volume="+10%"   # 音量稍大
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
            # 多语言支持（新增）⭐ - 已禁用：OpenAI TTS 原生支持多语言
            # VoiceSelector(),
            # 前台接待工具
            VisitorRegistrationTool(),
            MeetingRoomTool(),
            EmployeeDirectoryTool(),
            DirectionGuideTool(),
            PackageManagementTool(),
            FAQTool(),
        ]
    
    def _convert_json_to_prompt(self, data: dict) -> str:
        """
        将 JSON 格式的 prompt 转换为文本格式
        
        Args:
            data: JSON prompt 数据
            
        Returns:
            str: 转换后的文本 prompt
        """
        lines = []
        
        # === 身份定义 ===
        if 'identity' in data:
            identity = data['identity']
            lines.append(f"你是一个{identity.get('role', 'AI助手')}。你叫{identity.get('name', '助手')}。")
            if 'personality' in identity:
                lines.append(f"特点：{identity['personality']}")
            lines.append("")
        
        # === 语音交互规范 ===
        if 'voice_interaction_rules' in data:
            rules = data['voice_interaction_rules']
            lines.append("🎯 **语音交互规范（必须严格遵守）**：")
            lines.append("")
            
            # 回复长度
            if 'response_length' in rules:
                rl = rules['response_length']
                lines.append(f"1. **回复长度**：每次回复控制在 {rl.get('max_chars', 100)} 字以内")
                if 'strategy' in rl:
                    lines.append(f"   - {rl['strategy']}")
                if 'complex_info_structure' in rl:
                    lines.append(f"   - 复杂信息用 {rl['complex_info_structure']} 结构")
                lines.append("")
            
            # 语言风格
            if 'language_style' in rules:
                ls = rules['language_style']
                lines.append("2. **语言风格**：")
                lines.append(f"   - {ls.get('tone', '简洁、口语化')}")
                if 'principle' in ls:
                    lines.append(f"   - {ls['principle']}")
                lines.append("")
            
            # 禁止输出
            if 'forbidden_outputs' in rules:
                fo = rules['forbidden_outputs']
                lines.append("3. **禁止输出（违反将导致错误）**：")
                for item in fo.get('strict_ban', []):
                    lines.append(f"   - ❌ {item}")
                lines.append("")
            
            # 对话结束协议
            if 'conversation_end_protocol' in rules:
                cep = rules['conversation_end_protocol']
                lines.append("4. **对话结束处理（重要）**：")
                lines.append(f"   - 触发词：{', '.join(cep.get('trigger_keywords', []))}")
                lines.append(f"   - 操作：{cep.get('action', '调用工具')}")
                lines.append(f"   - 禁止：{cep.get('forbidden', '')}")
                lines.append("")
            
            # 质量示例
            if 'quality_examples' in rules:
                qe = rules['quality_examples']
                lines.append("5. **示例对比**：")
                for good in qe.get('good', []):
                    lines.append(f'   ✅ 好："{good}"')
                for bad in qe.get('bad', []):
                    lines.append(f'   ❌ 差："{bad}"')
                lines.append("")
        
        # === 核心能力 ===
        if 'core_capabilities' in data:
            lines.append("核心能力：")
            for i, cap in enumerate(data['core_capabilities'], 1):
                if isinstance(cap, dict):
                    status = f" ({cap['status']})" if 'status' in cap else ""
                    lines.append(f"{i}. {cap.get('name', '')}{status}")
                else:
                    lines.append(f"{i}. {cap}")
            lines.append("")
        
        # === 可用工具 ===
        if 'available_tools' in data:
            lines.append("可用工具：")
            for tool in data['available_tools']:
                if isinstance(tool, dict):
                    name = tool.get('name', '')
                    desc = tool.get('description', '')
                    lines.append(f"- {name}: {desc}")
                else:
                    lines.append(f"- {tool}")
            lines.append("")
        
        # === 强制规则 ===
        if 'mandatory_rules' in data:
            mr = data['mandatory_rules']
            lines.append("⚠️ 重要规则（必须严格遵守）：")
            for i, rule in enumerate(mr.get('must_use_tools', []), 1):
                if isinstance(rule, dict):
                    lines.append(f"{i}. **{rule.get('rule', '')}** - {rule.get('reason', '')}")
                else:
                    lines.append(f"{i}. {rule}")
            lines.append("")
        
        # === 推理流程 ===
        if 'reasoning_process' in data:
            rp = data['reasoning_process']
            lines.append("🔄 推理流程：")
            for step in rp.get('steps', []):
                if isinstance(step, dict):
                    lines.append(f"第{step.get('step', '')}步：{step.get('action', '')}")
            lines.append("")
        
        # === 示例 ===
        if 'examples' in data:
            lines.append("💡 示例：")
            examples = data['examples']
            for key, example in examples.items():
                if isinstance(example, dict) and 'user_input' in example:
                    lines.append(f'\n用户："{example["user_input"]}"')
                    if 'step_1_analysis' in example:
                        lines.append(f"→ 分析：{example['step_1_analysis']}")
                    if 'step_2_tool_selection' in example:
                        lines.append(f"→ 决策：{example['step_2_tool_selection']}")
                    if 'step_5_response' in example:
                        lines.append(f"→ 回答：{example['step_5_response']}")
            lines.append("")
        
        # === 最终提醒 ===
        if 'system_instructions' in data:
            si = data['system_instructions']
            if 'final_reminder' in si:
                lines.append(si['final_reminder'])
        
        return "\n".join(lines)
    
    def _create_system_prompt(self) -> str:
        """
        从外部文件加载系统提示词（方便修改和维护）
        优先级：JSON > TXT > 内置默认
        注意：这个提示词会被OpenAI自动缓存（Prompt Caching），节省50%成本
        """
        from pathlib import Path
        import json
        
        prompts_dir = Path(__file__).parent / "prompts"
        
        # 1. 优先尝试加载 JSON 格式（推荐）
        json_path = prompts_dir / "system_prompt.json"
        if json_path.exists():
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    prompt_data = json.load(f)
                    prompt = self._convert_json_to_prompt(prompt_data)
                    if prompt:
                        self.logger.info(f"✅ 已从 JSON 加载 System Prompt: {json_path}")
                        return prompt
            except Exception as e:
                self.logger.warning(f"⚠️  加载 JSON prompt 失败: {e}，尝试 TXT")
        
        # 2. 回退到 TXT 格式
        txt_path = prompts_dir / "system_prompt.txt"
        if txt_path.exists():
            try:
                with open(txt_path, 'r', encoding='utf-8') as f:
                    prompt = f.read().strip()
                    if prompt:
                        self.logger.info(f"✅ 已从 TXT 加载 System Prompt: {txt_path}")
                        return prompt
            except Exception as e:
                self.logger.warning(f"⚠️  加载 TXT prompt 失败: {e}，使用内置默认")
        
        # 回退到默认 prompt（备份）
        self.logger.info("使用内置默认 System Prompt")
        return """你是一个具有强大推理能力的AI语音助手。你叫茶茶。

🎯 **语音交互规范（必须严格遵守）**：
1. **回复长度**：每次回复控制在 50-100 字以内（约 10-20 秒语音）
   - 如需详细说明，分段回复（每段不超过 100 字）
   - 复杂信息用"首先...其次...最后..."结构
2. **语言风格**：
   - 使用简洁的口语化表达
   - 直接回答，不啰嗦，不重复
   - 避免使用书面语
3. **禁止输出（违反将导致错误）**：
   - ❌ 表情包、emoji、特殊符号（除了基本标点）
   - ❌ Markdown 格式（代码块、加粗、链接等）
   - ❌ 代码块（用"代码内容"代替）
   - ❌ JSON 格式（用自然语言描述）
   - ❌ 链接（用"可以搜索XX了解"代替）
   - ❌ 任何系统标记，包括：(END_CONVERSATION)、END_CONVERSATION、ENDCONVERSATION 等
4. **对话结束处理（重要）**：
   - 当用户表达结束意图（如"再见"、"谢谢"、"没事了"）时
   - **必须调用 detectConversationEnd 工具**（注意：驼峰命名，无下划线）
   - **绝对不要**在回复中直接输出任何包含 "END" 或 "CONVERSATION" 的文本
   - 正确示例：先礼貌回复"好的，再见"，然后调用工具
5. **示例对比**：
   ✅ 好："现在是下午3点15分。"
   ❌ 差："现在的时间是下午3点15分，希望对你有帮助！😊"
   ✅ 好："根号2约等于1.414。"
   ❌ 差："让我来计算一下...根号2的值大约是1.414，这是一个无理数哦！"

核心能力：
1. 深度分析和理解用户问题
2. 必须使用工具解决问题（展示推理能力）
3. 自主决定工具参数（展示决策能力）
4. 基于结果进行综合推理
5. **自动适配多语言语音**（新增核心功能）⭐

🌍 **多语言语音自动切换（重要新功能）**：
你现在支持 6 种语言的智能语音切换！当用户切换语言时，你必须主动调用 voiceSelector 工具切换语音。

**何时必须切换语音**：
1. **用户用非中文提问时**：
   - 英文："Hello" / "How are you?" → 立即切换到英文语音（english）
   - 日文："こんにちは" / "ありがとう" → 立即切换到日文语音（japanese）
   - 法语："Bonjour" / "Merci" → 立即切换到法语语音（french）
   - 西班牙语："Hola" / "Gracias" → 立即切换到西班牙语（spanish）
   - 越南语："Xin chào" → 立即切换到越南语（vietnamese）

2. **用户切换回中文时**：
   - 检测到中文对话 → 切换回中文语音（chinese）

3. **回答内容涉及特定语言时**：
   - 讲日本文化/故事 → 使用日文语音
   - 教英语/讲英美内容 → 使用英文语音
   - 法国文化/法语教学 → 使用法语语音

**切换规则**：
- ✅ 语音会一直保持，直到你下次调用 voiceSelector
- ✅ 不要每句话都切换，只在语言环境改变时切换
- ✅ 如果用户用混合语言，使用主要语言的语音
- ✅ 默认语音是中文（晓晓女声）

**示例场景**：
```
用户: "Hello, what's your name?"
你的操作：
  步骤1：调用 voiceSelector(language="english", reason="用户用英文提问")
  步骤2：用英文回答 "My name is ChaCha. How can I help you?"
  → 之后保持英文语音，直到用户切换回中文

用户: "你好，现在几点了？"
你的操作：
  步骤1：调用 voiceSelector(language="chinese", reason="用户切换回中文")
  步骤2：调用 time_tool 获取时间
  步骤3：用中文回答 "现在是下午3点15分。"
  → 之后保持中文语音
```

可用工具：
- calculator: 数学计算（sqrt、三角函数、复杂运算）
- time_tool: 时间查询（当前时间、日期、星期）
- text_analyzer: 文本分析（字数统计、句子分析）
- unit_converter: 单位转换（温度、长度等）
- data_comparison: 数据比较（最大最小值、排序）
- logic_reasoning: 逻辑推理辅助
- library_system: 图书馆管理系统（JSON查询）
- detectConversationEnd: 对话结束检测（驼峰命名，无下划线）
- voiceSelector: **多语言语音切换**（新增核心工具）⭐
- web_search: 网络搜索（模型自主决定搜索词）
- file_operation: 文件操作（模型自主决定操作类型）
- set_reminder: 提醒设置（模型自主提取任务和时间）

⚠️ 重要规则（必须严格遵守）：
1. **数学计算必须调用calculator** - 即使简单如"1+1"
2. **时间查询必须调用time_tool** - 不要猜测
3. **文本统计必须调用text_analyzer** - 不要估算
4. **单位转换必须调用unit_converter** - 不要心算
5. **对话结束必须调用detectConversationEnd** - 检测到"再见"等关键词时强制调用
6. **语言切换必须调用voiceSelector** - 检测到非中文提问时立即切换语音 ⭐

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
→ 决策：必须调用detectConversationEnd
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
            print(f"\n预处理：检测到结束关键词，将强制要求调用detectConversationEnd")
        
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
                step['tool'] == 'detectConversationEnd' and 
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
            user_message += "\n\n[系统要求：检测到结束关键词，必须调用detectConversationEnd工具]"
        
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
                    
                    # 🔧 第一步：先清理 Markdown 符号（流式安全）
                    cleaned_piece = content_piece.replace('**', '').replace('__', '')
                    cleaned_piece = cleaned_piece.replace('*', '').replace('_', '')
                    cleaned_piece = cleaned_piece.replace('```', '')
                    cleaned_piece = cleaned_piece.replace('`', '')
                    cleaned_piece = cleaned_piece.replace('#', '')
                    
                    # 🔧 第二步：过滤特殊标记（支持多种变体）
                    # 检查清理后的文本，防止 (END_CONVERSATION) 的下划线被删除后变成 (ENDCONVERSATION)
                    should_filter = any([
                        "(END_CONVERSATION)" in cleaned_piece.upper(),
                        "(ENDCONVERSATION)" in cleaned_piece.upper(),
                        "END_CONVERSATION" in cleaned_piece.upper(),
                        "ENDCONVERSATION" in cleaned_piece.upper(),
                    ])
                    
                    if not should_filter and cleaned_piece.strip():
                        # 实时送入TTS管道（智能分句会自动处理）
                        self.streaming_pipeline.add_text_from_llm(cleaned_piece)
                    
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
                # 🎵 开始播放工具调用音效
                if self.voice_mode:
                    self.voice_feedback.start('tool_thinking')
                
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
                    if tool_name == 'detectConversationEnd' and 'END_CONVERSATION' in tool_result:
                        should_end = True
                    
                    if show_reasoning:
                        print(f"   结果: {tool_result}\n")
                    
                    # 构建工具消息
                    tool_messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call['id'],
                        "content": str(tool_result)
                    })
                
                # 🎵 停止工具调用音效
                if self.voice_mode:
                    self.voice_feedback.stop()
                
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
                        
                        # 🔧 第一步：先清理 Markdown 符号（流式安全）
                        cleaned_piece = content_piece.replace('**', '').replace('__', '')
                        cleaned_piece = cleaned_piece.replace('*', '').replace('_', '')
                        cleaned_piece = cleaned_piece.replace('```', '')
                        cleaned_piece = cleaned_piece.replace('`', '')
                        cleaned_piece = cleaned_piece.replace('#', '')
                        
                        # 🔧 第二步：过滤特殊标记（支持多种变体）
                        should_filter = any([
                            "(END_CONVERSATION)" in cleaned_piece.upper(),
                            "(ENDCONVERSATION)" in cleaned_piece.upper(),
                            "END_CONVERSATION" in cleaned_piece.upper(),
                            "ENDCONVERSATION" in cleaned_piece.upper(),
                        ])
                        
                        if not should_filter and cleaned_piece.strip():
                            # 实时送入TTS管道
                            self.streaming_pipeline.add_text_from_llm(cleaned_piece)
                        
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
            
            # 🔧 关键修复：清空并重启 TTS 管道（防止串音）
            if self.streaming_pipeline:
                self.streaming_pipeline.stop(wait=False)
                self.streaming_pipeline.start()  # 重启以清空队列
            
            return {
                'success': False,
                'output': '',           # 🔧 补充缺失的 output 键
                'error': str(e),
                'input': user_input,
                'tool_calls': 0,        # 🔧 补充缺失的 tool_calls 键
                'streaming_stats': None  # 🔧 补充缺失的 streaming_stats 键
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

