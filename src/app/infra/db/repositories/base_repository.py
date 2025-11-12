from typing import Type, List, Optional, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.infra.db.base import Base


class SqlAlchemyRepositoryBase:
    """
    通用 CRUD 基類，封裝常見的 SQLAlchemy ORM 操作
    
    參考 Django ORM 的設計風格，提供常用的資料庫操作方法
    使用注入的 Session 而非全局 db 物件，符合依賴注入原則
    """

    def __init__(self, session: Session, model: Type[Base]):
        """
        初始化 Repository
        
        :param session: SQLAlchemy Session 實例（通過依賴注入）
        :param model: SQLAlchemy Model 類別
        """
        self.session = session
        self.__model__ = model

    def _isinstance(self, model: Base, raise_error: bool = True) -> bool:
        """
        檢查模型實例是否與 Repository 配置的 Model 類型相同
        
        :param model: 模型實例
        :param raise_error: 不匹配時是否拋出異常
        :return: 是否匹配
        """
        rv = isinstance(model, self.__model__)
        if not rv and raise_error:
            raise ValueError(f'{model} is not of type {self.__model__}')
        return rv

    def save(self, model: Base) -> Base:
        """
        保存模型實例到資料庫（新增或更新）
        
        :param model: 需要保存的模型實例
        :return: 保存後的模型實例
        """
        self._isinstance(model)
        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)
        return model

    def save_all(self, model_list: List[Base]) -> List[Base]:
        """
        批量保存模型實例
        
        :param model_list: 模型實例列表
        :return: 保存後的模型實例列表
        """
        for model in model_list:
            self._isinstance(model)
        self.session.add_all(model_list)
        self.session.commit()
        for model in model_list:
            self.session.refresh(model)
        return model_list

    def all(self) -> List[Base]:
        """
        獲取所有記錄
        
        :return: 所有模型實例列表
        """
        return self.session.query(self.__model__).all()

    def get(self, _id: Any) -> Optional[Base]:
        """
        根據主鍵 ID 獲取單一記錄
        
        :param _id: 主鍵值
        :return: 模型實例或 None
        """
        return self.session.query(self.__model__).get(_id)

    def get_or_404(self, _id: Any) -> Base:
        """
        根據主鍵 ID 獲取記錄，不存在則拋出異常
        
        :param _id: 主鍵值
        :return: 模型實例
        :raises: 404 錯誤（需要自行處理異常）
        """
        instance = self.get(_id)
        if instance is None:
            raise ValueError(f'{self.__model__.__name__} with id {_id} not found')
        return instance

    def exists(self, **kwargs) -> bool:
        """
        檢查是否存在符合條件的記錄
        
        :param kwargs: 查詢條件
        :return: 是否存在
        """
        return self.session.query(self.__model__).filter_by(**kwargs).first() is not None

    def count(self, **kwargs) -> int:
        """
        統計符合條件的記錄數量
        
        :param kwargs: 查詢條件
        :return: 記錄數量
        """
        query = self.session.query(self.__model__)
        if kwargs:
            query = query.filter_by(**kwargs)
        return query.count()

    def get_or_create(self, defaults: Optional[Dict[str, Any]] = None, **kwargs) -> tuple[Base, bool]:
        """
        獲取或創建記錄
        
        :param defaults: 創建時使用的預設值
        :param kwargs: 查詢條件
        :return: (模型實例, 是否為新創建)
        """
        obj = self.first(**kwargs)
        if not obj:
            create_kwargs = {**(defaults or {}), **kwargs}
            return self.create(**create_kwargs), True
        return obj, False

    def get_all(self, *_ids: Any) -> List[Base]:
        """
        根據多個 ID 批量獲取記錄
        
        :param _ids: 主鍵值列表
        :return: 模型實例列表
        """
        return self.session.query(self.__model__).filter(self.__model__.id.in_(_ids)).all()

    def find(self, **kwargs):
        """
        查找符合條件的記錄（返回 Query 物件，可進一步鏈式調用）
        
        :param kwargs: 查詢條件
        :return: SQLAlchemy Query 物件
        """
        return self.session.query(self.__model__).filter_by(**kwargs)

    def first(self, **kwargs) -> Optional[Base]:
        """
        返回符合條件的第一條記錄
        
        :param kwargs: 查詢條件
        :return: 模型實例或 None
        """
        return self.session.query(self.__model__).filter_by(**kwargs).first()

    def first_or_404(self, **kwargs) -> Base:
        """
        返回符合條件的第一條記錄，不存在則拋出異常
        
        :param kwargs: 查詢條件
        :return: 模型實例
        :raises: 404 錯誤（需要自行處理異常）
        """
        obj = self.first(**kwargs)
        if not obj:
            raise ValueError(f'{self.__model__.__name__} not found with conditions: {kwargs}')
        return obj

    def last(self, order_by: str = 'id', sort_type: str = 'desc', **kwargs) -> Optional[Base]:
        """
        返回符合條件的最後一條記錄
        
        :param order_by: 排序欄位
        :param sort_type: 排序方式 ('asc' 或 'desc')
        :param kwargs: 查詢條件
        :return: 模型實例或 None
        """
        query = self.session.query(self.__model__).filter_by(**kwargs)
        
        order_attr = getattr(self.__model__, order_by)
        if sort_type.lower() == 'desc':
            query = query.order_by(order_attr.desc())
        else:
            query = query.order_by(order_attr.asc())
        
        return query.first()

    def new(self, **kwargs) -> Base:
        """
        創建一個新的模型實例（不保存到資料庫）
        
        :param kwargs: 模型屬性
        :return: 模型實例
        """
        return self.__model__(**kwargs)

    def create(self, **kwargs) -> Base:
        """
        創建並保存一個新的模型實例
        
        :param kwargs: 模型屬性
        :return: 保存後的模型實例
        """
        model = self.new(**kwargs)
        return self.save(model)

    def update(self, model: Base, **kwargs) -> Base:
        """
        更新模型實例的屬性
        
        :param model: 要更新的模型實例
        :param kwargs: 要更新的屬性
        :return: 更新後的模型實例
        """
        self._isinstance(model)
        for k, v in kwargs.items():
            setattr(model, k, v)
        return self.save(model)

    def delete(self, model_or_id: Any) -> None:
        """
        刪除模型實例
        
        :param model_or_id: 模型實例或主鍵 ID
        """
        if model_or_id is None:
            return
        
        if isinstance(model_or_id, self.__model__):
            model = model_or_id
        else:
            model = self.get(model_or_id)
            if model is None:
                return
        
        self._isinstance(model)
        self.session.delete(model)
        self.session.commit()

    def delete_by(self, **kwargs) -> int:
        """
        根據條件批量刪除記錄
        
        :param kwargs: 刪除條件
        :return: 刪除的記錄數量
        """
        count = self.session.query(self.__model__).filter_by(**kwargs).delete()
        self.session.commit()
        return count

