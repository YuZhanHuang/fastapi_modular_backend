clean_backend/
├── pyproject.toml
├── alembic.ini              # Alembic 全域設定：指向 migrations 位置、DB URL 來源
├── docker-compose.yml
└── src/
    └── app/
        ├── config.py        # 提供 DATABASE_URL，給 app & Alembic 共用
        ├── core/
        │   ├── domain/
        │   ├── services/
        │   ├── repositories/
        │   └── gateways/
        ├── infra/
        │   ├── db/
        │   │   ├── base.py
        │   │   ├── session.py
        │   │   ├── models/
        │   │   │   └── cart_item.py
        │   │   ├── repositories/
        │   │   │   └── cart_repository_impl.py
        │   │   └── migrations/        # ✅ 新增：Alembic migration 專區
        │   │       ├── env.py         # 使用 config.DATABASE_URL + Base.metadata
        │   │       ├── script.py.mako
        │   │       └── versions/
        │   │           └── *.py       # 每個 schema 變更的 migration script
        │   └── wiring.py
        ├── api/
        │   ├── http_app.py            # 不再直接 create_all，而是依賴 Alembic 已執行的版本
        │   ├── deps.py
        │   └── v1/
        │       └── carts.py
        ├── cli/
        │   ├── main.py
        │   └── cart_commands.py       # 可包裝命令: `app db upgrade` 呼 Alembic
        ├── worker/
        │   ├── celery_app.py
        │   └── tasks.py
        └── tests/
            ├── unit/
            ├── integration/
            └── bdd/