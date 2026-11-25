"""
iPad Deck - Turn your iPad into a Stream Deck
Run this on your Windows laptop, then open the URL on your iPad's Safari.
"""

import ctypes
from ctypes import wintypes
import json
import os
import socket
import subprocess
import sys
import time

try:
    from flask import Flask, render_template, jsonify, request
except ImportError:
    print("\n  Flask is not installed. Run:\n")
    print("    python -m pip install flask\n")
    sys.exit(1)


# -- Flask App ----------------------------------------------------------
app = Flask(__name__)


# -- Win32 SendInput & keybd_event Setup ---------------------------------
user32 = ctypes.windll.user32

KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002

PUL = ctypes.POINTER(ctypes.c_ulong)

class KeyBdInput(ctypes.Structure):
    _fields_ = [
        ('wVk', wintypes.WORD),
        ('wScan', wintypes.WORD),
        ('dwFlags', wintypes.DWORD),
        ('time', wintypes.DWORD),
        ('dwExtraInfo', PUL)
    ]

class HardwareInput(ctypes.Structure):
    _fields_ = [('uMsg', wintypes.DWORD), ('wParamL', wintypes.WORD), ('wParamH', wintypes.WORD)]

class MouseInput(ctypes.Structure):
    _fields_ = [
        ('dx', wintypes.LONG), ('dy', wintypes.LONG),
        ('mouseData', wintypes.DWORD), ('dwFlags', wintypes.DWORD),
        ('time', wintypes.DWORD), ('dwExtraInfo', PUL)
    ]

class Input_I(ctypes.Union):
    _fields_ = [('ki', KeyBdInput), ('mi', MouseInput), ('hi', HardwareInput)]

class Input(ctypes.Structure):
    _fields_ = [('type', wintypes.DWORD), ('ii', Input_I)]


# Keys that require KEYEVENTF_EXTENDEDKEY in Windows
EXTENDED_KEYS = {
    0xAF,  # VK_VOLUME_UP
    0xAE,  # VK_VOLUME_DOWN
    0xAD,  # VK_VOLUME_MUTE
    0xB0,  # VK_MEDIA_NEXT_TRACK
    0xB1,  # VK_MEDIA_PREV_TRACK
    0xB2,  # VK_MEDIA_STOP
    0xB3,  # VK_MEDIA_PLAY_PAUSE
    0x5B,  # VK_LWIN
    0x5C,  # VK_RWIN
    0x2C,  # VK_SNAPSHOT
    0x2D,  # VK_INSERT
    0x2E,  # VK_DELETE
    0x25,  # VK_LEFT
    0x26,  # VK_UP
    0x27,  # VK_RIGHT
    0x28,  # VK_DOWN
    0x21,  # VK_PRIOR (Page Up)
    0x22,  # VK_NEXT (Page Down)
    0x23,  # VK_END
    0x24,  # VK_HOME
}

VK_CODES = {
    "volume_up":        0xAF,
    "volume_down":      0xAE,
    "volume_mute":      0xAD,
    "media_play_pause": 0xB3,
    "media_next":       0xB0,
    "media_prev":       0xB1,
    "media_stop":       0xB2,
    "print_screen":     0x2C,
}

SHORTCUT_KEYS = {
    "win": 0x5B, "shift": 0x10, "ctrl": 0x11, "alt": 0x12,
    "tab": 0x09, "escape": 0x1B, "enter": 0x0D, "space": 0x20,
    "backspace": 0x08, "delete": 0x2E,
    "up": 0x26, "down": 0x28, "left": 0x25, "right": 0x27,
}
# A-Z
for _i in range(0x41, 0x5B):
    SHORTCUT_KEYS[chr(_i).lower()] = _i
# 0-9
for _i in range(10):
    SHORTCUT_KEYS[str(_i)] = 0x30 + _i
# F1-F12
for _i in range(1, 13):
    SHORTCUT_KEYS["f" + str(_i)] = 0x6F + _i


def send_input_key(vk_code, is_up=False):
    """Send a key using SendInput with correct extended key flag."""
    flags = 0
    if vk_code in EXTENDED_KEYS:
        flags |= KEYEVENTF_EXTENDEDKEY
    if is_up:
        flags |= KEYEVENTF_KEYUP

    extra = ctypes.c_ulong(0)
    ii = Input_I()
    ii.ki = KeyBdInput(vk_code, 0, flags, 0, ctypes.pointer(extra))
    inp = Input(1, ii)
    user32.SendInput(1, ctypes.pointer(inp), ctypes.sizeof(inp))

    # Also trigger keybd_event as fallback
    user32.keybd_event(vk_code, 0, flags, 0)


