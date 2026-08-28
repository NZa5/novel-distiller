"""
TXT 文件加载器
"""

import os
from typing import List


class TxtLoader:
    """TXT 文件加载器"""
    
    def __init__(self, encoding: str = "utf-8"):
        """
        初始化加载器
        
        Args:
            encoding: 文件编码
        """
        self.encoding = encoding
    
    def load(self, file_path: str) -> str:
        """
        加载 TXT 文件
        
        Args:
            file_path: 文件路径
        
        Returns:
            文件内容
        
        Raises:
            FileNotFoundError: 文件不存在
            UnicodeDecodeError: 编码错误
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        try:
            with open(file_path, "r", encoding=self.encoding) as f:
                content = f.read()
            return content
        except UnicodeDecodeError:
            # 尝试其他常见编码
            for enc in ["gbk", "gb2312", "big5"]:
                try:
                    with open(file_path, "r", encoding=enc) as f:
                        content = f.read()
                    return content
                except UnicodeDecodeError:
                    continue
            
            raise UnicodeDecodeError(
                self.encoding,
                b"",
                0,
                0,
                f"无法解码文件，请确保文件编码为 UTF-8、GBK 或 GB2312"
            )
    
    def load_lines(self, file_path: str) -> List[str]:
        """
        按行加载文件
        
        Args:
            file_path: 文件路径
        
        Returns:
            行列表
        """
        content = self.load(file_path)
        return content.splitlines()
    
    def get_file_stats(self, file_path: str) -> dict:
        """
        获取文件统计信息
        
        Args:
            file_path: 文件路径
        
        Returns:
            统计信息字典
        """
        content = self.load(file_path)
        lines = content.splitlines()
        
        return {
            "file_size": os.path.getsize(file_path),
            "total_lines": len(lines),
            "total_chars": len(content),
            "total_words": len(content.replace("\n", "").replace(" ", "")),
        }
