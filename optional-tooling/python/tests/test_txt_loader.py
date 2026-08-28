"""
测试 TXT 加载器
"""

import pytest
import tempfile
import os
from novel_distiller.loaders import TxtLoader


def test_txt_loader_basic():
    """测试基本文件加载"""
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False, suffix=".txt") as f:
        f.write("这是测试内容\n第二行\n第三行")
        temp_path = f.name
    
    try:
        loader = TxtLoader()
        content = loader.load(temp_path)
        
        assert "这是测试内容" in content
        assert "第二行" in content
    finally:
        os.unlink(temp_path)


def test_txt_loader_not_found():
    """测试文件不存在的情况"""
    loader = TxtLoader()
    
    with pytest.raises(FileNotFoundError):
        loader.load("nonexistent_file.txt")


def test_txt_loader_lines():
    """测试按行加载"""
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False, suffix=".txt") as f:
        f.write("第一行\n第二行\n第三行")
        temp_path = f.name
    
    try:
        loader = TxtLoader()
        lines = loader.load_lines(temp_path)
        
        assert len(lines) == 3
        assert lines[0] == "第一行"
        assert lines[2] == "第三行"
    finally:
        os.unlink(temp_path)


def test_txt_loader_stats():
    """测试文件统计"""
    content = "测试内容" * 100
    
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False, suffix=".txt") as f:
        f.write(content)
        temp_path = f.name
    
    try:
        loader = TxtLoader()
        stats = loader.get_file_stats(temp_path)
        
        assert stats["total_words"] == 400  # 4字 * 100次
        assert stats["file_size"] > 0
    finally:
        os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
