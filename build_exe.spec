import os

block_cipher = None

bundle_datas = [
    # Bundle the icon so tray.py and windows can find it inside the .exe
    ('desktop/assets/icon.png', 'desktop/assets'),
    ('desktop/assets/icon.png', 'assets'),
]
for apk_cand in ['UniversalClipboard-v1.1.0.apk', 'android/app/build/outputs/apk/release/app-release.apk']:
    if os.path.exists(apk_cand):
        bundle_datas.append((apk_cand, '.'))

a = Analysis(
    ['desktop/main.py'],
    pathex=['.'],
    binaries=[],
    datas=bundle_datas,
    hiddenimports=[
        'desktop.version',
        'desktop.pairing',
        'desktop.tray',
        'desktop.server',
        'desktop.config',
        'desktop.crypto',
        'desktop.network_discovery',
        'desktop.clipboard_manager',
        'desktop.hotkey_manager',
        'pystray._win32',
        'pynput.keyboard._win32',
        'pynput.mouse._win32',
        'pyperclip',
        'aiohttp',
        'aiohttp.web',
        'aiohttp.web_ws',
        'cryptography',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'PIL.ImageGrab',
        'qrcode',
        'win32clipboard',
        'win32con',
        'tkinter',
        'tkinter.ttk',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='UniversalClipboard',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,   # No console window — runs silently in system tray
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='desktop/assets/icon.png',  # .exe file icon
    version='windows/version_info.txt',
)
