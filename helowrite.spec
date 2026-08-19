# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all

# Collect all textual submodules
textual_datas, textual_binaries, textual_hiddenimports = collect_all('textual')

# Collect all pyfiglet submodules (pyfiglet.fonts is loaded dynamically)
pyfiglet_datas, pyfiglet_binaries, pyfiglet_hiddenimports = collect_all('pyfiglet')

a = Analysis(
    ['src/app.py'],
    pathex=['src'],
    binaries=textual_binaries + pyfiglet_binaries,
    datas=[
        ('src/audio', 'src/audio'),
    ] + textual_datas + pyfiglet_datas,
    hiddenimports=[
        'rich',
        'watchdog',
        'watchdog.observers',
        'watchdog.events',
    ] + textual_hiddenimports + pyfiglet_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='helowrite',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
)
