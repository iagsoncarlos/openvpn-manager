"""
theme.py — Ubuntu/GNOME adaptive theme for PyQt6 apps.

Correctly handles:
  • Ubuntu 24.04 (GNOME 46): accent + dark/light encoded in gtk-theme name
      e.g.  Yaru            → orange, light
            Yaru-dark       → orange, dark
            Yaru-blue       → blue,   light
            Yaru-blue-dark  → blue,   dark
            Yaru-purple-dark → purple, dark
  • Ubuntu 24.10+ / GNOME 47+: accent-color key exists in
      org.gnome.desktop.interface
  • Fallback: Ubuntu orange, dark mode

Usage:
    from theme import ThemeManager, Colors

    tm = ThemeManager(parent=self)
    tm.theme_changed.connect(self._apply_theme)
    tm.start()
"""

import subprocess
import shutil
import re
import os
import json
import pwd
from PyQt6.QtCore import QObject, pyqtSignal, QThread


# ── Yaru accent name → hex ────────────────────────────────────────────────────
# Colours taken from the official Yaru palette / Ubuntu brand guidelines.
YARU_ACCENT_MAP: dict[str, str] = {
    "bark":     "#787859",
    "sage":     "#657B69",
    "olive":    "#4B8501",
    "viridian": "#03875B",
    "prussiangreen": "#308280",
    "blue":     "#0073E5",
    "purple":   "#7764D8",
    "magenta":  "#B34CB3",
    "red":      "#DA3450",
    # GNOME 47+ accent-color values (libadwaita names)
    "teal":     "#2190A4",
    "green":    "#3A944A",
    "yellow":   "#C88800",
    "orange":   "#E95420",   # Yaru default / Ubuntu orange
    "pink":     "#D56199",
    "slate":    "#6F8396",
}

# The default Ubuntu accent when no accent suffix is found in the theme name
UBUNTU_ORANGE   = "#E95420"
UBUNTU_ORANGE_L = "#F46A3F"
UBUNTU_ORANGE_D = "#C7461A"


def _get_original_user_context() -> dict | None:
    """Return context for the graphical user when app runs as root.

    Supports both:
    - sudo: SUDO_USER
    - pkexec: PKEXEC_UID
    """
    if os.getuid() != 0:
        return None

    sudo_user = os.environ.get("SUDO_USER")
    if sudo_user:
        try:
            pw = pwd.getpwnam(sudo_user)
            return {
                "username": pw.pw_name,
                "uid": pw.pw_uid,
                "gid": pw.pw_gid,
                "home": pw.pw_dir,
            }
        except Exception:
            pass

    pkexec_uid = os.environ.get("PKEXEC_UID")
    if pkexec_uid:
        try:
            pw = pwd.getpwuid(int(pkexec_uid))
            return {
                "username": pw.pw_name,
                "uid": pw.pw_uid,
                "gid": pw.pw_gid,
                "home": pw.pw_dir,
            }
        except Exception:
            pass

    return None


def _get_theme_cache_path() -> str:
    """Get cache file path, preferring the original desktop user's home."""
    ctx = _get_original_user_context()
    if ctx:
        return os.path.join(ctx["home"], ".cache", "openvpn-manager-theme.json")
    return os.path.expanduser("~/.cache/openvpn-manager-theme.json")


def _save_theme_cache(accent_hex: str, is_dark: bool) -> None:
    """Save theme settings to cache file.
    
    Works identically for both normal user and sudo - both can create and update.
    """
    try:
        cache_file = _get_theme_cache_path()
        cache_dir = os.path.dirname(cache_file)
        
        # Use owner-only cache permissions.
        os.makedirs(cache_dir, mode=0o700, exist_ok=True)
        
        # Write the cache file
        with open(cache_file, 'w') as f:
            json.dump({
                "accent": accent_hex,
                "dark": is_dark,
            }, f)

        try:
            os.chmod(cache_dir, 0o700)
            os.chmod(cache_file, 0o600)
        except Exception:
            pass

        ctx = _get_original_user_context()
        if ctx:
            try:
                os.chown(cache_dir, ctx["uid"], ctx["gid"])
                os.chown(cache_file, ctx["uid"], ctx["gid"])
            except Exception:
                pass
        
        print(f"[theme] Cached theme to {cache_file}")
    except Exception as e:
        print(f"[theme] WARNING: Could not cache theme: {e}")


