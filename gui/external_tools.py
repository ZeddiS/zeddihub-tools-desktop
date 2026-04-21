"""
ZeddiHub Tools — External (downloadable) modules manager.

Modules are installed as Python packages embedded in ZIP archives and
rendered as CTkFrame panels inside the main app window.

Registry at <data_dir>/apps/apps.json. Files live under <data_dir>/apps/<slug>/.

admin_apps.json catalog format (served from webhosting):
{
  "tools": [
    {
      "slug": "speedtest",
      "name": "SpeedTest",
      "description": "…",
      "icon": "gauge-high",
      "version": "1.0.1",
      "url": "https://files.zeddihub.eu/modules/speedtest-1.0.1.zip"
    }
  ]
}

Each module ZIP must contain a manifest.json at the root:
{
  "slug": "speedtest",
  "name": "SpeedTest",
  "version": "1.0.1",
  "kind": "panel",
  "panel_module": "panel",
  "panel_class": "SpeedTestPanel",
  "icon": "gauge-high"
}
"""

import importlib
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import threading
import time
import urllib.error
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


def _bundled_catalog() -> list:
    """Fallback catalog shipped inside the app bundle — used whenever
    the remote endpoint returns 404 or is unreachable so the module
    panel never appears empty in production."""
    here = Path(__file__).resolve().parent.parent
    candidates = [
        here / "webhosting" / "data" / "admin_apps.json",
        here / "admin_apps.json",
    ]
    # PyInstaller onefile: _MEIPASS
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.insert(0, Path(meipass) / "admin_apps.json")
    for p in candidates:
        if p.exists():
            try:
                with open(p, encoding="utf-8") as f:
                    data = json.load(f)
                return data.get("tools", [])
            except Exception:
                continue
    return []


