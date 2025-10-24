"""
LangChain工具库 - 为混合架构Agent提供丰富的工具集

包含：
1. 基础工具（计算、时间、文本分析等）
2. 图书馆管理工具
3. 对话管理工具
4. 前台接待专用工具（新增）
"""

from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Optional, List, Dict, Any
import math
import re
from datetime import datetime, timedelta
import json


# ============================================================
# 基础工具
# ============================================================

class CalculatorInput(BaseModel):
    """计算器工具输入"""
    expression: str = Field(description="数学表达式，支持基本运算和函数如sqrt、sin、cos等")


class CalculatorTool(BaseTool):
    """数学计算工具 - 支持各种数学运算"""
    
    name: str = "calculator"
    description: str = """
    数学计算工具。用于计算数学表达式。
    支持：
    - 基本运算：+、-、*、/、**（幂运算）
    - 函数：sqrt（平方根）、sin、cos、tan、log、exp
    - 常数：pi、e
    - 函数：round（四舍五入）、abs（绝对值）
    
    示例：
    - "sqrt(2)" → 1.414...
    - "round(sqrt(2), 3)" → 1.414
    - "sin(pi/2)" → 1.0
    """
    args_schema: Type[BaseModel] = CalculatorInput
    
    def _run(self, expression: str) -> str:
        try:
            # 安全的数学命名空间
            safe_dict = {
                'sqrt': math.sqrt,
                'sin': math.sin,
                'cos': math.cos,
                'tan': math.tan,
                'log': math.log,
                'exp': math.exp,
                'pi': math.pi,
                'e': math.e,
                'round': round,
                'abs': abs,
                'pow': pow,
                'floor': math.floor,
                'ceil': math.ceil,
            }
            
            result = eval(expression, {"__builtins__": {}}, safe_dict)
            return str(result)
        except Exception as e:
            return f"计算错误: {str(e)}"


class TimeToolInput(BaseModel):
    """时间工具输入"""
    query_type: str = Field(
        description="查询类型：current_time（当前时间）、current_date（日期）、weekday（星期）、full（完整信息）"
    )


class TimeTool(BaseTool):
    """时间日期工具"""
    
    name: str = "time_tool"
    description: str = """
    获取当前时间和日期信息。
    支持的查询类型：
    - current_time: 当前时间（时:分:秒）
    - current_date: 当前日期（年-月-日）
    - weekday: 星期几
    - full: 完整的日期时间信息
    """
    args_schema: Type[BaseModel] = TimeToolInput
    
    def _run(self, query_type: str) -> str:
        now = datetime.now()
        
        if query_type == "current_time":
            return now.strftime("%H:%M:%S")
        elif query_type == "current_date":
            return now.strftime("%Y年%m月%d日")
        elif query_type == "weekday":
            weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
            return weekdays[now.weekday()]
        elif query_type == "full":
            weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
            return f"{now.strftime('%Y年%m月%d日')} {weekdays[now.weekday()]} {now.strftime('%H:%M:%S')}"
        else:
            return "不支持的查询类型"


class TextAnalysisInput(BaseModel):
    """文本分析工具输入"""
    text: str = Field(description="要分析的文本")
    analysis_type: str = Field(
        description="分析类型：word_count（字数）、char_count（字符数）、sentence_count（句子数）、all（全部）",
        default="all"
    )


class TextAnalysisTool(BaseTool):
    """文本分析工具"""
    
    name: str = "text_analyzer"
    description: str = """
    文本分析工具，统计文本的各种信息。
    支持：
    - word_count: 统计字数（中文按字，英文按单词）
    - char_count: 统计字符数
    - sentence_count: 统计句子数
    - all: 返回所有统计信息
    """
    args_schema: Type[BaseModel] = TextAnalysisInput
    
    def _run(self, text: str, analysis_type: str = "all") -> str:
        # 字符数
        char_count = len(text)
        
        # 字数（中文字符 + 英文单词）
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))
        word_count = chinese_chars + english_words
        
        # 句子数
        sentences = re.split(r'[。！？.!?]+', text)
        sentence_count = len([s for s in sentences if s.strip()])
        
        if analysis_type == "word_count":
            return f"字数: {word_count}"
        elif analysis_type == "char_count":
            return f"字符数: {char_count}"
        elif analysis_type == "sentence_count":
            return f"句子数: {sentence_count}"
        else:
            return f"字符数: {char_count}, 字数: {word_count}, 句子数: {sentence_count}"