def press_key(vk_code):
    """Press and release a single key."""
    send_input_key(vk_code, is_up=False)
    time.sleep(0.03)
    send_input_key(vk_code, is_up=True)


def press_shortcut(key_names):
    """Press a keyboard shortcut (e.g. ['ctrl', 'shift', 'escape'])."""
    codes = [SHORTCUT_KEYS[k.lower()] for k in key_names if k.lower() in SHORTCUT_KEYS]
    for vk in codes:
        send_input_key(vk, is_up=False)
        time.sleep(0.02)
    time.sleep(0.05)
    for vk in reversed(codes):
        send_input_key(vk, is_up=True)
        time.sleep(0.02)


def set_mic_mute(mute=None):
    """Set or toggle system default microphone mute state via Windows Core Audio."""
    import comtypes
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

    comtypes.CoInitialize()
    try:
        mic = AudioUtilities.GetMicrophone()
        interface = mic.Activate(IAudioEndpointVolume._iid_, comtypes.CLSCTX_ALL, None)
        volume = ctypes.cast(interface, ctypes.POINTER(IAudioEndpointVolume))
        if mute is None:
            new_mute = 0 if volume.GetMute() else 1
        else:
            new_mute = 1 if mute else 0
        volume.SetMute(new_mute, None)
        return bool(new_mute)
    finally:
        comtypes.CoUninitialize()


# -- Config --------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def find_button(button_id):
    for btn in load_config()["buttons"]:
        if btn["id"] == button_id:
            return btn
    return None


# -- Routes ---------------------------------------------------------------
@app.route("/")
def index():
    cfg = load_config()
    return render_template(
        "index.html",
        buttons=cfg["buttons"],
        columns=cfg.get("columns", 4),
        title=cfg.get("title", "iPad Deck"),
    )


@app.route("/api/press", methods=["POST"])
def handle_press():
    data = request.get_json(silent=True) or {}
    btn_id = data.get("id", "")
    btn = find_button(btn_id)
    if not btn:
        print(f"[ERROR] Unknown button ID: {btn_id}")
        return jsonify(status="error", msg="Unknown button"), 404

    action = btn["action"]
    atype = action["type"]

    try:
        if atype == "key":
            vk = VK_CODES.get(action["key"])
            if not vk:
                return jsonify(status="error", msg="Unknown key"), 400
            print(f"[ACTION] Key: {action['key']} (0x{vk:02X})")
            press_key(vk)

        elif atype == "shortcut":
            print(f"[ACTION] Shortcut: {action['keys']}")
            press_shortcut(action["keys"])

        elif atype == "app":
            print(f"[ACTION] Launch app: {action['path']}")
            subprocess.Popen(action["path"], shell=True)

        elif atype == "command":
            print(f"[ACTION] Command: {action['cmd']}")
            subprocess.Popen(action["cmd"], shell=True)

        elif atype == "mic_mute":
            muted = set_mic_mute(True)
            print("[ACTION] Microphone: Muted")
            return jsonify(status="ok", muted=muted, msg="Mic Muted")

        elif atype == "mic_unmute":
            muted = set_mic_mute(False)
            print("[ACTION] Microphone: Unmuted")
            return jsonify(status="ok", muted=muted, msg="Mic Unmuted")

        else:
            return jsonify(status="error", msg="Unknown action type"), 400

        return jsonify(status="ok")

    except Exception as e:
        print(f"[ERROR] Failed executing {btn_id}: {e}")
        return jsonify(status="error", msg=str(e)), 500


# -- Startup ---------------------------------------------------------------
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


if __name__ == "__main__":
    cfg = load_config()
    port = cfg.get("port", 5000)
    ip = get_local_ip()

    print()
    print("=" * 52)
    print("  iPad Deck  -  Your iPad as a Stream Deck")
    print("=" * 52)
    print()
    print("  Open this URL on your iPad Safari:")
    print()
    print(f"    ->  http://{ip}:{port}")
    print()
    print("  TIP: Tap Share > Add to Home Screen for")
    print("       a fullscreen app-like experience!")
    print()
    print("  *  Both devices must be on the same WiFi.")
    print("=" * 52)
    print()

    app.run(host="0.0.0.0", port=port, debug=False)