def _load_theme_cache() -> tuple[str, bool] | None:
    """Load cached theme settings."""
    try:
        cache_file = _get_theme_cache_path()
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                data = json.load(f)
                accent = data.get("accent", UBUNTU_ORANGE)
                dark = data.get("dark", True)
                print(f"[theme] Loaded cached theme: {accent}, dark={dark}")
                return accent, dark
    except Exception as e:
        print(f"[theme] WARNING: Could not load theme cache: {e}")
    
    return None


# ── gsettings helpers ─────────────────────────────────────────────────────────

def _get_user_env() -> dict:
    """Get environment variables from the original user (not sudo user).
    
    When running with sudo, recovers the user's session environment so gsettings
    can access D-Bus, allowing sudo to read the same system theme as the user.
    """
    env = os.environ.copy()
    
    ctx = _get_original_user_context()
    if ctx:
        print(f"[theme] Running as root, using desktop user context: {ctx['username']}")

        env["HOME"] = ctx["home"]
        env["USER"] = ctx["username"]
        env["LOGNAME"] = ctx["username"]

        xdg_runtime = f"/run/user/{ctx['uid']}"
        if os.path.exists(xdg_runtime):
            env["XDG_RUNTIME_DIR"] = xdg_runtime
            dbus_socket = f"{xdg_runtime}/bus"
            if os.path.exists(dbus_socket):
                env["DBUS_SESSION_BUS_ADDRESS"] = f"unix:path={dbus_socket}"
    
    return env


def _build_gsettings_cmd(args: list[str], env: dict) -> list[str]:
    """Build a gsettings command that targets the graphical user when root."""
    base_cmd = ["gsettings"] + args
    ctx = _get_original_user_context()
    if not (ctx and os.getuid() == 0 and shutil.which("sudo")):
        return base_cmd

    cmd = ["sudo", "-H", "-u", ctx["username"], "env"]
    for k in ("HOME", "USER", "LOGNAME", "XDG_RUNTIME_DIR", "DBUS_SESSION_BUS_ADDRESS"):
        v = env.get(k)
        if v:
            cmd.append(f"{k}={v}")
    cmd.extend(base_cmd)
    return cmd


def _gsettings_get(schema: str, key: str) -> str | None:
    """Run `gsettings get <schema> <key>` and return the stripped value."""
    if not shutil.which("gsettings"):
        print(f"[theme] WARNING: gsettings command not found")
        return None
    
    try:
        env = _get_user_env()
        cmd = _build_gsettings_cmd(["get", schema, key], env)
        
        r = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=3, env=env
        )
        if r.returncode == 0:
            value = r.stdout.strip().strip("'\"")
            if value:
                print(f"[theme] ✓ {schema}/{key} = {value}")
                return value
            else:
                print(f"[theme] WARNING: {schema}/{key} returned empty value")
                return None
        else:
            error_msg = r.stderr.strip() if r.stderr else "unknown error"
            print(f"[theme] WARNING: gsettings {schema}/{key} failed: {error_msg}")
    except subprocess.TimeoutExpired:
        print(f"[theme] WARNING: gsettings {schema}/{key} timed out")
    except Exception as e:
        print(f"[theme] WARNING: gsettings {schema}/{key} exception: {e}")
    return None


def _key_exists(schema: str, key: str) -> bool:
    """Return True if <key> exists in <schema>."""
    if not shutil.which("gsettings"):
        return False
    try:
        env = _get_user_env()
        cmd = _build_gsettings_cmd(["list-keys", schema], env)
        r = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=3, env=env
        )
        exists = key in r.stdout.split()
        if exists:
            print(f"[theme] ✓ Key exists: {schema}/{key}")
        return exists
    except Exception:
        return False


# ── Theme readers ─────────────────────────────────────────────────────────────