class UnitConversionInput(BaseModel):
    """单位转换工具输入"""
    value: float = Field(description="要转换的数值")
    from_unit: str = Field(description="源单位")
    to_unit: str = Field(description="目标单位")
    category: str = Field(description="类别：temperature（温度）、length（长度）、weight（重量）")


class UnitConversionTool(BaseTool):
    """单位转换工具"""
    
    name: str = "unit_converter"
    description: str = """
    单位转换工具。支持：
    - 温度：celsius（摄氏度）、fahrenheit（华氏度）、kelvin（开尔文）
    - 长度：meter（米）、kilometer（千米）、mile（英里）、foot（英尺）
    - 重量：kilogram（千克）、gram（克）、pound（磅）
    """
    args_schema: Type[BaseModel] = UnitConversionInput
    
    def _run(self, value: float, from_unit: str, to_unit: str, category: str) -> str:
        try:
            if category == "temperature":
                return self._convert_temperature(value, from_unit, to_unit)
            elif category == "length":
                return self._convert_length(value, from_unit, to_unit)
            elif category == "weight":
                return self._convert_weight(value, from_unit, to_unit)
            else:
                return "不支持的转换类别"
        except Exception as e:
            return f"转换错误: {str(e)}"
    
    def _convert_temperature(self, value: float, from_unit: str, to_unit: str) -> str:
        # 转换为摄氏度
        if from_unit == "celsius":
            celsius = value
        elif from_unit == "fahrenheit":
            celsius = (value - 32) * 5/9
        elif from_unit == "kelvin":
            celsius = value - 273.15
        else:
            return "不支持的温度单位"
        
        # 从摄氏度转换
        if to_unit == "celsius":
            result = celsius
        elif to_unit == "fahrenheit":
            result = celsius * 9/5 + 32
        elif to_unit == "kelvin":
            result = celsius + 273.15
        else:
            return "不支持的温度单位"
        
        return f"{value} {from_unit} = {result:.2f} {to_unit}"
    
    def _convert_length(self, value: float, from_unit: str, to_unit: str) -> str:
        # 转换为米
        to_meter = {
            "meter": 1,
            "kilometer": 1000,
            "mile": 1609.34,
            "foot": 0.3048,
        }
        
        if from_unit not in to_meter or to_unit not in to_meter:
            return "不支持的长度单位"
        
        meters = value * to_meter[from_unit]
        result = meters / to_meter[to_unit]
        
        return f"{value} {from_unit} = {result:.2f} {to_unit}"
    
    def _convert_weight(self, value: float, from_unit: str, to_unit: str) -> str:
        # 转换为千克
        to_kg = {
            "kilogram": 1,
            "gram": 0.001,
            "pound": 0.453592,
        }
        
        if from_unit not in to_kg or to_unit not in to_kg:
            return "不支持的重量单位"
        
        kg = value * to_kg[from_unit]
        result = kg / to_kg[to_unit]
        
        return f"{value} {from_unit} = {result:.2f} {to_unit}"


class ComparisonInput(BaseModel):
    """数据比较工具输入"""
    numbers: List[float] = Field(description="要比较的数字列表")
    operation: str = Field(description="操作：max（最大值）、min（最小值）、avg（平均值）、sort（排序）")


