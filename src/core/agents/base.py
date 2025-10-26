"""
Agent 抽象基类 - 定义统一的 Agent 接口
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class AgentResponse:
    """Agent 响应结果"""
    success: bool
    output: str
    reasoning_steps: List[Dict] = None
    tool_calls: int = 0
    metadata: Dict[str, Any] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.reasoning_steps is None:
            self.reasoning_steps = []
        if self.metadata is None:
            self.metadata = {}


class BaseAgent(ABC):
    """
    Agent 抽象基类

    所有 Agent 必须实现:
    - run(): 执行推理
    - clear_history(): 清除历史
    """

    def __init__(self, name: str = "BaseAgent"):
        self.name = name
        self.conversation_history = []

    @abstractmethod
    def run(self, user_input: str, **kwargs) -> AgentResponse:
        """
        执行推理

        Args:
            user_input: 用户输入
            **kwargs: 其他参数

        Returns:
            AgentResponse: 响应结果
        """
        pass

    @abstractmethod
    def clear_history(self) -> None:
        """清除对话历史"""
        pass

    def get_history(self) -> List[Dict]:
        """获取对话历史"""
        return self.conversation_history.copy()

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计数据字典
        """
        return {
            'agent_name': self.name,
            'conversation_turns': len(self.conversation_history) // 2,
            'total_messages': len(self.conversation_history)
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name}>"


# 导出
__all__ = ['BaseAgent', 'AgentResponse']