def _parse_yaru_theme(gtk_theme: str) -> tuple[str, bool]:
    """
    Parse a Yaru gtk-theme string.
    Returns (accent_hex, is_dark).

    Examples
    --------
    'Yaru'             → (UBUNTU_ORANGE, False)
    'Yaru-dark'        → (UBUNTU_ORANGE, True)
    'Yaru-blue'        → ('#0073E5', False)
    'Yaru-blue-dark'   → ('#0073E5', True)
    'Yaru-purple-dark' → ('#7764D8', True)
    """
    name = gtk_theme.strip().lower()

    is_dark = name.endswith("-dark")
    if is_dark:
        name = name[:-5]          # strip trailing "-dark"

    # strip leading "yaru" prefix
    if name.startswith("yaru-"):
        accent_name = name[5:]    # e.g. "blue", "purple", "prussiangreen"
    elif name == "yaru":
        accent_name = ""
    else:
        # Not a Yaru theme at all — return defaults
        return UBUNTU_ORANGE, is_dark

    hex_color = YARU_ACCENT_MAP.get(accent_name, UBUNTU_ORANGE)
    return hex_color, is_dark


def _read_theme() -> tuple[str, bool]:
    """
    Returns (accent_hex, is_dark) by reading the best available source.

    Both user and sudo use the same unified approach:
    1. Try org.gnome.desktop.interface accent-color  (GNOME 47+)
    2. Try org.gnome.desktop.interface gtk-theme     (Yaru name parsing)
    3. Try org.gnome.desktop.interface color-scheme  (dark/light preference)
    4. Fall back to cache (when gsettings unavailable)
    5. Hard fallback: Ubuntu orange, dark mode
    
    This ensures both user and sudo see identical colors, with cache as
    a reliable fallback when D-Bus is unavailable (common in sudo).
    """
    print("[theme] Reading Ubuntu/GNOME theme settings...")
    
    # ── 1. GNOME 47+ accent-color key ────────────────────────────────────────
    if _key_exists("org.gnome.desktop.interface", "accent-color"):
        accent_name = _gsettings_get("org.gnome.desktop.interface", "accent-color") or ""
        if accent_name in YARU_ACCENT_MAP:
            hex_color = YARU_ACCENT_MAP[accent_name]
            # dark/light still comes from color-scheme on GNOME 47+
            scheme = _gsettings_get("org.gnome.desktop.interface", "color-scheme") or "default"
            is_dark = "dark" in scheme.lower()
            print(f"[theme] ✓ Using GNOME 47+ accent-color: {accent_name} ({hex_color}), dark={is_dark}")
            return hex_color, is_dark

    # ── 2. Yaru theme name (Ubuntu 24.04 / GNOME 46) ─────────────────────────
    gtk_theme = _gsettings_get("org.gnome.desktop.interface", "gtk-theme") or ""
    if gtk_theme.lower().startswith("yaru"):
        accent_hex, is_dark = _parse_yaru_theme(gtk_theme)
        # Also honour color-scheme = 'prefer-dark' even if theme name lacks -dark
        scheme = _gsettings_get("org.gnome.desktop.interface", "color-scheme") or "default"
        if "dark" in scheme.lower():
            is_dark = True
        print(f"[theme] ✓ Using Yaru theme: {gtk_theme} ({accent_hex}), dark={is_dark}")
        return accent_hex, is_dark

    # ── 3. Non-Yaru theme — at least try to get dark/light from color-scheme ──
    scheme = _gsettings_get("org.gnome.desktop.interface", "color-scheme") or "default"
    is_dark = "dark" in scheme.lower()
    # Also check if the theme name itself contains "dark"
    if gtk_theme and "dark" in gtk_theme.lower():
        is_dark = True
    
    # ── 4. Try cache as fallback (when gsettings fails - common in sudo) ──────
    if not gtk_theme:
        print(f"[theme] ⚠ gsettings failed, trying cached theme...")
        cached = _load_theme_cache()
        if cached:
            cached_accent, cached_dark = cached
            print(f"[theme] ✓ Using cached theme: {cached_accent}, dark={cached_dark}")
            return cached_accent, cached_dark
    
    print(f"[theme] ⚠ Falling back to default colors (color-scheme={scheme}, gtk-theme={gtk_theme}), dark={is_dark}")
    return UBUNTU_ORANGE, is_dark


# ── Live color palette ────────────────────────────────────────────────────────