class ComparisonTool(BaseTool):
    """数据比较工具"""
    
    name: str = "data_comparison"
    description: str = """
    数据比较和统计工具。
    支持操作：
    - max: 找出最大值
    - min: 找出最小值
    - avg: 计算平均值
    - sort: 排序（从小到大）
    """
    args_schema: Type[BaseModel] = ComparisonInput
    
    def _run(self, numbers: List[float], operation: str) -> str:
        if not numbers:
            return "数字列表为空"
        
        if operation == "max":
            return f"最大值: {max(numbers)}"
        elif operation == "min":
            return f"最小值: {min(numbers)}"
        elif operation == "avg":
            return f"平均值: {sum(numbers)/len(numbers):.2f}"
        elif operation == "sort":
            return f"排序结果: {sorted(numbers)}"
        else:
            return "不支持的操作"


class LogicReasoningInput(BaseModel):
    """逻辑推理工具输入"""
    problem: str = Field(description="逻辑问题描述")


class LogicReasoningTool(BaseTool):
    """逻辑推理辅助工具"""
    
    name: str = "logic_reasoning"
    description: str = """
    逻辑推理辅助工具，帮助结构化分析逻辑问题。
    用于帮助AI进行系统性的逻辑推理。
    """
    args_schema: Type[BaseModel] = LogicReasoningInput
    
    def _run(self, problem: str) -> str:
        return f"""
逻辑推理框架：
问题: {problem}

建议分析步骤：
1. 识别关键信息和前提条件
2. 列出已知和未知要素
3. 应用逻辑规则进行推理
4. 验证结论的合理性
5. 给出最终答案

请基于此框架进行系统性推理。
"""


# ============================================================
# 图书馆管理工具
# ============================================================

class LibraryQueryInput(BaseModel):
    """图书馆查询输入"""
    query_type: str = Field(description="查询类型：search_book（搜索书籍）、check_status（检查状态）、list_all（列出所有）")
    keyword: str = Field(description="搜索关键词（书名、作者、类别）", default="")


class LibraryManagementTool(BaseTool):
    """图书馆管理系统工具 - 查询图书信息、借阅状态等"""
    
    name: str = "library_system"
    description: str = """
    图书馆管理系统工具，用于查询图书信息。
    
    支持的查询类型：
    - search_book: 搜索书籍（通过书名、作者或类别）
    - check_status: 检查特定书籍的借阅状态
    - list_all: 列出所有图书
    
    返回JSON格式的图书信息。
    """
    args_schema: Type[BaseModel] = LibraryQueryInput
    
    def _get_books_db(self):
        """获取图书馆数据库（模拟数据）"""
        return [
            {
                "isbn": "978-7-115-54321-0",
                "title": "Python编程：从入门到实践",
                "author": "Eric Matthes",
                "category": "编程",
                "status": "可借阅",
                "location": "A区-3层-102架"
            },
            {
                "isbn": "978-7-111-64474-5",
                "title": "深度学习",
                "author": "Ian Goodfellow",
                "category": "人工智能",
                "status": "已借出",
                "location": "B区-2层-205架",
                "return_date": "2025-11-05"
            },
            {
                "isbn": "978-7-121-39082-5",
                "title": "机器学习实战",
                "author": "Peter Harrington",
                "category": "机器学习",
                "status": "可借阅",
                "location": "B区-2层-203架"
            },
            {
                "isbn": "978-7-115-52801-9",
                "title": "算法导论",
                "author": "Thomas H. Cormen",
                "category": "算法",
                "status": "可借阅",
                "location": "A区-3层-105架"
            },
            {
                "isbn": "978-7-121-35292-2",
                "title": "Python数据分析",
                "author": "Wes McKinney",
                "category": "数据分析",
                "status": "已借出",
                "location": "B区-2层-210架",
                "return_date": "2025-11-10"
            }
        ]
    
    def _run(self, query_type: str, keyword: str = "") -> str:
        import json
        
        books_db = self._get_books_db()
        
        if query_type == "list_all":
            result = {
                "total": len(books_db),
                "books": books_db
            }
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        elif query_type == "search_book":
            keyword_lower = keyword.lower()
            found_books = [
                book for book in books_db
                if keyword_lower in book["title"].lower() or
                   keyword_lower in book["author"].lower() or
                   keyword_lower in book["category"].lower()
            ]
            
            result = {
                "query": keyword,
                "found": len(found_books),
                "books": found_books
            }
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        elif query_type == "check_status":
            for book in books_db:
                if keyword.lower() in book["title"].lower():
                    return json.dumps(book, ensure_ascii=False, indent=2)
            
            return json.dumps({
                "error": f"未找到书籍: {keyword}"
            }, ensure_ascii=False, indent=2)
        
        else:
            return json.dumps({
                "error": "不支持的查询类型"
            }, ensure_ascii=False, indent=2)


