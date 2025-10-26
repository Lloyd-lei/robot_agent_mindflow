"""
工具注册表 - 管理所有可用工具

使用方式:
    from src.core.tools.registry import tool_registry

    # 注册工具
    tool_registry.register(MyTool())

    # 获取工具
    tool = tool_registry.get('my_tool')

    # 获取所有工具
    all_tools = tool_registry.get_all()
"""
from typing import Dict, List, Optional
from src.core.tools.base import BaseTool, ToolMetadata


class ToolRegistry:
    """工具注册表 - 单例模式"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools: Dict[str, BaseTool] = {}
            cls._instance._categories: Dict[str, List[str]] = {}
        return cls._instance

    def register(self, tool: BaseTool) -> None:
        """
        注册工具

        Args:
            tool: 工具实例
        """
        tool_name = tool.name

        if tool_name in self._tools:
            print(f"⚠️  工具 '{tool_name}' 已存在,将被覆盖")

        self._tools[tool_name] = tool

        # 按类别索引
        category = tool.category
        if category not in self._categories:
            self._categories[category] = []
        if tool_name not in self._categories[category]:
            self._categories[category].append(tool_name)

        print(f"✅ 注册工具: {tool_name} (类别: {category})")

    def register_batch(self, tools: List[BaseTool]) -> None:
        """批量注册工具"""
        for tool in tools:
            self.register(tool)

    def get(self, tool_name: str) -> Optional[BaseTool]:
        """
        获取工具

        Args:
            tool_name: 工具名称

        Returns:
            工具实例,不存在则返回 None
        """
        return self._tools.get(tool_name)

    def get_all(self) -> List[BaseTool]:
        """获取所有工具"""
        return list(self._tools.values())

    def get_by_category(self, category: str) -> List[BaseTool]:
        """
        根据类别获取工具

        Args:
            category: 工具类别(basic/reception/system)

        Returns:
            该类别下的所有工具
        """
        tool_names = self._categories.get(category, [])
        return [self._tools[name] for name in tool_names if name in self._tools]

    def get_metadata_all(self) -> List[ToolMetadata]:
        """获取所有工具的元数据"""
        return [tool.get_metadata() for tool in self._tools.values()]

    def list_tools(self) -> None:
        """打印所有工具列表"""
        print(f"\n{'='*70}")
        print(f"📦 已注册工具: {len(self._tools)} 个")
        print(f"{'='*70}\n")

        for category, tool_names in self._categories.items():
            print(f"📁 {category.upper()} ({len(tool_names)}个)")
            for name in tool_names:
                tool = self._tools[name]
                print(f"   - {name}: {tool.description[:50]}...")
            print()

    def clear(self) -> None:
        """清空注册表"""
        self._tools.clear()
        self._categories.clear()
        print("🗑️  工具注册表已清空")

    def unregister(self, tool_name: str) -> bool:
        """
        注销工具

        Args:
            tool_name: 工具名称

        Returns:
            是否成功注销
        """
        if tool_name in self._tools:
            tool = self._tools[tool_name]
            category = tool.category

            # 从工具字典中删除
            del self._tools[tool_name]

            # 从类别索引中删除
            if category in self._categories:
                self._categories[category].remove(tool_name)
                if not self._categories[category]:
                    del self._categories[category]

            print(f"✅ 已注销工具: {tool_name}")
            return True

        print(f"⚠️  工具 '{tool_name}' 不存在")
        return False


# 创建全局注册表实例
tool_registry = ToolRegistry()


# 导出
__all__ = ['ToolRegistry', 'tool_registry']
