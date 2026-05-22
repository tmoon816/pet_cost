# T-026: 后端 pydantic-core 依赖 minor 升级 v2.46.4 → v2.47.0

## 背景
后端当前依赖 `pydantic-core==2.46.4`，上游已发布 `v2.47.0`。这是 minor 版本升级，需人工审批后执行。

## 变更范围
- **文件**：`backend/pyproject.toml`（版本号）、`backend/uv.lock`（锁定文件自动更新）
- **不涉及**：业务源码、API schema、数据库

## 实施步骤
1. `cd backend && uv lock --upgrade-package pydantic-core` 升级依赖
2. `uv run pytest` 跑全量测试确认兼容性
3. 检查 `uv.lock` diff 确认仅 pydantic-core 及其传递依赖变更

## 风险评估
- **风险等级**：低
- pydantic-core 2.47.x 为兼容性 minor 升级，主要包含 bugfix 和性能优化
- 项目使用 FastAPI + Pydantic v2，与 pydantic-core 2.47.x 兼容
- 若测试不通过，回滚 uv.lock 即可

## 验收标准
- 后端 pytest 全过
- `uv lock` 后 pydantic-core 版本升至 2.47.0
- 无其他依赖意外升级

## 审批
- [ ] 人工审批通过（改 status 为 approved）