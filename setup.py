from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="novel-distiller",
    version="0.2.0",
    author="Novel Distiller Team",
    description="从小说中提取和分析核心信息的 AI Skill",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/novel-distiller",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Text Processing :: Linguistic",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
    install_requires=[
        "langchain>=0.1.0",
        "langchain-openai>=0.0.5",
        "openai>=1.0.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "tiktoken>=0.5.0",
        "ebooklib>=0.18",
        "beautifulsoup4>=4.12.0",
        "jieba>=0.42.1",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "novel-distiller=novel_distiller.__main__:main",
        ],
    },
)
