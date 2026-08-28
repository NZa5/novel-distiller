"""Packaging metadata for the optional local Python tooling."""
from pathlib import Path

from setuptools import find_packages, setup


ROOT = Path(__file__).parent
VERSION = "0.2.0"

setup(
    name="novel-distiller",
    version=VERSION,
    author="Novel Distiller Team",
    description="Optional local tooling for the Novel Distiller cross-agent Skill",
    long_description=(ROOT / "README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "langchain>=0.1.0",
        "langchain-openai>=0.0.5",
        "openai>=1.0.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "tiktoken>=0.5.0",
        "networkx>=3.0",
        "matplotlib>=3.5.0",
        "ebooklib>=0.18",
        "beautifulsoup4>=4.12.0",
        "jieba>=0.42.1",
    ],
    entry_points={"console_scripts": ["novel-distiller=novel_distiller.__main__:main"]},
)
