"""
Cart 相關的 API Schema

定義購物車相關的請求與回應資料結構。
"""
from typing import List

from pydantic import BaseModel, Field


class CartItemOut(BaseModel):
    """購物車項目回應 Schema"""
    product_id: str
    quantity: int
    unit_price: int


class CartOut(BaseModel):
    """購物車回應 Schema"""
    user_id: str
    items: List[CartItemOut]
    total: int


class AddItemIn(BaseModel):
    """新增購物車項目請求 Schema"""
    product_id: str
    unit_price: int = Field(..., ge=0, description="商品單價（最小貨幣單位，如分）")
    quantity: int = Field(1, ge=1, description="數量")