# ============================================================
# 对话管理工具
# ============================================================

class ConversationEndInput(BaseModel):
    """对话结束检测输入"""
    user_message: str = Field(description="用户的消息内容")


class ConversationEndDetector(BaseTool):
    """对话结束检测工具 - 识别用户是否想要结束对话"""
    
    name: str = "end_conversation_detector"
    description: str = """
    【强制调用】对话结束检测工具 - 当用户消息中包含结束关键词时，必须调用此工具！
    
    **何时必须使用此工具**：
    - 用户说"再见"、"拜拜"、"bye"、"goodbye"
    - 用户说"退出"、"结束"、"关闭"、"离开"
    - 用户说"不聊了"、"走了"、"下线"
    - 用户说"quit"、"exit"、"886"、"88"
    
    **这是强制性的** - 只要检测到这些关键词，就必须调用此工具！
    
    返回：
    - "END_CONVERSATION" - 检测到结束意图
    - "CONTINUE" - 用户想继续对话
    """
    args_schema: Type[BaseModel] = ConversationEndInput
    
    def _run(self, user_message: str) -> str:
        end_keywords = [
            '再见', '拜拜', 'bye', 'goodbye', '退出', '结束',
            '关闭', '离开', '不聊了', '走了', 'quit', 'exit',
            '886', '88', '下线', '断开'
        ]
        
        message_lower = user_message.lower().strip()
        
        for keyword in end_keywords:
            if keyword in message_lower:
                return "END_CONVERSATION: 检测到用户想要结束对话"
        
        return "CONTINUE: 用户想继续对话"


class WebSearchInput(BaseModel):
    """网络搜索工具输入"""
    query: str = Field(description="搜索关键词")
    num_results: int = Field(description="返回结果数量", default=3)


class WebSearchTool(BaseTool):
    """网络搜索工具（模拟）"""
    
    name: str = "web_search"
    description: str = """
    网络搜索工具，模拟搜索引擎查询。
    模型需要自主决定搜索关键词和结果数量。
    """
    args_schema: Type[BaseModel] = WebSearchInput
    
    def _run(self, query: str, num_results: int = 3) -> str:
        # 模拟搜索结果
        results = [
            {
                "title": f"关于'{query}'的最新资讯 - 百度百科",
                "snippet": f"这是关于{query}的详细介绍...",
                "url": f"https://baike.baidu.com/item/{query}"
            },
            {
                "title": f"{query} - 维基百科",
                "snippet": f"{query}是一个...的概念",
                "url": f"https://zh.wikipedia.org/wiki/{query}"
            },
            {
                "title": f"{query}的应用和发展",
                "snippet": f"深入了解{query}的实际应用...",
                "url": f"https://example.com/{query}"
            }
        ]
        
        return json.dumps({
            "query": query,
            "results": results[:num_results]
        }, ensure_ascii=False, indent=2)


class FileOperationInput(BaseModel):
    """文件操作工具输入"""
    operation: str = Field(description="操作类型：read（读取）、write（写入）、list（列表）")
    filename: str = Field(description="文件名", default="")
    content: str = Field(description="要写入的内容", default="")