def fetch_catalog(timeout: int = 8) -> list:
    """Fetch the remote module catalog. Falls back to the bundled
    admin_apps.json whenever the remote is unreachable, 404s, or
    returns non-JSON — so the panel always renders something usable."""
    req = urllib.request.Request(
        ADMIN_APPS_URL, headers={"User-Agent": "ZeddiHubTools"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
        data = json.loads(body)
        tools = data.get("tools", [])
        if tools:
            return tools
        # Empty or malformed remote → prefer bundled over nothing
        bundled = _bundled_catalog()
        return bundled or tools
    except urllib.error.HTTPError as e:
        if e.code == 404:
            bundled = _bundled_catalog()
            if bundled:
                return bundled
            raise RuntimeError(
                f"HTTP 404 — katalog na {ADMIN_APPS_URL} nebyl nalezen"
            )
        raise
    except (urllib.error.URLError, TimeoutError, OSError,
            json.JSONDecodeError, UnicodeDecodeError) as e:
        bundled = _bundled_catalog()
        if bundled:
            return bundled
        raise RuntimeError(f"Nepřipojeno: {e}")


def _read_manifest(target_dir: Path) -> dict:
    mf = target_dir / "manifest.json"
    if not mf.exists():
        return {}
    try:
        with open(mf, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


class InstallTask:
    """Represents an in-flight module install. Supports pause / resume /
    cancel. Emits progress callbacks with (done, total, speed_bps, state).

    state: one of 'downloading', 'paused', 'extracting', 'done', 'cancelled', 'error'.
    """

    def __init__(self, tool: dict,
                 progress_cb: Optional[Callable[[int, int, float, str], None]] = None,
                 done_cb: Optional[Callable[[bool, str], None]] = None):
        self.tool = tool
        self._progress_cb = progress_cb
        self._done_cb = done_cb
        self._pause_ev = threading.Event()
        self._stop_ev = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.state = "idle"

    @property
    def paused(self) -> bool:
        return self._pause_ev.is_set()

    @property
    def cancelled(self) -> bool:
        return self._stop_ev.is_set()

    def pause(self):
        self._pause_ev.set()

    def resume(self):
        self._pause_ev.clear()

    def cancel(self):
        self._stop_ev.set()
        self._pause_ev.clear()

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _emit(self, done: int, total: int, speed: float, state: str):
        self.state = state
        if self._progress_cb:
            try:
                self._progress_cb(done, total, speed, state)
            except Exception:
                pass

    def _run(self):
        slug = self.tool.get("slug")
        url = self.tool.get("url")
        if not slug or not url:
            self._emit(0, 0, 0.0, "error")
            if self._done_cb: self._done_cb(False, "Neplatný záznam nástroje.")
            return

        def _fake_phase(state: str, duration: float, total_fake: int = 100):
            """Emit a fake progress animation in the given state for `duration`
            seconds. Respects pause/cancel events."""
            steps = max(8, int(duration * 20))
            dt = duration / steps
            for i in range(1, steps + 1):
                if self._stop_ev.is_set():
                    return False
                while self._pause_ev.is_set() and not self._stop_ev.is_set():
                    time.sleep(0.1)
                self._emit(int(total_fake * i / steps), total_fake, 0.0, state)
                time.sleep(dt)
            return True

        tmp_path = None
        try:
            target_dir = _apps_dir() / slug
            if target_dir.exists():
                shutil.rmtree(target_dir)
            target_dir.mkdir(parents=True, exist_ok=True)

            if not _fake_phase("preparing", 1.5):
                if self._done_cb: self._done_cb(False, "Instalace zrušena.")
                return

            tmp_fd, tmp_path = tempfile.mkstemp(suffix=".zip")
            os.close(tmp_fd)

            req = urllib.request.Request(url, headers={"User-Agent": "ZeddiHubTools"})
            self._emit(0, 0, 0.0, "downloading")
            with urllib.request.urlopen(req, timeout=30) as resp:
                total = int(resp.headers.get("Content-Length", 0))
                done = 0
                start_t = time.monotonic()
                last_t = start_t
                last_done = 0
                speed_ema = 0.0
                with open(tmp_path, "wb") as out:
                    while True:
                        if self._stop_ev.is_set():
                            self._emit(done, total, 0.0, "cancelled")
                            break
                        if self._pause_ev.is_set():
                            self._emit(done, total, 0.0, "paused")
                            while self._pause_ev.is_set() and not self._stop_ev.is_set():
                                time.sleep(0.1)
                            last_t = time.monotonic()
                            last_done = done
                            if self._stop_ev.is_set():
                                self._emit(done, total, 0.0, "cancelled")
                                break
                            self._emit(done, total, speed_ema, "downloading")
                            continue
                        chunk = resp.read(65536)
                        if not chunk:
                            break
                        out.write(chunk)
                        done += len(chunk)
                        now = time.monotonic()
                        if now - last_t >= 0.2:
                            inst = (done - last_done) / (now - last_t)
                            speed_ema = inst if speed_ema == 0.0 else speed_ema * 0.7 + inst * 0.3
                            last_t, last_done = now, done
                            self._emit(done, total, speed_ema, "downloading")

            if self._stop_ev.is_set():
                try:
                    if tmp_path and os.path.exists(tmp_path): os.remove(tmp_path)
                except Exception:
                    pass
                try:
                    if target_dir.exists(): shutil.rmtree(target_dir)
                except Exception:
                    pass
                if self._done_cb: self._done_cb(False, "Instalace zrušena.")
                return

            if not _fake_phase("verifying", 1.5):
                try:
                    if tmp_path and os.path.exists(tmp_path): os.remove(tmp_path)
                except Exception:
                    pass
                try:
                    if target_dir.exists(): shutil.rmtree(target_dir)
                except Exception:
                    pass
                if self._done_cb: self._done_cb(False, "Instalace zrušena.")
                return

            self._emit(done, total, 0.0, "extracting")
            if not zipfile.is_zipfile(tmp_path):
                raise RuntimeError("Stažený soubor není ZIP archiv.")
            with zipfile.ZipFile(tmp_path) as zf:
                zf.extractall(target_dir)
            try:
                os.remove(tmp_path)
            except Exception:
                pass

            _fake_phase("registering", 1.5)

            manifest = _read_manifest(target_dir)
            if not manifest:
                raise RuntimeError("ZIP neobsahuje manifest.json.")

            reg = load_registry()
            reg.setdefault("installed", {})[slug] = {
                "slug":         slug,
                "name":         manifest.get("name", self.tool.get("name", slug)),
                "description":  self.tool.get("description", ""),
                "icon":         manifest.get("icon", self.tool.get("icon", "wrench")),
                "version":      manifest.get("version", self.tool.get("version", "1.0.0")),
                "kind":         manifest.get("kind", "panel"),
                "panel_module": manifest.get("panel_module", "panel"),
                "panel_class":  manifest.get("panel_class", "Panel"),
                "path":         str(target_dir),
            }
            save_registry(reg)

            self._emit(done, total, 0.0, "done")
            if self._done_cb: self._done_cb(True, f"Nainstalováno: {manifest.get('name', slug)}")
        except urllib.error.HTTPError as e:
            self._emit(0, 0, 0.0, "error")
            if self._done_cb: self._done_cb(False, f"Chyba stahování: HTTP {e.code}")
        except Exception as e:
            self._emit(0, 0, 0.0, "error")
            if self._done_cb: self._done_cb(False, f"Chyba instalace: {e.__class__.__name__}: {e}")


def install_tool(tool: dict,
                 progress_cb: Optional[Callable[[int, int, float, str], None]] = None,
                 done_cb: Optional[Callable[[bool, str], None]] = None) -> InstallTask:
    """Start an install task and return its handle for pause/cancel control."""
    task = InstallTask(tool, progress_cb=progress_cb, done_cb=done_cb)
    task.start()
    return task


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
    _forget_module(slug, entry.get("panel_module", "panel"))
    return True


class UninstallTask:
    """Background uninstall with a fake progress animation.

    Phases: removing (2.5s) -> cleaning (1.5s). Emits (done, total, 0.0, state)
    where state ∈ {'removing','cleaning','done','error'}."""

    def __init__(self, slug: str,
                 progress_cb: Optional[Callable[[int, int, float, str], None]] = None,
                 done_cb: Optional[Callable[[bool, str], None]] = None):
        self.slug = slug
        self._progress_cb = progress_cb
        self._done_cb = done_cb
        self._thread: Optional[threading.Thread] = None
        self.state = "idle"

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _emit(self, done: int, total: int, state: str):
        self.state = state
        if self._progress_cb:
            try:
                self._progress_cb(done, total, 0.0, state)
            except Exception:
                pass

    def _fake_phase(self, state: str, duration: float, total: int = 100):
        steps = max(8, int(duration * 20))
        dt = duration / steps
        for i in range(1, steps + 1):
            self._emit(int(total * i / steps), total, state)
            time.sleep(dt)

    def _run(self):
        try:
            self._fake_phase("removing", 2.5)
            ok = uninstall_tool(self.slug)
            self._fake_phase("cleaning", 1.5)
            self._emit(100, 100, "done")
            if self._done_cb:
                self._done_cb(bool(ok),
                              f"Odinstalováno: {self.slug}" if ok else "Modul nebyl nainstalován.")
        except Exception as e:
            self._emit(0, 0, "error")
            if self._done_cb:
                self._done_cb(False, f"Chyba odinstalace: {e.__class__.__name__}: {e}")


def uninstall_tool_async(slug: str,
                         progress_cb: Optional[Callable[[int, int, float, str], None]] = None,
                         done_cb: Optional[Callable[[bool, str], None]] = None) -> UninstallTask:
    task = UninstallTask(slug, progress_cb=progress_cb, done_cb=done_cb)
    task.start()
    return task


def _forget_module(slug: str, module_name: str):
    """Remove cached imports so next launch picks fresh code (e.g. after update)."""
    qual = f"_zhmod_{slug}_{module_name}"
    if qual in sys.modules:
        try:
            del sys.modules[qual]
        except Exception:
            pass


def load_panel_class(slug: str):
    """Return (cls, display_name) or raise. Dynamically imports the installed
    module's panel file and returns the panel class."""
    reg = load_registry()
    entry = reg.get("installed", {}).get(slug)
    if not entry:
        raise RuntimeError(f"Modul '{slug}' není nainstalován.")
    path = Path(entry["path"])
    mod_name = entry.get("panel_module", "panel")
    cls_name = entry.get("panel_class", "Panel")
    mod_file = path / f"{mod_name}.py"
    if not mod_file.exists():
        raise RuntimeError(f"Chybí soubor modulu: {mod_file.name}")

    qual = f"_zhmod_{slug}_{mod_name}"
    # Ensure module dir is on sys.path so relative imports inside the package work
    p = str(path)
    if p not in sys.path:
        sys.path.insert(0, p)
    try:
        spec = importlib.util.spec_from_file_location(qual, str(mod_file))
        module = importlib.util.module_from_spec(spec)
        sys.modules[qual] = module
        spec.loader.exec_module(module)  # type: ignore[union-attr]
    except Exception:
        sys.modules.pop(qual, None)
        raise

    cls = getattr(module, cls_name, None)
    if cls is None:
        raise RuntimeError(f"Třída '{cls_name}' nebyla nalezena v {mod_file.name}.")
    return cls, entry.get("name", slug)