class Colors:
    """
    Single source of truth for ALL colors in the app.
    Rebuilt automatically whenever the GNOME/Ubuntu theme changes.

    Accent  → driven by Yaru accent / GNOME accent-color
    Semantic → fixed (error, success, upload) — adjusted per dark/light mode
    BG / text / border → driven by dark/light mode
    """

    # Accent
    ORANGE:      str = UBUNTU_ORANGE
    ORANGE_L:    str = UBUNTU_ORANGE_L
    ORANGE_D:    str = UBUNTU_ORANGE_D
    ACCENT_NAME: str = "default"

    # Semantic / state
    RED_ERR:  str = "#E74C3C"
    RED_DARK: str = "#C0392B"
    RED_DEEP: str = "#922B21"
    GRN_OK:   str = "#26A269"
    BLUE_UP:  str = "#5BC8F5"

    # Backgrounds
    BG_BASE:    str = "#1A1A1A"
    BG_SIDEBAR: str = "#1E1E1E"
    BG_SURF:    str = "#242424"
    BG_ELEV:    str = "#2E2E2E"
    BG_CARD:    str = "#242424"

    # Borders
    BORDER:    str = "#3A3A3A"
    BORDER_LT: str = "#444444"

    # Text
    TXT_PRI: str = "#F0EDE8"
    TXT_SEC: str = "#AEA79F"
    TXT_MUT: str = "#6E6866"
    LOG_TEXT: str = "#86A886"  # Terminal/log output text

    IS_DARK: bool = True

    @classmethod
    def rebuild(cls, accent_hex: str, is_dark: bool) -> None:
        print(f"[Colors.rebuild] Called with accent_hex={accent_hex}, is_dark={is_dark}")
        cls.IS_DARK = is_dark
        cls.ORANGE   = accent_hex
        cls.ORANGE_L = cls._lighten(accent_hex, 0.15)
        cls.ORANGE_D = cls._darken(accent_hex, 0.18)
        
        # LOG_TEXT adapts to the accent color and light/dark mode
        if is_dark:
            # Dark mode: use lighter version of accent for readability on dark background
            cls.LOG_TEXT = cls._lighten(accent_hex, 0.25)
        else:
            # Light mode: use the accent color or darker version for readability on light background
            cls.LOG_TEXT = cls._darken(accent_hex, 0.15)
        
        print(f"[Colors.rebuild] Updated: ORANGE={cls.ORANGE}, LOG_TEXT={cls.LOG_TEXT}")

        if is_dark:
            cls.BG_BASE    = "#1A1A1A"
            cls.BG_SIDEBAR = "#1E1E1E"
            cls.BG_SURF    = "#242424"
            cls.BG_ELEV    = "#2E2E2E"
            cls.BG_CARD    = "#242424"
            cls.BORDER     = "#3A3A3A"
            cls.BORDER_LT  = "#444444"
            cls.TXT_PRI    = "#F0EDE8"
            cls.TXT_SEC    = "#AEA79F"
            cls.TXT_MUT    = "#6E6866"
            cls.RED_ERR    = "#E74C3C"
            cls.RED_DARK   = "#C0392B"
            cls.RED_DEEP   = "#922B21"
            cls.GRN_OK     = "#26A269"
            cls.BLUE_UP    = "#5BC8F5"
        else:
            cls.BG_BASE    = "#F4F3F2"
            cls.BG_SIDEBAR = "#ECEAE8"
            cls.BG_SURF    = "#FFFFFF"
            cls.BG_ELEV    = "#FFFFFF"
            cls.BG_CARD    = "#FFFFFF"
            cls.BORDER     = "#D8D5D0"
            cls.BORDER_LT  = "#C8C5C0"
            cls.TXT_PRI    = "#1A1A1A"
            cls.TXT_SEC    = "#5C5652"
            cls.TXT_MUT    = "#9A9590"
            cls.RED_ERR    = "#C0392B"
            cls.RED_DARK   = "#A93226"
            cls.RED_DEEP   = "#7B241C"
            cls.GRN_OK     = "#1E8449"
            cls.BLUE_UP    = "#1A6FA8"

    # ── Helpers ───────────────────────────────────────────────────────────────

    @classmethod
    def accent_rgb(cls) -> tuple[int, int, int]:
        h = cls.ORANGE.lstrip("#")
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

    @classmethod
    def _lighten(cls, hex_color: str, amount: float) -> str:
        r, g, b = cls._hex_to_rgb(hex_color)
        return cls._rgb_to_hex(
            min(255, int(r + (255 - r) * amount)),
            min(255, int(g + (255 - g) * amount)),
            min(255, int(b + (255 - b) * amount)),
        )

    @classmethod
    def _darken(cls, hex_color: str, amount: float) -> str:
        r, g, b = cls._hex_to_rgb(hex_color)
        return cls._rgb_to_hex(
            max(0, int(r * (1 - amount))),
            max(0, int(g * (1 - amount))),
            max(0, int(b * (1 - amount))),
        )

    @staticmethod
    def _hex_to_rgb(h: str) -> tuple[int, int, int]:
        h = h.lstrip("#")
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

    @staticmethod
    def _rgb_to_hex(r: int, g: int, b: int) -> str:
        return f"#{r:02X}{g:02X}{b:02X}"


