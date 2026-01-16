# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(
    ['prevent_lock.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['PIL', 'pystray', 'PIL.ImageTk'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 为 Windows 应用程序添加图标资源
# 注意：这里的图标路径需要替换为实际的图标文件路径
# 如果没有图标文件，可以注释掉这行
# a.datas += [('icon.ico', 'icon.ico', 'DATA')]

b = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 创建 Windows 应用程序，使用控制台隐藏模式
# 移除 console=True 可以隐藏控制台窗口
# 如果需要调试，可以保留 console=True

# 单文件模式
# exe = EXE(
#     b,
#     a.scripts,
#     a.binaries,
#     a.zipfiles,
#     a.datas,
#     [],
#     name='prevent_lock',
#     debug=False,
#     bootloader_ignore_signals=False,
#     strip=False,
#     upx=True,
#     upx_exclude=[],
#     runtime_tmpdir=None,
#     console=True,
#     disable_windowed_traceback=False,
#     argv_emulation=False,
#     target_arch=None,
#     codesign_identity=None,
#     entitlements_file=None,
#     icon=None,
# )

# 文件夹模式（推荐，更容易处理资源文件）
exec = EXE(
    b,
    a.scripts,
    [],
    exclude_binaries=True,
    name='prevent_lock',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 隐藏控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exec,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='prevent_lock',
)
