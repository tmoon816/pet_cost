# Windows 单机部署指南

宠物店管理系统的 Windows 单机版打包与部署文档。打包后是一个独立的 exe + 资源目录，目标机器**不需要装 Python、Node、MySQL**，双击即用。

---

## 一、产物概览

- **入口**：`pet-cost-server.exe`（黑窗口启动，可看日志）
- **数据库**：SQLite，落在 exe 同目录的 `data\pet-cost.db`
- **配置**：首启自动生成 `data\app.env`（含管理员密码哈希、JWT 密钥）
- **访问**：浏览器打开 `http://127.0.0.1:8000`，自动弹出
- **备份**：拷贝整个 `data\` 文件夹即可（关掉 exe 之后再拷）

---

## 二、打包环境（开发机一次性准备）

打包机器上需要装好下面三样。如果你只在 Mac 上开发，可以在 Windows 虚拟机或一台 Windows 实体机上打包。

> **注意**：PyInstaller 不支持跨平台编译，**必须在 Windows 上打包**才能产出 Windows 的 exe。

### 1. Python 3.11+

到 [python.org](https://www.python.org/downloads/) 下载安装，**勾选 Add Python to PATH**。

```cmd
python --version
```

### 2. uv（Python 包管理器）

```cmd
pip install uv
```

或用 winget：

```cmd
winget install --id=astral-sh.uv -e
```

验证：

```cmd
uv --version
```

### 3. Node.js 18+

到 [nodejs.org](https://nodejs.org/) 下 LTS 版安装，验证：

```cmd
node --version
npm --version
```

---

## 三、打包步骤

### 1. 拉代码

```cmd
git clone <仓库地址> pet-cost
cd pet-cost
```

### 2. 一键打包

```cmd
cd backend
scripts\build-windows.bat
```

脚本会依次做三件事：

1. 进 `frontend\` 跑 `npm install` + `npm run build`
2. 进 `backend\` 跑 `uv sync --group package`（装运行时依赖 + PyInstaller）
3. 跑 `pyinstaller pet-cost.spec --noconfirm`

整个过程 1-3 分钟，产物在 `backend\dist\pet-cost\`，体积约 80-150 MB。

### 3. 验证打包成功

```cmd
cd dist\pet-cost
pet-cost-server.exe
```

首次启动会让你设置 admin 密码（至少 6 位），设完会自动跑迁移、起服务、弹浏览器。

按 `Ctrl+C` 停止。

### 4. 分发

把整个 `backend\dist\pet-cost\` 文件夹拷到目标机器任意位置即可，**不要只拷 exe**，里面的 `_internal\` 子目录是必须的。

---

## 四、目标机器使用

### 启动

进到 `pet-cost\` 目录，双击 `pet-cost-server.exe`。

- 黑窗口里能看到启动日志
- 首次启动设置管理员密码
- 浏览器自动打开 `http://127.0.0.1:8000`
- **关黑窗口 = 关服务**，要长期跑请看下面的"开机自启"章节

### 停止

在黑窗口按 `Ctrl+C`，或直接关窗口。

### 查看数据

数据全在 exe 同目录的 `data\` 下：

```
pet-cost\
├── pet-cost-server.exe
├── _internal\          ← 依赖库，别动
└── data\
    ├── app.env         ← 管理员配置
    ├── pet-cost.db     ← 主数据库
    ├── pet-cost.db-shm ← WAL 共享内存（运行时）
    └── pet-cost.db-wal ← WAL 日志（运行时）