# ── gsettings monitor thread ──────────────────────────────────────────────────

class _GSettingsWatcher(QThread):
    """
    Runs `gsettings monitor org.gnome.desktop.interface` and emits
    `changed` whenever a theme-relevant key changes.
    """
    changed = pyqtSignal()

    WATCHED_KEYS = {
        "accent-color",
        "color-scheme",
        "gtk-theme",
        "gtk-color-scheme",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._proc = None
        self.daemon = True

    def run(self):
        if not shutil.which("gsettings"):
            return
        try:
            env = _get_user_env()
            cmd = _build_gsettings_cmd(["monitor", "org.gnome.desktop.interface"], env)
            self._proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                text=True, bufsize=1, env=env,
            )
            for line in iter(self._proc.stdout.readline, ""):
                line = line.strip()
                if not line:
                    continue
                # Output format: "key: value"
                key = line.split(":", 1)[0].strip()
                if key in self.WATCHED_KEYS:
                    self.changed.emit()
        except Exception:
            pass

    def stop(self):
        if self._proc and self._proc.poll() is None:
            try:
                self._proc.terminate()
                self._proc.wait(timeout=2)
            except Exception:
                pass


# ── Public API ────────────────────────────────────────────────────────────────

class ThemeManager(QObject):
    """
    Reads the current Ubuntu/GNOME theme on startup, then watches gsettings
    for live changes.  Emits `theme_changed(accent_hex, is_dark)` on every
    update so the UI can rebuild its stylesheets.
    """
    theme_changed = pyqtSignal(str, bool)   # accent_hex, is_dark

    def __init__(self, parent=None):
        super().__init__(parent)
        print("[theme] ThemeManager initializing...")
        self._watcher: _GSettingsWatcher | None = None
        self._reload()
        print(f"[theme] Loaded: ORANGE={Colors.ORANGE}, IS_DARK={Colors.IS_DARK}")

    def _reload(self):
        accent_hex, is_dark = _read_theme()
        Colors.rebuild(accent_hex, is_dark)
        # Save to cache for fallback when running with sudo
        _save_theme_cache(accent_hex, is_dark)

    def start(self):
        """Start background watcher.  Call after QApplication is created."""
        print("[theme] Starting gsettings monitor...")
        self._watcher = _GSettingsWatcher(self)
        self._watcher.changed.connect(self._on_changed)
        self._watcher.start()

    def stop(self):
        if self._watcher:
            self._watcher.stop()
            self._watcher.wait(3000)

    def _on_changed(self):
        print("[theme] gsettings changed, reloading theme...")
        accent_hex, is_dark = _read_theme()
        Colors.rebuild(accent_hex, is_dark)
        # Save to cache for fallback when running with sudo
        _save_theme_cache(accent_hex, is_dark)
        print(f"[theme] Updated: ORANGE={Colors.ORANGE}, IS_DARK={Colors.IS_DARK}")
        self.theme_changed.emit(Colors.ORANGE, is_dark)

    @property
    def accent(self) -> str:
        return Colors.ORANGE

    @property
    def is_dark(self) -> bool:
        return Colors.IS_DARK