class FileOperationTool(BaseTool):
    """文件操作工具（模拟）"""
    
    name: str = "file_operation"
    description: str = """
    文件操作工具（模拟），支持读取、写入和列出文件。
    模型需要自主决定操作类型、文件名和内容。
    """
    args_schema: Type[BaseModel] = FileOperationInput
    
    def _run(self, operation: str, filename: str = "", content: str = "") -> str:
        if operation == "read":
            return f"[模拟] 读取文件 '{filename}' 的内容..."
        elif operation == "write":
            return f"[模拟] 已将内容写入文件 '{filename}'"
        elif operation == "list":
            return "[模拟] 文件列表: file1.txt, file2.txt, data.json"
        else:
            return "不支持的文件操作"


class ReminderInput(BaseModel):
    """提醒工具输入"""
    task: str = Field(description="提醒的任务内容")
    time: str = Field(description="提醒时间")
    priority: str = Field(description="优先级：high（高）、medium（中）、low（低）", default="medium")


class ReminderTool(BaseTool):
    """提醒设置工具"""
    
    name: str = "set_reminder"
    description: str = """
    设置提醒工具。模型需要自主从用户话语中提取：
    - 任务内容
    - 时间（可能是相对时间如"明天"、"3点"）
    - 优先级（根据任务重要性判断）
    """
    args_schema: Type[BaseModel] = ReminderInput
    
    def _run(self, task: str, time: str, priority: str = "medium") -> str:
        return json.dumps({
            "status": "success",
            "reminder": {
                "task": task,
                "time": time,
                "priority": priority,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            "message": f"已设置{priority}优先级提醒：{task}，时间：{time}"
        }, ensure_ascii=False, indent=2)


# ============================================================
# 前台接待专用工具（新增）
# ============================================================

class VisitorRegistrationInput(BaseModel):
    """访客登记输入"""
    visitor_name: str = Field(description="访客姓名")
    company: str = Field(description="访客公司", default="")
    visit_purpose: str = Field(description="来访目的")
    contact_person: str = Field(description="受访人姓名")
    contact_department: str = Field(description="受访人部门", default="")


class VisitorRegistrationTool(BaseTool):
    """访客登记工具"""
    
    name: str = "visitor_registration"
    description: str = """
    访客登记/签到工具。用于登记访客信息。
    
    需要收集的信息：
    - 访客姓名
    - 访客公司（可选）
    - 来访目的
    - 受访人姓名
    - 受访人部门（可选）
    
    模型需要从对话中智能提取这些信息。
    """
    args_schema: Type[BaseModel] = VisitorRegistrationInput
    
    def _run(
        self,
        visitor_name: str,
        company: str = "",
        visit_purpose: str = "",
        contact_person: str = "",
        contact_department: str = ""
    ) -> str:
        visit_id = f"V{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        return json.dumps({
            "status": "success",
            "visit_id": visit_id,
            "visitor_info": {
                "name": visitor_name,
                "company": company,
                "purpose": visit_purpose,
                "contact": contact_person,
                "department": contact_department,
                "check_in_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "badge_number": f"BADGE-{visit_id[-6:]}"
            },
            "message": f"登记成功！访客编号：{visit_id}，请佩戴{visit_id[-6:]}号访客牌。"
        }, ensure_ascii=False, indent=2)


class MeetingRoomQueryInput(BaseModel):
    """会议室查询输入"""
    query_type: str = Field(description="查询类型：availability（查询空闲）、book（预订）、cancel（取消）、list（列出所有）")
    room_name: str = Field(description="会议室名称", default="")
    start_time: str = Field(description="开始时间", default="")
    duration: int = Field(description="时长（分钟）", default=60)
    organizer: str = Field(description="预订人", default="")


