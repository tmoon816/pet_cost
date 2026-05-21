# 🐾 宠物花费管理系统

宠物店/医院后台管理系统，管理客户（宠主）→ 宠物 → 花费记录三层数据，支持统计分析。

## 🛠️ 技术栈

| 层级 | 技术 |
|---|---|
| 前端 | Vue 3 + Vite + Pinia + Vue Router + Element Plus + ECharts |
| 后端 | Python + FastAPI + SQLAlchemy 2.x + Alembic |
| 数据库 | MySQL 8（生产）/ SQLite（开发） |
| 包管理 | 前端：npm，后端：uv |

## 🚀 快速启动

### 前端
```bash
cd frontend
npm install
npm run dev
# 访问 http://127.0.0.1:3000
```

### 后端
```bash
cd backend
uv sync
cp .env.example .env
# 编辑 .env 配置（开发期默认SQLite无需修改）
uv run alembic upgrade head # 建表（Phase 2完成后才有）
uv run uvicorn app.main:app --reload --port 8000
# 访问 http://127.0.0.1:8000/docs 查看API文档
```

## 📁 目录结构

```
pet_cost/
├── frontend/                    # 前端Vue项目
│   ├── src/
│   ├── public/
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── backend/                     # 后端FastAPI项目
│   ├── app/                     # 业务代码
│   │   ├── main.py              # 入口
│   │   ├── core/                # 配置、数据库
│   │   ├── models/              # ORM模型
│   │   ├── schemas/             # Pydantic请求/响应模型
│   │   ├── api/                 # 路由
│   │   └── crud/                # 数据库操作
│   ├── alembic/                 # 数据库迁移
│   ├── tests/                   # 测试
│   └── pyproject.toml
├── docs/                        # 文档
│   └── superpowers/
│       ├── specs/               # 设计文档
│       └── plans/               # 实施计划
├── .gitignore
└── README.md
```

## 📚 更多文档

- [后端README](./backend/README.md)
- [设计Spec](./docs/superpowers/specs/2026-05-21-frontend-backend-split-design.md)
- [实施计划](./docs/superpowers/plans/2026-05-21-frontend-backend-split-plan.md)
