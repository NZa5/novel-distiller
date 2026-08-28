"""
人物关系可视化 (Phase 2)
"""

import os
from typing import List, Optional
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib import font_manager
import json

from ..models.schemas import CharacterRelation, Character


class RelationshipVisualizer:
    """人物关系可视化器"""
    
    def __init__(self):
        """初始化可视化器"""
        # 设置中文字体
        self._setup_chinese_font()
    
    def _setup_chinese_font(self):
        """设置中文字体支持"""
        try:
            # 尝试使用系统中文字体
            fonts = ['SimHei', 'Microsoft YaHei', 'PingFang SC', 'STHeiti', 'Arial Unicode MS']
            for font in fonts:
                try:
                    plt.rcParams['font.sans-serif'] = [font]
                    plt.rcParams['axes.unicode_minus'] = False
                    break
                except:
                    continue
        except Exception:
            pass
    
    def build_graph(
        self,
        relations: List[CharacterRelation],
        characters: Optional[List[Character]] = None
    ) -> nx.Graph:
        """
        构建 NetworkX 图
        
        Args:
            relations: 关系列表
            characters: 人物列表（可选，用于添加人物属性）
        
        Returns:
            NetworkX Graph 对象
        """
        G = nx.Graph()
        
        # 添加人物节点
        if characters:
            for char in characters:
                G.add_node(
                    char.name,
                    role=char.role.value,
                    description=char.description[:50] if char.description else ""
                )
        
        # 添加关系边
        for rel in relations:
            G.add_edge(
                rel.source,
                rel.target,
                relation_type=rel.relation_type,
                description=rel.description,
                strength=rel.strength,
                chapters=len(rel.chapters)
            )
        
        return G
    
    def visualize(
        self,
        relations: List[CharacterRelation],
        characters: Optional[List[Character]] = None,
        output_path: str = "relationship_graph.png",
        figsize: tuple = (12, 10)
    ):
        """
        生成人物关系图
        
        Args:
            relations: 关系列表
            characters: 人物列表
            output_path: 输出文件路径
            figsize: 图片尺寸
        """
        if not relations:
            print("没有人物关系，跳过可视化")
            return
        
        # 构建图
        G = self.build_graph(relations, characters)
        
        # 创建画布
        plt.figure(figsize=figsize)
        
        # 使用 spring layout
        pos = nx.spring_layout(G, k=2, iterations=50)
        
        # 根据角色类型设置节点颜色
        node_colors = []
        if characters:
            char_roles = {char.name: char.role.value for char in characters}
            color_map = {
                'protagonist': '#FF6B6B',  # 红色 - 主角
                'major': '#4ECDC4',        # 青色 - 主要配角
                'minor': '#95E1D3',        # 淡青 - 次要配角
                'villain': '#9B59B6',      # 紫色 - 反派
                'supporting': '#BDC3C7'   # 灰色 - 配角
            }
            for node in G.nodes():
                role = char_roles.get(node, 'supporting')
                node_colors.append(color_map.get(role, '#BDC3C7'))
        else:
            node_colors = ['#4ECDC4'] * len(G.nodes())
        
        # 绘制节点
        nx.draw_networkx_nodes(
            G, pos,
            node_color=node_colors,
            node_size=1000,
            alpha=0.9
        )
        
        # 绘制边，根据关系强度设置宽度
        edge_widths = [G[u][v].get('strength', 0.5) * 3 for u, v in G.edges()]
        nx.draw_networkx_edges(
            G, pos,
            width=edge_widths,
            alpha=0.5,
            edge_color='gray'
        )
        
        # 绘制标签
        nx.draw_networkx_labels(
            G, pos,
            font_size=10,
            font_weight='bold'
        )
        
        # 添加边标签（关系类型）
        edge_labels = {
            (u, v): G[u][v].get('relation_type', '')
            for u, v in G.edges()
        }
        nx.draw_networkx_edge_labels(
            G, pos,
            edge_labels,
            font_size=8
        )
        
        plt.title("人物关系图谱", fontsize=16, fontweight='bold')
        plt.axis('off')
        plt.tight_layout()
        
        # 保存图片
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ 关系图谱已保存到: {output_path}")
    
    def export_graph_data(
        self,
        relations: List[CharacterRelation],
        characters: Optional[List[Character]] = None,
        output_dir: str = "output"
    ):
        """
        导出图数据
        
        Args:
            relations: 关系列表
            characters: 人物列表
            output_dir: 输出目录
        """
        G = self.build_graph(relations, characters)
        
        os.makedirs(output_dir, exist_ok=True)
        
        # 导出 GraphML 格式（可被 Gephi 等工具读取）
        graphml_path = os.path.join(output_dir, "relationship_graph.graphml")
        nx.write_graphml(G, graphml_path)
        
        # 导出 JSON 格式（便于前端可视化）
        json_data = {
            "nodes": [
                {
                    "id": node,
                    "label": node,
                    **G.nodes[node]
                }
                for node in G.nodes()
            ],
            "edges": [
                {
                    "source": u,
                    "target": v,
                    **G[u][v]
                }
                for u, v in G.edges()
            ]
        }
        
        json_path = os.path.join(output_dir, "relationship_graph.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        return {
            "graphml": graphml_path,
            "json": json_path
        }
    
    def get_graph_statistics(
        self,
        relations: List[CharacterRelation],
        characters: Optional[List[Character]] = None
    ) -> dict:
        """
        获取图统计信息
        
        Args:
            relations: 关系列表
            characters: 人物列表
        
        Returns:
            统计信息字典
        """
        G = self.build_graph(relations, characters)
        
        stats = {
            "nodes": G.number_of_nodes(),
            "edges": G.number_of_edges(),
            "density": nx.density(G),
            "avg_degree": sum(dict(G.degree()).values()) / G.number_of_nodes() if G.number_of_nodes() > 0 else 0
        }
        
        # 中心性分析
        if G.number_of_nodes() > 0:
            degree_centrality = nx.degree_centrality(G)
            stats["most_central"] = sorted(
                degree_centrality.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        
        return stats