class MeetingRoomTool(BaseTool):
    """会议室管理工具"""
    
    name: str = "meeting_room_system"
    description: str = """
    会议室预订和查询系统。
    
    支持功能：
    - availability: 查询指定时间段的空闲会议室
    - book: 预订会议室
    - cancel: 取消预订
    - list: 列出所有会议室及当前状态
    
    会议室信息包括：名称、容量、设备、当前状态等。
    """
    args_schema: Type[BaseModel] = MeetingRoomQueryInput
    
    def _get_meeting_rooms(self):
        """获取会议室数据"""
        return [
            {
                "room_id": "MR001",
                "name": "创新会议室",
                "capacity": 10,
                "equipment": ["投影仪", "白板", "视频会议"],
                "floor": 3,
                "status": "空闲",
                "next_booking": None
            },
            {
                "room_id": "MR002",
                "name": "头脑风暴室",
                "capacity": 6,
                "equipment": ["白板", "便签墙"],
                "floor": 3,
                "status": "使用中",
                "next_booking": "15:00-16:00"
            },
            {
                "room_id": "MR003",
                "name": "大型会议室",
                "capacity": 30,
                "equipment": ["投影仪", "音响系统", "视频会议"],
                "floor": 5,
                "status": "空闲",
                "next_booking": None
            }
        ]
    
    def _run(
        self,
        query_type: str,
        room_name: str = "",
        start_time: str = "",
        duration: int = 60,
        organizer: str = ""
    ) -> str:
        rooms = self._get_meeting_rooms()
        
        if query_type == "list":
            return json.dumps({
                "total": len(rooms),
                "rooms": rooms
            }, ensure_ascii=False, indent=2)
        
        elif query_type == "availability":
            available_rooms = [r for r in rooms if r["status"] == "空闲"]
            return json.dumps({
                "time": start_time or "当前",
                "available": len(available_rooms),
                "rooms": available_rooms
            }, ensure_ascii=False, indent=2)
        
        elif query_type == "book":
            booking_id = f"BK{datetime.now().strftime('%Y%m%d%H%M%S')}"
            return json.dumps({
                "status": "success",
                "booking_id": booking_id,
                "room": room_name,
                "time": start_time,
                "duration": f"{duration}分钟",
                "organizer": organizer,
                "message": f"预订成功！会议室：{room_name}，时间：{start_time}，时长：{duration}分钟"
            }, ensure_ascii=False, indent=2)
        
        else:
            return json.dumps({"error": "不支持的操作"}, ensure_ascii=False)


class EmployeeDirectoryInput(BaseModel):
    """员工通讯录查询输入"""
    query_type: str = Field(description="查询类型：find_person（查找员工）、find_department（查找部门）、call（呼叫）")
    keyword: str = Field(description="搜索关键词（姓名、部门、职位）", default="")


class EmployeeDirectoryTool(BaseTool):
    """员工通讯录工具"""
    
    name: str = "employee_directory"
    description: str = """
    员工通讯录和联系工具。
    
    功能：
    - find_person: 查找员工信息（姓名、部门、职位、联系方式）
    - find_department: 查找部门信息和成员
    - call: 呼叫/通知指定员工
    
    用于帮助访客找到联系人，或前台呼叫员工。
    """
    args_schema: Type[BaseModel] = EmployeeDirectoryInput
    
    def _get_employees(self):
        """获取员工数据"""
        return [
            {
                "id": "E001",
                "name": "张伟",
                "department": "技术部",
                "position": "技术总监",
                "extension": "8001",
                "email": "zhangwei@company.com",
                "status": "在岗"
            },
            {
                "id": "E002",
                "name": "李娜",
                "department": "人力资源部",
                "position": "HR经理",
                "extension": "8020",
                "email": "lina@company.com",
                "status": "在岗"
            },
            {
                "id": "E003",
                "name": "王明",
                "department": "技术部",
                "position": "高级工程师",
                "extension": "8005",
                "email": "wangming@company.com",
                "status": "会议中"
            }
        ]
    
    def _run(self, query_type: str, keyword: str = "") -> str:
        employees = self._get_employees()
        
        if query_type == "find_person":
            keyword_lower = keyword.lower()
            found = [
                e for e in employees
                if keyword_lower in e["name"].lower() or
                   keyword_lower in e["position"].lower()
            ]
            return json.dumps({
                "query": keyword,
                "found": len(found),
                "employees": found
            }, ensure_ascii=False, indent=2)
        
        elif query_type == "find_department":
            dept_employees = [e for e in employees if keyword in e["department"]]
            return json.dumps({
                "department": keyword,
                "members": len(dept_employees),
                "employees": dept_employees
            }, ensure_ascii=False, indent=2)
        
        elif query_type == "call":
            for emp in employees:
                if keyword in emp["name"]:
                    return json.dumps({
                        "status": "calling",
                        "employee": emp["name"],
                        "extension": emp["extension"],
                        "current_status": emp["status"],
                        "message": f"正在呼叫{emp['name']}（分机{emp['extension']}）..."
                    }, ensure_ascii=False, indent=2)
            return json.dumps({"error": f"未找到员工：{keyword}"}, ensure_ascii=False)
        
        return json.dumps({"error": "不支持的查询类型"}, ensure_ascii=False)