```

---

## 五、常见操作

### 备份数据

**先关掉 exe**，然后整个 `data\` 文件夹拷走即可：

```cmd
xcopy /E /I data D:\backup\pet-cost-2026-06-01
```

恢复：把备份的 `data\` 覆盖回去。

### 重置管理员密码

删掉 `data\app.env` 然后重启 exe，会重新让你设密码。注意会同时刷新 JWT 密钥，所有已登录设备需要重新登录。

### 升级版本

1. 关闭旧版 exe
2. 备份 `data\` 文件夹
3. 把新版整个 `pet-cost\` 文件夹拷到目标机器（覆盖旧的，但**保留 `data\`**）
4. 启动新 exe，alembic 会自动跑增量迁移

> **永远先备份 `data\` 再升级**，迁移过程出问题可以回滚。

### 改端口

默认 `8000`。要改的话编辑 `backend\app\launcher.py` 顶部的 `PORT = 8000`，重新打包。

### 多机访问（局域网）

默认只监听 `127.0.0.1`，外部访问不到。要让局域网内其他机器访问，把 `launcher.py` 顶部 `HOST = "127.0.0.1"` 改成 `"0.0.0.0"`，重新打包。

> 改成 `0.0.0.0` 后，**该机器的 Windows 防火墙要放行 8000 端口**。打开"控制面板 → Windows Defender 防火墙 → 高级设置 → 入站规则 → 新建规则"，端口 TCP 8000 允许。

---

## 六、开机自启（可选）

### 方案 A：任务计划程序（最简单）

1. Win+R → `taskschd.msc`
2. 创建基本任务 → 触发器选"计算机启动时"
3. 操作选"启动程序"，程序填 `pet-cost-server.exe` 的完整路径
4. 完成后右键属性，勾选"使用最高权限运行"和"不管用户是否登录都要运行"

### 方案 B：注册成 Windows 服务（推荐长期运行）

用 [NSSM](https://nssm.cc/) 把 exe 包装成服务，关闭黑窗口也不影响。

```cmd
:: 下载 nssm.exe 放到 pet-cost\ 目录
nssm install PetCost "C:\path\to\pet-cost\pet-cost-server.exe"
nssm set PetCost AppDirectory "C:\path\to\pet-cost"
nssm set PetCost Start SERVICE_AUTO_START
nssm start PetCost
```

> ⚠️ **注意**：注册成服务后**没有交互式黑窗口**，所以**首次必须先双击 exe 把密码设好**，之后再注册服务。

管理：

```cmd
nssm stop PetCost      :: 停服务
nssm restart PetCost   :: 重启
nssm remove PetCost    :: 卸载
```

---

## 七、故障排查

### exe 启动闪退

在 cmd 里手动跑能看到完整报错：

```cmd
cd C:\path\to\pet-cost
pet-cost-server.exe
```

常见错误：

| 报错 | 原因 | 处理 |
|---|---|---|
| `ModuleNotFoundError: No module named 'xxx'` | PyInstaller 没收齐依赖 | 编辑 `backend\pet-cost.spec`，在 `hiddenimports` 里加上缺失模块名，重新打包 |
| `sqlite3.OperationalError: database is locked` | 多个 exe 同时跑同一个 db | 检查任务管理器，杀掉重复进程 |
| 浏览器打不开 `http://127.0.0.1:8000` | 端口被占用 | `netstat -ano \| findstr :8000` 查谁占的；或改端口（见上面） |
| 登录提示 `auth_not_configured` | `app.env` 没生成或损坏 | 删掉 `data\app.env` 重启重设 |

### 迁移失败

如果升级时 alembic 跑挂了，黑窗口会显示具体迁移版本号。**先把备份的 `data\pet-cost.db` 还原**，然后联系开发查迁移脚本。

### 日志位置

目前所有日志直接打在黑窗口（stdout）。要存盘可以这样启动：

```cmd
pet-cost-server.exe > log.txt 2>&1
```

---

## 八、SQLite 容量参考

宠物店单机自用，SQLite 完全够：

- 单库最大 281 TB（基本无视）
- 单表理论行数 2^64
- **实际经验**：5000 会员 × 3 宠物 × 200 条服务记录 ≈ 300 万行 cost，几十 MB，查询毫秒级

什么时候要升 MySQL：多门店联网、多机共用同一份数据、数据量奔着几十 GB 去。届时只需要改 `data\app.env` 里的 `DATABASE_URL`，业务代码不用动。
