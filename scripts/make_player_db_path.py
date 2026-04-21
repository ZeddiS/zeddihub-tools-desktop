import secrets
from pathlib import Path

p1, p2, p3 = secrets.token_hex(3), secrets.token_hex(3), secrets.token_hex(3)
base = Path("modules") / p1 / p2 / p3 / "player-db"
base.mkdir(parents=True, exist_ok=True)

mapping = Path("modules/.player-db-path")
rel = str(base).replace("\\", "/")
mapping.write_text(rel, encoding="utf-8")
print(rel)
