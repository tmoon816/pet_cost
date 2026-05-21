# 宠物花费管理系统 - 后端

## 🔧 环境要求
- Python 3.11+
- uv（Python包管理器）

## 🚀 启动流程

### 1. 安装依赖
```bash
uv sync
```

### 2. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 配置
# DATABASE_URL: 数据库连接地址，开发期默认sqlite:///./dev.db无需修改
# CORS_ORIGINS: 允许跨域的前端地址
```

### 3. 数据库迁移
```bash
# 运行所有迁移，创建表
uv run alembic upgrade head
```

### 4. 启动服务
```bash
uv run uvicorn app.main:app --reload --port 8000
# API文档地址：http://127.0.0.1:8000/docs
```

## 📦 常用命令

### 填充假数据
```bash
uv run python -m app.seed
```
> 每次运行会先清空客户、宠物、花费记录，再插入新的测试数据，不影响分类字典表。

### 运行测试
```bash
uv run pytest
```

### 数据库迁移
```bash
# 生成新迁移（修改ORM模型后执行）
uv run alembic revision --autogenerate -m "add xxx field"
# 应用迁移到数据库
uv run alembic upgrade head
# 回滚上一次迁移
uv run alembic downgrade -1
```

## ⚠️ SQLite开发限制
本项目开发期使用SQLite作为开发数据库，生产环境切换到MySQL 8即可。SQLite有以下限制请注意：
1. 不严格校验varchar字段长度
2. 默认外键约束不生效（本项目已强制开启`PRAGMA foreign_keys=ON`）
3. 并发处理能力有限，仅适合开发使用
4. 所有ORM模型和迁移脚本都是按照MySQL 8标准编写，切换到生产数据库直接修改DATABASE_URL即可

## 🧪 测试说明
- 测试使用内存SQLite数据库，不影响本地开发数据
- 覆盖API主路径、异常场景、级联删除、统计聚合等核心逻辑
