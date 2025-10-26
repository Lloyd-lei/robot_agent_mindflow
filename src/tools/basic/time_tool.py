"""时间工具"""
from pydantic import BaseModel, Field
from typing import Type
from datetime import datetime

from src.core.tools.base import BaseTool


class TimeToolInput(BaseModel):
    """时间工具输入"""
    query_type: str = Field(
        description="查询类型: current_time(当前时间)、current_date(日期)、weekday(星期)、full(完整信息)"
    )


class TimeTool(BaseTool):
    """时间日期工具"""

    name: str = "time_tool"
    description: str = """
    获取当前时间和日期信息。
    支持的查询类型:
    - current_time: 当前时间(时:分:秒)
    - current_date: 当前日期(年-月-日)
    - weekday: 星期几
    - full: 完整的日期时间信息
    """
    args_schema: Type[BaseModel] = TimeToolInput
    category: str = "basic"

    def execute(self, query_type: str) -> str:
        """执行时间查询"""
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


__all__ = ['TimeTool']
