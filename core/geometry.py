import math
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Point:
    """2D空間上の座標とベクトル演算を定義するクラス"""
    x: float
    y: float

    def __add__(self, other: 'Point') -> 'Point':
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other: 'Point') -> 'Point':
        return Point(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> 'Point':
        return Point(self.x * scalar, self.y * scalar)

    def norm(self) -> float:
        """原点からの距離（ベクトルの長さ）を計算"""
        return math.hypot(self.x, self.y)

    def normalize(self) -> 'Point':
        """単位ベクトル化"""
        n = self.norm()
        return Point(self.x / n, self.y / n) if n > 0 else Point(0, 0)

    def dot(self, other: 'Point') -> float:
        """内積"""
        return self.x * other.x + self.y * other.y

    def cross(self, other: 'Point') -> float:
        """外積（2Dにおける回転方向の判定に使用）"""
        return self.x * other.y - self.y * other.x

    def to_tuple(self):
        return (self.x, self.y)
    
    def translate(self, dx: float, dy: float) -> 'Point':
        """平行移動"""
        return Point(self.x + dx, self.y + dy)

    def rotate(self, angle_rad: float, origin: 'Point' = None) -> 'Point':
        """指定した原点（デフォルトは0,0）を中心とした回転"""
        if origin is None:
            origin = Point(0, 0)
            
        # 原点への移動 -> 回転 -> 元の位置への移動
        qx = self.x - origin.x
        qy = self.y - origin.y
        
        rx = qx * math.cos(angle_rad) - qy * math.sin(angle_rad)
        ry = qx * math.sin(angle_rad) + qy * math.cos(angle_rad)
        
        return Point(rx + origin.x, ry + origin.y)


class GeometryEngine:
    """型紙生成のための幾何学計算ロジック"""

    @staticmethod
    def calculate_fillet(p1: Point, p0: Point, p2: Point, radius: float, resolution: int = 8) -> List[Point]:
        """
        頂点p0に半径radiusのフィレット（角R）を適用し、円弧の頂点リストを返す。
        resolution: 90度あたりの分割数。
        """
        if radius <= 0:
            return [p0]

        # ベクトル定義
        v1 = (p1 - p0).normalize()
        v2 = (p2 - p0).normalize()

        # ベクトルが同一直線上にある（または重なっている）場合の例外処理
        dot_val = max(-1.0, min(1.0, v1.dot(v2)))
        theta = math.acos(dot_val)
        
        if theta < 1e-6 or theta > math.pi - 1e-6:
            return [p0]

        # 半角
        alpha = theta / 2.0
        
        # p0から接点までの距離
        d = radius / math.tan(alpha)
        
        # 接点
        t1 = p0 + v1 * d
        t2 = p0 + v2 * d
        
        # 円弧の中心
        bisector = (v1 + v2).normalize()
        dist_to_center = radius / math.sin(alpha)
        center = p0 + bisector * dist_to_center
        
        # 円弧の描画範囲（角度）
        start_angle = math.atan2(t1.y - center.y, t1.x - center.x)
        end_angle = math.atan2(t2.y - center.y, t2.x - center.x)
        
        # 短い方の弧を選択
        sweep = end_angle - start_angle
        if sweep > math.pi: sweep -= 2 * math.pi
        if sweep < -math.pi: sweep += 2 * math.pi
        
        # 分割数の決定（角度に応じて調整）
        num_segments = max(2, int(abs(sweep) / (math.pi / 2) * resolution))
        
        arc_points = []
        for i in range(num_segments + 1):
            angle = start_angle + sweep * (i / num_segments)
            arc_points.append(Point(
                center.x + radius * math.cos(angle),
                center.y + radius * math.sin(angle)
            ))
            
        return arc_points

    @staticmethod
    def create_offset_polygon(vertices: List[Point], distance: float) -> List[Point]:
        """
        多角形を指定した距離だけ内側（または外側）にオフセットする（簡易版）。
        主にステッチラインの生成に使用。
        """
        # ※ 実装の簡略化のため、各辺の法線方向に移動させるロジック
        # 複雑な凹多角形の場合はMiter制限などの処理が必要だが、財布パーツならこれで十分対応可能
        new_vertices = []
        n = len(vertices)
        
        for i in range(n):
            curr = vertices[i]
            prev = vertices[(i - 1) % n]
            nxt = vertices[(i + 1) % n]
            
            # 各辺の単位ベクトル
            v_prev = (curr - prev).normalize()
            v_next = (nxt - curr).normalize()
            
            # 各辺の法線ベクトル（反時計回りを想定）
            n_prev = Point(-v_prev.y, v_prev.x)
            n_next = Point(-v_next.y, v_next.x)
            
            # 頂点における法線の合成
            bisector = (n_prev + n_next).normalize()
            # 内積で角の開き具合によるオフセット量の補正（Miter Length）
            cos_half_angle = bisector.dot(n_prev)
            if cos_half_angle == 0:
                offset_vec = bisector * distance
            else:
                offset_vec = bisector * (distance / cos_half_angle)
                
            new_vertices.append(curr + offset_vec)
            
        return new_vertices