class DirectionGuideInput(BaseModel):
    """路线指引输入"""
    destination: str = Field(description="目的地（部门名称、会议室、设施等）")


class DirectionGuideTool(BaseTool):
    """路线指引工具"""
    
    name: str = "direction_guide"
    description: str = """
    办公室路线指引工具。
    
    提供：
    - 部门位置指引
    - 会议室位置
    - 设施位置（卫生间、电梯、停车场、餐厅等）
    - 详细的路线说明
    """
    args_schema: Type[BaseModel] = DirectionGuideInput
    
    def _get_location_map(self):
        """获取位置地图"""
        return {
            "技术部": {"floor": 3, "area": "东区", "room": "301-305", "direction": "乘电梯到3楼，右转直走到底"},
            "人力资源部": {"floor": 2, "area": "西区", "room": "208", "direction": "乘电梯到2楼，左转第三间"},
            "创新会议室": {"floor": 3, "area": "中区", "room": "MR001", "direction": "3楼电梯口正对面"},
            "大型会议室": {"floor": 5, "area": "中区", "room": "MR003", "direction": "5楼电梯口右手边"},
            "餐厅": {"floor": 1, "area": "南区", "room": "-", "direction": "一楼南侧，穿过大堂"},
            "停车场": {"floor": -1, "area": "地下", "room": "-", "direction": "乘电梯到B1层"},
        }
    
    def _run(self, destination: str) -> str:
        location_map = self._get_location_map()
        
        # 模糊匹配
        for key, info in location_map.items():
            if destination in key or key in destination:
                return json.dumps({
                    "destination": key,
                    "floor": info["floor"],
                    "area": info["area"],
                    "room": info["room"],
                    "direction": info["direction"],
                    "message": f"{key}位于{info['floor']}楼{info['area']}。{info['direction']}"
                }, ensure_ascii=False, indent=2)
        
        return json.dumps({
            "error": f"未找到'{destination}'的位置信息",
            "suggestion": "请提供更具体的目的地名称，如部门名称或会议室编号"
        }, ensure_ascii=False, indent=2)


class PackageManagementInput(BaseModel):
    """包裹管理输入"""
    operation: str = Field(description="操作类型：register（登记）、query（查询）、pickup（取件）")
    recipient: str = Field(description="收件人姓名", default="")
    tracking_number: str = Field(description="快递单号", default="")
    courier_company: str = Field(description="快递公司", default="")


