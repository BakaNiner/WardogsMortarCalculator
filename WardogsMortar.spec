# Build on Windows: .venv\Scripts\python.exe -m PyInstaller WardogsMortar.spec --noconfirm
from PyInstaller.utils.hooks import collect_all, collect_dynamic_libs
from pathlib import Path

ocr_data, ocr_binaries, ocr_imports = collect_all('rapidocr')

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=ocr_binaries + collect_dynamic_libs('onnxruntime'),
    datas=ocr_data + [
        ('wardogs_mortar/data/l81.json', 'wardogs_mortar/data'),
        ('wardogs_mortar/assets/check.svg', 'wardogs_mortar/assets'),
        ('wardogs_mortar/assets/language.svg', 'wardogs_mortar/assets'),
        ('licenses', 'licenses'),
        ('README.md', '.'),
    ],
    hiddenimports=ocr_imports,
    hookspath=[],
    excludes=['tkinter', 'matplotlib', 'IPython', 'pytest', 'torch', 'paddle', 'openvino'],
    noarchive=False,
)
# Qt's generic hooks collect optional plugins that this application never uses.
# Keep the desktop screen-capture UI free of PDF and virtual-keyboard components.
unused_qt_binaries = {'qpdf.dll', 'qt6pdf.dll', 'qtvirtualkeyboardplugin.dll', 'qt6virtualkeyboard.dll'}
a.binaries = [item for item in a.binaries if Path(item[0]).name.lower() not in unused_qt_binaries]
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [], exclude_binaries=True,
    name='WardogsMortar', debug=False, bootloader_ignore_signals=False,
    strip=False, upx=False, console=False,
    icon='assets/icon.ico',
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='WardogsMortar')
