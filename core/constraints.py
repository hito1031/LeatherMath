from dataclasses import dataclass
from typing import Dict, List, Optional
from .material import Leather

@dataclass
class AssemblyNode:
    """3D UIから渡される、1つのパーツの積層情報"""
    part_id: str
    leather: Leather
    parent_id: Optional[str] = None
    # 将来的な拡張: offset_x, offset_y (親パーツのどの位置に貼られているか)

class StackConstraintManager:
    """
    パーツの親子関係（積層状態）を管理し、
    物理的な厚みの足し算と、関係性のエラーチェックを行うクラス。
    """
    
    def __init__(self, glue_allowance: float = 0.1):
        self.nodes: Dict[str, AssemblyNode] = {}
        # レザークラフト特有の物理制約: 
        # 革同士を貼り合わせると、ボンドの層や表面の凹凸（空気層）により
        # 革単体の厚みの合計よりも、わずかに厚くなります。これを定数で補正します。
        self.glue_allowance = glue_allowance

    def add_node(self, node: AssemblyNode):
        """パーツを積層ツリーに登録する"""
        self.nodes[node.part_id] = node

    def get_inner_thickness(self, target_part_id: str) -> float:
        """
        ターゲットとなるパーツの「内側（親方向）」に積層されている全ての厚みを計算する。
        外装（Outer）が曲がる際、このメソッドを呼ぶことで「乗り越えるべき障害物の厚み」が分かります。
        """
        if target_part_id not in self.nodes:
            raise ValueError(f"Part ID '{target_part_id}' が登録されていません。")

        total_thickness = 0.0
        current_node = self.nodes[target_part_id]

        # 親を辿りながら厚みを足し合わせる（ルートノードに到達するまで）
        parent_id = current_node.parent_id
        while parent_id:
            if parent_id not in self.nodes:
                break  # 親が未登録の場合は安全にストップ
            
            parent_node = self.nodes[parent_id]
            # 親パーツの革の厚み + 接着剤/空気層のバッファ
            total_thickness += (parent_node.leather.thickness + self.glue_allowance)
            
            # さらにその親へ遡る
            parent_id = parent_node.parent_id

        return total_thickness

    def validate_stack(self) -> List[str]:
        """
        UI側の操作ミスやバグによる「循環参照」を防ぐバリデーション。
        （例: パーツAの上にパーツBが乗り、パーツBの上にパーツAが乗っている等の物理的矛盾）
        """
        errors = []
        for part_id in self.nodes:
            visited = set()
            current = part_id
            
            while current:
                if current in visited:
                    errors.append(
                        f"物理的矛盾（循環参照）を検知しました。 "
                        f"パーツ '{part_id}' の積層順序を見直してください。"
                    )
                    break
                
                visited.add(current)
                node = self.nodes.get(current)
                current = node.parent_id if node else None
                
        return errors