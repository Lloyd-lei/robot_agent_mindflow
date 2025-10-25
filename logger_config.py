"""
日志配置模块

统一管理项目中的所有日志输出
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from colorama import Fore, Style


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器"""
    
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT,
    }
    
    def format(self, record):
        # 添加颜色
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{Style.RESET_ALL}"
        
        return super().format(record)


def setup_logger(
    name: str = "agent_mvp",
    level: int = logging.INFO,
    log_to_file: bool = True,
    log_dir: str = "logs"
) -> logging.Logger:
    """
    配置日志系统
    
    参数：
    - name: 日志名称
    - level: 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
    - log_to_file: 是否输出到文件
    - log_dir: 日志文件目录
    
    返回：
    - Logger 对象
    """
    
    # 创建 logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重复添加 handler
    if logger.handlers:
        return logger
    
    # === 控制台 Handler（彩色） ===
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # 彩色格式
    console_formatter = ColoredFormatter(
        fmt='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # === 文件 Handler（完整日志） ===
    if log_to_file:
        # 创建日志目录
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True)
        
        # 按日期命名日志文件
        log_filename = log_path / f"agent_{datetime.now().strftime('%Y%m%d')}.log"
        
        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # 文件记录所有级别
        
        # 完整格式
        file_formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    获取 logger（便捷函数）
    
    参数：
    - name: logger 名称（默认为调用模块名）
    
    返回：
    - Logger 对象
    """
    if name is None:
        # 自动获取调用者的模块名
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals['__name__']
    
    return logging.getLogger(name)


# 创建默认 logger
default_logger = setup_logger()


if __name__ == "__main__":
    # 测试日志系统
    logger = setup_logger("test", level=logging.DEBUG)
    
    logger.debug("🔍 这是 DEBUG 消息")
    logger.info("✅ 这是 INFO 消息")
    logger.warning("⚠️  这是 WARNING 消息")
    logger.error("❌ 这是 ERROR 消息")
    logger.critical("💀 这是 CRITICAL 消息")
    
    print(f"\n日志文件已保存到: logs/")

