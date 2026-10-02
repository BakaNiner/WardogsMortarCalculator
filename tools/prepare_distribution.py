"""Generate the application icon and preserve installed dependency notices."""
from importlib import metadata
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PIL import Image
from PySide6.QtWidgets import QApplication
from wardogs_mortar.app import app_icon

root = Path(__file__).resolve().parents[1]
app = QApplication([])
(root / "assets").mkdir(exist_ok=True)
app_icon().pixmap(64, 64).save(str(root / "assets" / "icon.png"))
with Image.open(root / "assets" / "icon.png") as image:
    image.save(root / "assets" / "icon.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])

destination = root / "licenses" / "third_party"
for dist in metadata.distributions():
    name = dist.metadata["Name"]
    target = destination / name
    for path in dist.files or []:
        parts = [part.lower() for part in path.parts]
        if any("license" in part or part.startswith(("copying", "notice")) for part in parts) and not str(path).endswith((".py", ".pyc")):
            source = Path(dist.locate_file(path))
            if source.is_file():
                # Keep a stable relative structure and avoid '..' escaping.
                safe = Path(*[part for part in path.parts if part not in ("..", ".")])
                output = target / safe
                output.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, output)
    target.mkdir(parents=True, exist_ok=True)
    (target / "PACKAGE.txt").write_text(f"{name} {dist.version}\n{dist.metadata.get('License', '')}\n{dist.metadata.get('Home-page', '')}\n", encoding="utf-8")
print("Icon and third-party notices prepared.")