class PackageManagementTool(BaseTool):
    """包裹/快递管理工具"""
    
    name: str = "package_management"
    description: str = """
    包裹和快递管理系统。
    
    功能：
    - register: 登记新到快递
    - query: 查询员工的快递
    - pickup: 记录快递取件
    
    帮助前台管理和通知快递信息。
    """
    args_schema: Type[BaseModel] = PackageManagementInput
    
    def _run(
        self,
        operation: str,
        recipient: str = "",
        tracking_number: str = "",
        courier_company: str = ""
    ) -> str:
        if operation == "register":
            package_id = f"PKG{datetime.now().strftime('%Y%m%d%H%M%S')}"
            return json.dumps({
                "status": "success",
                "package_id": package_id,
                "recipient": recipient,
                "tracking_number": tracking_number,
                "courier": courier_company,
                "arrival_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "storage_location": f"货架-{package_id[-4:]}",
                "message": f"快递已登记！收件人：{recipient}，存放位置：货架-{package_id[-4:]}。已发送通知。"
            }, ensure_ascii=False, indent=2)
        
        elif operation == "query":
            # 模拟查询结果
            return json.dumps({
                "recipient": recipient,
                "packages": [
                    {
                        "id": "PKG20251024143000",
                        "tracking": "SF1234567890",
                        "courier": "顺丰",
                        "arrival": "2025-10-24 14:30",
                        "status": "待取件"
                    }
                ],
                "total": 1
            }, ensure_ascii=False, indent=2)
        
        elif operation == "pickup":
            return json.dumps({
                "status": "success",
                "tracking_number": tracking_number,
                "recipient": recipient,
                "pickup_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "message": f"{recipient}已取件，单号：{tracking_number}"
            }, ensure_ascii=False, indent=2)
        
        return json.dumps({"error": "不支持的操作"}, ensure_ascii=False)


class FAQToolInput(BaseModel):
    """常见问题查询输入"""
    question: str = Field(description="用户的问题")


class FAQTool(BaseTool):
    """常见问题解答工具"""
    
    name: str = "faq_system"
    description: str = """
    常见问题解答系统（FAQ）。
    
    涵盖：
    - 公司基本信息（地址、营业时间、联系方式）
    - 访客须知（停车、WiFi、访客流程）
    - 会议室使用规则
    - 办公设施位置
    - 其他常见问题
    """
    args_schema: Type[BaseModel] = FAQToolInput
    
    def _get_faq_db(self):
        """获取FAQ数据库"""
        return {
            "WiFi": {
                "question": "WiFi密码是什么？",
                "answer": "访客WiFi：Guest-Network，密码：Welcome2024"
            },
            "停车": {
                "question": "停车怎么办理？",
                "answer": "访客可在前台登记车牌号，免费停车2小时。长时间停车请咨询前台。"
            },
            "营业时间": {
                "question": "公司营业时间？",
                "answer": "工作日：9:00-18:00，午休：12:00-13:00。周末和节假日休息。"
            },
            "餐厅": {
                "question": "公司有餐厅吗？",
                "answer": "一楼南侧有员工餐厅，营业时间：11:30-13:30。访客可使用，餐费20元/位。"
            },
            "会议室": {
                "question": "如何预订会议室？",
                "answer": "请联系行政部（分机8030）或通过OA系统预订。需提前24小时预约。"
            }
        }
    
    def _run(self, question: str) -> str:
        faq_db = self._get_faq_db()
        
        # 关键词匹配
        question_lower = question.lower()
        for key, item in faq_db.items():
            if key in question or key.lower() in question_lower:
                return json.dumps({
                    "question": item["question"],
                    "answer": item["answer"],
                    "category": key
                }, ensure_ascii=False, indent=2)
        
        # 没找到匹配
        return json.dumps({
            "status": "not_found",
            "message": "抱歉，没有找到相关问题的答案。您可以咨询前台工作人员获取帮助。",
            "available_topics": list(faq_db.keys())
        }, ensure_ascii=False, indent=2)


# 导出所有工具（方便导入）
__all__ = [
    # 基础工具
    'CalculatorTool',
    'TimeTool',
    'TextAnalysisTool',
    'UnitConversionTool',
    'ComparisonTool',
    'LogicReasoningTool',
    # 图书馆
    'LibraryManagementTool',
    # 对话管理
    'ConversationEndDetector',
    'WebSearchTool',
    'FileOperationTool',
    'ReminderTool',
    # 前台接待专用（新增）
    'VisitorRegistrationTool',
    'MeetingRoomTool',
    'EmployeeDirectoryTool',
    'DirectionGuideTool',
    'PackageManagementTool',
    'FAQTool',
]

