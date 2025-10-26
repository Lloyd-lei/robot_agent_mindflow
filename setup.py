"""
Setup script for robot_agent_mindflow package
"""
from setuptools import setup, find_packages
from pathlib import Path

# 读取 README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# 读取 requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    requirements = [
        line.strip()
        for line in requirements_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="robot_agent_mindflow",
    version="0.2.0",
    description="混合架构AI Agent - OpenAI原生 + LangChain工具池 + KV Cache优化",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/Lloyd-lei/robot_agent_mindflow",
    packages=find_packages(include=["src", "src.*"]),
    install_requires=requirements,
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords="ai agent openai langchain tts voice llm",
    project_urls={
        "Documentation": "https://github.com/Lloyd-lei/robot_agent_mindflow/tree/main/docs",
        "Source": "https://github.com/Lloyd-lei/robot_agent_mindflow",
        "Tracker": "https://github.com/Lloyd-lei/robot_agent_mindflow/issues",
    },
)
