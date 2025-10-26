"""计算器工具"""
from pydantic import BaseModel, Field
from typing import Type
import math

from src.core.tools.base import BaseTool


class CalculatorInput(BaseModel):
    """计算器工具输入"""
    expression: str = Field(description="数学表达式,支持基本运算和函数如sqrt、sin、cos等")


class CalculatorTool(BaseTool):
    """数学计算工具 - 支持各种数学运算"""

    name: str = "calculator"
    description: str = """
    数学计算工具。用于计算数学表达式。
    支持:
    - 基本运算: +、-、*、/、**(幂运算)
    - 函数: sqrt(平方根)、sin、cos、tan、log、exp
    - 常数: pi、e
    - 函数: round(四舍五入)、abs(绝对值)

    示例:
    - "sqrt(2)" → 1.414...
    - "round(sqrt(2), 3)" → 1.414
    - "sin(pi/2)" → 1.0
    """
    args_schema: Type[BaseModel] = CalculatorInput
    category: str = "basic"

    def execute(self, expression: str) -> str:
        """执行计算"""
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


__all__ = ['CalculatorTool']
