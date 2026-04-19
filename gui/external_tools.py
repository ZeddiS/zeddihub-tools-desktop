"""
ZeddiHub Tools — External tools manager.

Admin-only downloaded modules. Registry at <data_dir>/apps/apps.json.
Files live under <data_dir>/apps/<slug>/.

admin_apps.json format (served from webhosting):
{
  "tools": [
    {
      "slug": "my-tool",
      "name": "My Tool",
      "description": "Short description",
      "icon": "wrench",
      "version": "1.0.0",
      "url": "https://example.com/my-tool-1.0.0.zip",
      "entrypoint": "my_tool.exe"
    }
  ]
}
"""

import json
import os
import shutil
import subprocess
import tempfile
import threading
import urllib.request
import zipfile
from pathlib import Path
from typing import Callable, Optional

ADMIN_APPS_URL = "https://zeddihub.eu/tools/data/admin_apps.json"


def _apps_dir() -> Path:
    from .config import get_data_dir
    d = get_data_dir() / "apps"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _registry_file() -> Path:
    return _apps_dir() / "apps.json"


def load_registry() -> dict:
    rf = _registry_file()
    if not rf.exists():
        return {"installed": {}}
    try:
        with open(rf, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"installed": {}}


def save_registry(reg: dict):
    with open(_registry_file(), "w", encoding="utf-8") as f:
        json.dump(reg, f, indent=2, ensure_ascii=False)


def list_installed() -> list:
    reg = load_registry()
    return list(reg.get("installed", {}).values())


def is_installed(slug: str) -> bool:
    return slug in load_registry().get("installed", {})


def fetch_catalog(timeout: int = 8) -> list:
    """Returns list of tool dicts from admin_apps.json. Raises on failure."""
    req = urllib.request.Request(
        ADMIN_APPS_URL,
        headers={"User-Agent": "ZeddiHubTools"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode())
    return data.get("tools", [])


def install_tool(tool: dict, progress_cb: Optional[Callable[[int, int], None]] = None,
                 done_cb: Optional[Callable[[bool, str], None]] = None):
    """
    Download + extract/install tool. Runs in background thread.
    tool = catalog entry dict. done_cb(success, message).
    """
    def _run():
        slug = tool.get("slug")
        url = tool.get("url")
        if not slug or not url:
            if done_cb: done_cb(False, "Neplatný záznam nástroje.")
            return
        try:
            target_dir = _apps_dir() / slug
            if target_dir.exists():
                shutil.rmtree(target_dir)
            target_dir.mkdir(parents=True, exist_ok=True)

            # Download to temp
            tmp_fd, tmp_path = tempfile.mkstemp(suffix=os.path.basename(url) or ".bin")
            os.close(tmp_fd)

            req = urllib.request.Request(url, headers={"User-Agent": "ZeddiHubTools"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                total = int(resp.headers.get("Content-Length", 0))
                done = 0
                with open(tmp_path, "wb") as out:
                    while True:
                        chunk = resp.read(65536)
                        if not chunk:
                            break
                        out.write(chunk)
                        done += len(chunk)
                        if progress_cb:
                            progress_cb(done, total)

            # Auto-detect format
            entrypoint = tool.get("entrypoint", "")
            lower = url.lower()
            if lower.endswith(".zip"):
                with zipfile.ZipFile(tmp_path) as zf:
                    zf.extractall(target_dir)
            else:
                # Treat as .exe (or other single binary)
                exe_name = entrypoint or os.path.basename(url) or f"{slug}.exe"
                shutil.copyfile(tmp_path, target_dir / exe_name)
                entrypoint = exe_name

            try:
                os.remove(tmp_path)
            except Exception:
                pass

            # Register
            reg = load_registry()
            reg.setdefault("installed", {})[slug] = {
                "slug": slug,
                "name": tool.get("name", slug),
                "description": tool.get("description", ""),
                "icon": tool.get("icon", "wrench"),
                "version": tool.get("version", "1.0.0"),
                "entrypoint": entrypoint,
                "path": str(target_dir),
            }
            save_registry(reg)

            if done_cb: done_cb(True, f"Nainstalováno: {tool.get('name', slug)}")
        except Exception as e:
            if done_cb: done_cb(False, f"Chyba instalace: {e}")

    threading.Thread(target=_run, daemon=True).start()


def uninstall_tool(slug: str) -> bool:
    reg = load_registry()
    entry = reg.get("installed", {}).pop(slug, None)
    if not entry:
        return False
    path = Path(entry.get("path", _apps_dir() / slug))
    try:
        if path.exists():
            shutil.rmtree(path)
    except Exception:
        pass
    save_registry(reg)
    return True


def launch_tool(slug: str) -> bool:
    reg = load_registry()
    entry = reg.get("installed", {}).get(slug)
    if not entry:
        return False
    exe = Path(entry["path"]) / entry["entrypoint"]
    if not exe.exists():
        # Fallback: find first .exe in dir
        for p in Path(entry["path"]).glob("*.exe"):
            exe = p
            break
    if not exe.exists():
        return False
    try:
        subprocess.Popen([str(exe)], cwd=str(exe.parent))
        return True
    except Exception:
        return False
