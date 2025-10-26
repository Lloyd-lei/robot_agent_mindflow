"""
工具加载器 - 从旧代码加载所有工具

这是一个过渡性的加载器,用于从旧的 tools.py 文件加载工具
将来可以逐步迁移到新的模块化结构
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 从旧的 tools.py 导入所有工具
try:
    from tools import (
        # 基础工具
        CalculatorTool,
        TimeTool,
        TextAnalysisTool,
        UnitConversionTool,
        ComparisonTool,
        LogicReasoningTool,
        # 图书馆
        LibraryManagementTool,
        # 对话管理
        ConversationEndDetector,
        WebSearchTool,
        FileOperationTool,
        ReminderTool,
        # 前台接待
        VisitorRegistrationTool,
        MeetingRoomTool,
        EmployeeDirectoryTool,
        DirectionGuideTool,
        PackageManagementTool,
        FAQTool,
    )

    def load_all_tools():
        """加载所有工具"""
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

    print("✅ 工具加载器: 从旧代码成功导入所有工具")

except ImportError as e:
    print(f"⚠️  警告: 无法从旧代码导入工具: {e}")
    print("提示: 请确保项目根目录的 tools.py 文件存在")

    def load_all_tools():
        """降级: 返回空列表"""
        return []


__all__ = ['load_all_tools']
