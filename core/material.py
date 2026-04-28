from dataclasses import dataclass
import math
from typing import Literal

@dataclass
class Leather:
    """
    革の物理特性を保持するクラス
    """
    thickness: float  # 厚み (mm)
    name: str = "Default Leather"
    
    # 柔軟性 (0.0: 非常に硬い 〜 1.0: 非常に柔らかい)
    # これにより K-factor を簡易的に自動調整する
    softness: float = 0.5

    @property
    def k_factor(self) -> float:
        """
        中立軸の係数。
        柔らかいほど内側に潰れるため、中立軸は内側（0.5未満）に寄ると定義する。
        """
        # 実務的な近似値: 0.3 (柔らかい) 〜 0.5 (硬い) の範囲で変化
        return 0.5 - (self.softness * 0.2)

@dataclass
class Material:
    """すべての素材の基底クラス"""
    thickness: float
    name: str
    material_type: Literal['leather', 'textile', 'hardware', 'stiffener'] = 'leather'

@dataclass
class Leather(Material):
    softness: float = 0.5
    
    @property
    def k_factor(self) -> float:
        return 0.5 - (self.softness * 0.2)

@dataclass
class Textile(Material):
    """裏地などの布素材（曲げても内輪差計算に影響を与えにくい）"""
    material_type: Literal['textile'] = 'textile'

class BendCalculator:
    """
    曲げによる寸法の変化（内輪差）を算出するクラス
    """

    @staticmethod
    def calculate_bend_allowance(radius: float, thickness: float, k_factor: float, angle_deg: float = 180.0) -> float:
        """
        中立軸に基づいた展開長（曲げに必要な長さ）を計算する。
        公式: L = (π * angle / 180) * (R + K * t)
        """
        angle_rad = math.radians(angle_deg)
        # 中立軸（伸び縮みゼロの地点）の半径を基準に長さを出す
        return angle_rad * (radius + k_factor * thickness)

    @staticmethod
    def get_outer_offset(thickness: float, k_factor: float) -> float:
        """
        3Dモデルの「内装表面」を基準としたとき、
        外装を何ミリ長く設計すべきかの差分（ΔL）を算出するための基礎値を返す。
        """
        # 半円（180度）折り返した時の、内側パーツと外側パーツの長さの差
        # ΔL = π * (内装半径 + 革厚) - π * (内装半径) に相当する物理的な伸び
        # ここではシンプルに「π * 厚み」をベースにした補正係数を算出
        return math.pi * thickness * k_factor