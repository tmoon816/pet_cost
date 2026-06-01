# 宠物店管理 - 店员移动端 (wx-mini)

基于 uni-app + Vue 3 + Pinia 的微信小程序，复用 `backend/` 的 FastAPI 接口和现有 JWT 鉴权。仅供个人/单店店员手机办公用，不上线。

## 当前进度（Stage 1 骨架）

- [x] 工程骨架（uni-app + vite + pinia）
- [x] 网络层（`utils/request.js`，注入 Bearer，401 自动跳登录）
- [x] auth store（登录/登出/持久化 token）
- [x] 登录页（账号密码 → 调 `/api/v1/auth/login`）
- [x] 4 个 tabbar 占位页：首页 / 开单 / 会员 / 我的
- [ ] Stage 3 开单流程
- [ ] Stage 4 今日营收数据接入
- [ ] Stage 5 会员搜索/详情

## 目录结构

```
wx-mini/
├── src/
│   ├── api/          # 每个资源一个 axios-like 模块
│   │   └── auth.js
│   ├── stores/       # Pinia store
│   │   └── auth.js
│   ├── utils/
│   │   ├── config.js   # BASE_URL / TOKEN_KEY
│   │   └── request.js  # uni.request 封装
│   ├── pages/
│   │   ├── login/
│   │   ├── index/      # 首页（今日营收）
│   │   ├── bill/       # 开单
│   │   ├── customer/   # 会员
│   │   └── mine/       # 我的（退出登录）
│   ├── App.vue
│   ├── main.js
│   ├── manifest.json
│   └── pages.json
├── index.html
├── package.json
└── vite.config.js
```

## 快速启动

### 1. 安装依赖

```bash
cd wx-mini
npm install
```

### 2. 启动后端（在另一个终端）

```bash
cd ../backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

> `--host 0.0.0.0` 是为了真机预览时手机能访问。模拟器开发者工具直连本机 `127.0.0.1` 即可。

### 3. 编译小程序

```bash
npm run dev:mp-weixin
```

编译产物会输出到 `dist/dev/mp-weixin/`。

### 4. 用微信开发者工具打开

1. 打开「微信开发者工具」
2. 导入项目，目录选 `wx-mini/dist/dev/mp-weixin/`
3. AppID 选「测试号」（`manifest.json` 已写 `touristappid` 占位）
4. 详情 → 本地设置 → 勾选 **不校验合法域名**（关键，不然 `127.0.0.1` 请求会被拦）
5. 编译预览，看到登录页即骨架就绪

### 5. 真机预览（同一局域网）

1. 把 `src/utils/config.js` 里的 `BASE_URL` 改成电脑局域网 IP，如 `http://192.168.1.10:8000`
2. 后端必须用 `--host 0.0.0.0` 启动
3. 微信开发者工具点「预览」生成二维码，手机扫码

## 关键约定

- **字段全部 snake_case**（`total_amount`、`pet_id`、`occurred_on` 等），跟后端对齐
- **登录态**：JWT 存在 `uni.storage` 的 `petcost.token`，每次 `uni.request` 自动注入 Header
- **401 处理**：自动清 token + `reLaunch` 到 `/pages/login/login`
- **409 处理**：业务侧自己 catch 处理（手机号冲突等）
- **其他错误**：`request.js` 自动弹 toast，业务页不需要重复处理

## 后续计划

按使用频率排：

1. **Stage 3 开单**（最高频，先做）：搜会员 → 选宠物 → 选项目 → 录金额 → 提交
2. **Stage 4 首页营收**：今日单数 / 流水 / 客单价 + 今日订单列表
3. **Stage 5 会员**：手机号搜索 + 会员详情 + 历史消费
4. 不做：预算、分类管理、报表导出（这些低频且复杂，留桌面端）
