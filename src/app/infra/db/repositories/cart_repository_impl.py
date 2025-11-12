from typing import Optional, List

from sqlalchemy.orm import Session

from app.core.domain.cart import Cart, CartItem
from app.core.repositories.cart_repository import CartRepository
from app.infra.db.models.cart_item import CartItemModel
from app.infra.db.repositories.base_repository import SqlAlchemyRepositoryBase


class CartRepositoryImpl(SqlAlchemyRepositoryBase, CartRepository):
    """
    購物車 Repository 實作類
    
    使用多重繼承：
    1. SqlAlchemyRepositoryBase - 提供通用 CRUD 操作
    2. CartRepository - 實現業務接口契約
    """

    def __init__(self, session: Session):
        """
        初始化 Repository
        
        :param session: SQLAlchemy Session 實例（通過依賴注入）
        """
        # 初始化基類，傳入 session 和對應的 Model
        SqlAlchemyRepositoryBase.__init__(self, session, CartItemModel)

    def get_by_user_id(self, user_id: str) -> Optional[Cart]:
        """
        根據用戶 ID 獲取購物車
        
        使用基類提供的 find() 方法進行查詢
        """
        # 使用基類的 find() 方法
        rows: List[CartItemModel] = self.find(user_id=user_id).all()
        
        if not rows:
            return None

        # 將資料庫模型轉換為領域模型
        return Cart(
            user_id=user_id,
            items=[
                CartItem(
                    product_id=row.product_id,
                    quantity=row.quantity,
                    unit_price=row.unit_price,
                )
                for row in rows
            ],
        )

    def save(self, cart: Cart) -> None:
        """
        保存購物車
        
        實作策略：刪除現有記錄並重新插入
        注意：此方法實現業務接口的 save(cart: Cart)，與基類的 save(model: Base) 不同
        """
        # 刪除該用戶現有的購物車項目
        self.delete_by(user_id=cart.user_id)

        # 批量創建新的購物車項目
        cart_items = [
            CartItemModel(
                user_id=cart.user_id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
            )
            for item in cart.items
        ]

        # 使用基類的 save_all() 方法批量保存
        if cart_items:
            self.save_all(cart_items)
