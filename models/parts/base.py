import math
from abc import ABC, abstractmethod
from typing import List, Optional

# ※ 前のステップで作成したクラスをインポートしている前提です
from core.geometry import Point
from core.topology import Edge

class PartBase(ABC):
    """
    すべてのレザークラフト用パーツの基底クラス。
    各パーツの「ローカル座標での形状生成」を強制し、「グローバル座標への変換」を自動化する。
    """
    
    def __init__(self, 
                 part_id: str, 
                 parent_id: Optional[str] = None,
                 anchor_x: float = 0.0,    # 親パーツ上のX配置座標
                 anchor_y: float = 0.0,    # 親パーツ上のY配置座標
                 rotation_deg: float = 0.0): # 親パーツに対する回転角度
        
        self.part_id = part_id
        self.parent_id = parent_id
        self.anchor_x = anchor_x
        self.anchor_y = anchor_y
        self.rotation_rad = math.radians(rotation_deg)

    # ---------------------------------------------------------
    # 子クラス（具体的なパーツ）が必ず実装しなければならないメソッド
    # ---------------------------------------------------------

    @abstractmethod
    def _generate_local_polygon(self) -> List[Point]:
        """
        パーツ単体の形状を、左下(0,0)を基準としたローカル座標系で生成する。
        （引数の種類は子クラスごとに自由で構わない）
        """
        pass

    @abstractmethod
    def _define_edges(self) -> List[Edge]:
        """
        縫い合わせの対象となる「辺」をローカル座標系で定義する。
        """
        pass

    # ---------------------------------------------------------
    # 基底クラスが提供する共通機能（座標変換）
    # ---------------------------------------------------------

    def _transform_point(self, pt: Point) -> Point:
        """
        ローカル座標の点を、回転と平行移動を加えてグローバル座標（親の空間）に変換する。
        """
        # 1. 原点(0,0)を中心とした回転
        rotated_x = pt.x * math.cos(self.rotation_rad) - pt.y * math.sin(self.rotation_rad)
        rotated_y = pt.x * math.sin(self.rotation_rad) + pt.y * math.cos(self.rotation_rad)
        
        # 2. アンカーポイントへの平行移動
        global_x = rotated_x + self.anchor_x
        global_y = rotated_y + self.anchor_y
        
        return Point(global_x, global_y)

    def get_global_polygon(self) -> List[Point]:
        """
        計算エンジンが呼び出すメソッド。
        ローカル形状を生成し、配置位置に合わせて変換した頂点リストを返す。
        """
        local_points = self._generate_local_polygon()
        return [self._transform_point(pt) for pt in local_points]

    def get_global_edges(self) -> List[Edge]:
        """
        トポロジー層が呼び出すメソッド。
        辺の座標もグローバル空間に変換して返す。
        """
        local_edges = self._define_edges()
        global_edges = []
        for edge in local_edges:
            global_points = [self._transform_point(pt) for pt in edge.points]
            global_edges.append(Edge(
                parent_part_id=self.part_id,
                edge_id=edge.edge_id,
                points=global_points
            ))
        return global_edges