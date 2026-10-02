# Build on Windows: .venv\Scripts\python.exe -m PyInstaller WardogsMortar.spec --noconfirm
from PyInstaller.utils.hooks import collect_all, collect_dynamic_libs

ocr_data, ocr_binaries, ocr_imports = collect_all('rapidocr')

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=ocr_binaries + collect_dynamic_libs('onnxruntime'),
    datas=ocr_data + [
        ('wardogs_mortar/data/l81.json', 'wardogs_mortar/data'),
        ('licenses', 'licenses'),
        ('README.md', '.'),
    ],
    hiddenimports=ocr_imports,
    hookspath=[],
    excludes=['tkinter', 'matplotlib', 'IPython', 'pytest', 'torch', 'paddle', 'openvino'],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [], exclude_binaries=True,
    name='WardogsMortar', debug=False, bootloader_ignore_signals=False,
    strip=False, upx=False, console=False,
    icon='assets/icon.ico',
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='WardogsMortar')

