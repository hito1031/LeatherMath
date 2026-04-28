from dataclasses import dataclass
from typing import List, Dict, Optional
from .geometry import Point, GeometryEngine
from .material import Leather, BendCalculator

# --- 1. データの入力定義（UIから受け取るマニフェストの型） ---

@dataclass
class PartBlueprint:
    """UI側で定義された各パーツの基本仕様（理想の寸法）"""
    part_id: str
    part_type: str            # 'inner_shell', 'outer_shell', 'card_slot' など
    width: float              # 基準となる幅 (mm)
    height: float             # 基準となる高さ (mm)
    leather: Leather
    parent_id: Optional[str] = None  # どのパーツの上に重なっているか
    fold_angle: float = 0.0   # このパーツが何度曲がるか（例: 財布なら180度）
    anchor_x: float = 0.0
    anchor_y: float = 0.0
    rotation_deg: float = 0.0

@dataclass
class CompiledPart:
    """エンジンが計算し終わった出力データ（2D型紙データ）"""
    part_id: str
    vertices: List[Point]     # 外形線の頂点リスト
    stitch_lines: List[List[Point]] # 縫い目ラインの頂点リスト（今回は省略可）

# --- 2. 計算エンジン本体 ---

class PatternEngine:
    """3Dの設計図から2Dの型紙を生成するコンパイラ"""
    
    def __init__(self, blueprints: List[PartBlueprint], fold_radius: float = 2.0):
        self.blueprints = {bp.part_id: bp for bp in blueprints}
        self.fold_radius = fold_radius # 財布を曲げた時の基準となる内側の空間R
        self.compiled_parts: Dict[str, CompiledPart] = {}

    def _calculate_stack_thickness(self, target_part_id: str) -> float:
        """
        [簡略版 constraints.py の役割]
        指定されたパーツの「内側」にどれだけの厚みの革が積層されているかを計算する。
        """
        thickness = 0.0
        target_bp = self.blueprints[target_part_id]
        
        # 自身より内側（親）にあるパーツの厚みを全て足し合わせる
        current_parent = target_bp.parent_id
        while current_parent:
            parent_bp = self.blueprints[current_parent]
            thickness += parent_bp.leather.thickness
            current_parent = parent_bp.parent_id
            
        return thickness

    def compile(self) -> List[CompiledPart]:
        """全パーツの物理補正を行い、2D頂点を生成する"""
        results = []
        
        for bp in self.blueprints.values():
            # 1. 物理補正（曲げに伴う寸法の伸びを計算）
            final_width = bp.width
            final_height = bp.height
            
            if bp.fold_angle > 0:
                # このパーツの内側に積層されている革の合計厚みを算出
                inner_thickness = self._calculate_stack_thickness(bp.part_id)
                
                # 自分自身の曲げ半径 = 基準R + 内側の積層厚
                my_radius = self.fold_radius + inner_thickness
                
                # 展開長（Bend Allowance）を計算
                # ※ここでは幅方向（X軸）に曲げると仮定
                bend_allowance = BendCalculator.calculate_bend_allowance(
                    radius=my_radius,
                    thickness=bp.leather.thickness,
                    k_factor=bp.leather.k_factor,
                    angle_deg=bp.fold_angle
                )
                
                # 元の直線長さに、曲げ部分の展開長を差し替えて幅を補正
                # （※簡略化のため、元の幅から曲げ部分の直線距離を引いてBAを足す計算をイメージ）
                # 今回は純粋に「外側に行くほど長くなる」差分ΔLを加算する形に単純化します
                delta_l = BendCalculator.get_outer_offset(inner_thickness, bp.leather.k_factor)
                final_width += delta_l

            # 2. 幾何学生成（確定した寸法からPolygonを作る）
            # ※ 本来は parts/wallets.py の関数を呼ぶが、ここでは直接矩形を生成
            p1 = Point(0, 0)
            p2 = Point(final_width, 0)
            p3 = Point(final_width, final_height)
            p4 = Point(0, final_height)
            
            # 角R（フィレット）を適用（例として全パーツに 3.0mm のRをつける）
            vertices = []
            vertices.extend(GeometryEngine.calculate_fillet(p4, p1, p2, 3.0))
            vertices.extend(GeometryEngine.calculate_fillet(p1, p2, p3, 3.0))
            vertices.extend(GeometryEngine.calculate_fillet(p2, p3, p4, 3.0))
            vertices.extend(GeometryEngine.calculate_fillet(p3, p4, p1, 3.0))
            
            # コンパイル結果として保存
            compiled = CompiledPart(part_id=bp.part_id, vertices=vertices, stitch_lines=[])
            results.append(compiled)
            self.compiled_parts[bp.part_id] = compiled
            
        return results