"""
工具基类 - 统一的工具接口

所有工具必须继承 BaseTool (LangChain)
"""
from langchain.tools import BaseTool as LangChainBaseTool
from pydantic import BaseModel
from typing import Type, Optional, Dict, Any
from abc import abstractmethod


class ToolMetadata(BaseModel):
    """工具元数据"""
    name: str
    description: str
    category: str  # basic, reception, system
    version: str = "1.0.0"
    author: Optional[str] = None
    tags: list[str] = []


class BaseTool(LangChainBaseTool):
    """
    工具抽象基类

    继承自 LangChain BaseTool,扩展了元数据和生命周期管理

    使用示例:
        class MyTool(BaseTool):
            name = "my_tool"
            description = "我的工具"

            def _run(self, **kwargs):
                return "result"
    """

    # 元数据(子类需要设置) - 注意: LangChain BaseTool 已定义了 name 和 description
    category: str = "basic"  # 类型注解
    version: str = "1.0.0"    # 类型注解

    def get_metadata(self) -> ToolMetadata:
        """获取工具元数据"""
        return ToolMetadata(
            name=self.name,
            description=self.description,
            category=self.category,
            version=self.version
        )

    def before_run(self, **kwargs) -> Dict[str, Any]:
        """
        执行前钩子

        可用于:
        - 参数验证
        - 日志记录
        - 权限检查

        Returns:
            处理后的参数字典
        """
        return kwargs

    def after_run(self, result: Any) -> Any:
        """
        执行后钩子

        可用于:
        - 结果格式化
        - 日志记录
        - 错误处理

        Returns:
            处理后的结果
        """
        return result

    def _run(self, **kwargs) -> str:
        """
        工具执行方法(子类必须实现)

        Returns:
            字符串格式的执行结果
        """
        # 执行前钩子
        kwargs = self.before_run(**kwargs)

        # 实际执行
        try:
            result = self.execute(**kwargs)
        except Exception as e:
            result = self.handle_error(e, **kwargs)

        # 执行后钩子
        result = self.after_run(result)

        return str(result)

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """
        实际执行逻辑(子类必须实现)

        这个方法包含工具的核心逻辑
        """
        pass

    def handle_error(self, error: Exception, **kwargs) -> str:
        """
        错误处理

        Args:
            error: 异常对象
            **kwargs: 执行参数

        Returns:
            错误信息字符串
        """
        error_msg = f"[{self.name}] 执行错误: {str(error)}"
        print(f"⚠️  {error_msg}")
        return error_msg


# 导出
__all__ = ['BaseTool', 'ToolMetadata']
