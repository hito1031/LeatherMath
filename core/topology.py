from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional
from .geometry import Point
import math

@dataclass
class StitchParams:
    """縫い目の仕様を定義"""
    pitch: float = 4.0      # 穴の間隔 (mm)
    offset: float = 3.0     # 縁からの距離 (mm)
    start_margin: float = 2.0 # 辺の始点からのマージン

@dataclass
class Edge:
    """パーツの特定の「辺」を管理するクラス"""
    parent_part_id: str
    edge_id: str
    points: List[Point]  # 辺を構成する頂点リスト
    
    @property
    def length(self) -> float:
        """辺の総延長を計算"""
        total = 0.0
        for i in range(len(self.points) - 1):
            total += (self.points[i+1] - self.points[i]).norm()
        return total

    def calculate_stitch_count(self, params: StitchParams) -> int:
        """この辺に配置される菱目の穴数を算出"""
        effective_length = self.length - (params.start_margin * 2)
        if effective_length <= 0:
            return 0
        return math.floor(effective_length / params.pitch) + 1

class TopologyManager:
    """パーツ間の接続関係と整合性を管理するクラス"""
    
    def __init__(self):
        # 接続定義: {(part_a, edge_a): (part_b, edge_b)}
        self.connections: Dict[Tuple[str, str], Tuple[str, str]] = {}
        # 登録された全エッジ
        self.edges: Dict[Tuple[str, str], Edge] = {}

    def register_edge(self, edge: Edge):
        """エッジをシステムに登録"""
        self.edges[(edge.parent_part_id, edge.edge_id)] = edge

    def add_seam(self, part_a: str, edge_a: str, part_b: str, edge_b: str):
        """2つのパーツの辺を縫い合わせる（シーム）として定義"""
        self.connections[(part_a, edge_a)] = (part_b, edge_b)

    def validate_all(self, params: StitchParams, tolerance: float = 0.5) -> List[str]:
        """
        全接続箇所の整合性を検証し、エラーメッセージのリストを返す。
        """
        errors = []
        
        for (p_a, e_a), (p_b, e_b) in self.connections.items():
            edge_a = self.edges.get((p_a, e_a))
            edge_b = self.edges.get((p_b, e_b))
            
            if not edge_a or not edge_b:
                errors.append(f"Missing edge definition: {p_a}.{e_a} or {p_b}.{e_b}")
                continue

            # 1. 長さの検証
            diff = abs(edge_a.length - edge_b.length)
            if diff > tolerance:
                errors.append(
                    f"Length mismatch: {p_a}.{e_a}({edge_a.length:.2f}mm) "
                    f"vs {p_b}.{e_b}({edge_b.length:.2f}mm). Diff: {diff:.2f}mm"
                )

            # 2. 穴数の検証
            count_a = edge_a.calculate_stitch_count(params)
            count_b = edge_b.calculate_stitch_count(params)
            if count_a != count_b:
                errors.append(
                    f"Stitch count mismatch: {p_a}.{e_a}({count_a} holes) "
                    f"vs {p_b}.{e_b}({count_b} holes)"
                )
                
        return errors