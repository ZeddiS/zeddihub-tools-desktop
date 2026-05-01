import zipfile
from pathlib import Path

path_file = Path("modules/.player-db-path")
src = Path(path_file.read_text(encoding="utf-8").strip())
out_dir = Path("dist_modules")
out_dir.mkdir(exist_ok=True)
out = out_dir / "player-db-1.0.0.zip"

with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
    for p in src.rglob("*"):
        if p.is_file():
            arc = p.relative_to(src)
            zf.write(p, arc.as_posix())

print(f"Built {out} ({out.stat().st_size} bytes)")
