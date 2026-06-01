# PyInstaller spec — Windows 单机打包入口
# 用法: uv run pyinstaller pet-cost.spec
#
# 假设当前工作目录是 backend/，前端 dist 在 ../frontend/dist
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

hiddenimports = []
# app/ 下所有子模块全收（uvicorn / alembic 用字符串导入，PyInstaller 静态分析看不到）
hiddenimports += collect_submodules("app")
# alembic 用字符串动态加载方言/迁移依赖
hiddenimports += collect_submodules("alembic")

a = Analysis(
    ["app/launcher.py"],
    pathex=["."],
    binaries=[],
    datas=[
        ("alembic.ini", "."),
        ("alembic", "alembic"),
        ("../frontend/dist", "frontend_dist"),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "faker", "openpyxl"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="pet-cost-server",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # 黑窗口模式：方便首启输入密码、看日志
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="pet-cost",
)
