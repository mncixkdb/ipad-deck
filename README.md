# 📱 iPad Deck — Turn Any Old iPad into a Stream Deck

A lightweight, web-based Stream Deck for Windows that works in **Safari on old iPads (even iOS 10!)** — no App Store download required.

## ⚡ Quick Start

### 1. Install Dependencies
Make sure [Python](https://www.python.org/downloads/) is installed, then open a terminal in this folder and run:

```bash
pip install -r requirements.txt
```

### 2. Run the Server
Double-click **`run.bat`** (or run `python deck.py` in a terminal).
It will show your local IP address, e.g. `http://192.168.1.9:5000`.

### 3. Open on Your iPad
1. Make sure your iPad and Windows PC are on the **same Wi-Fi**.
2. Open **Safari** on your iPad and go to the URL shown in the terminal.
3. **Optional:** Tap **Share → Add to Home Screen** for a fullscreen app-like experience!

> **Windows Firewall:** If Windows prompts you to allow Python through the firewall on first launch, click **Allow**.

---

## 🎛️ Default Buttons

- **Media & Volume:** Vol +, Vol - (hold to repeat), Mute, Play/Pause, Previous, Next, Stop
- **System & Gaming:** Screenshot (`Win+Shift+S`), Xbox Game Bar Clip (`Win+Alt+G`), Mute Mic, Unmute Mic, Task Manager, Lock PC, Sleep
- **Apps:** Notepad, Firefox, File Explorer, OneClient, Spotify, Discord

---

## 🔧 Customizing Buttons

Edit `config.json` to add, remove, or reorder buttons, then refresh Safari on your iPad.

### Action Types

- **`key`** — Press a media/volume key (`volume_up`, `volume_down`, `volume_mute`, `media_play_pause`, `media_next`, `media_prev`, `media_stop`)
  ```json
  {"type": "key", "key": "volume_up"}
  ```
- **`shortcut`** — Press a keyboard shortcut (`win`, `ctrl`, `shift`, `alt`, `a`-`z`, `0`-`9`, `f1`-`f12`, etc.)
  ```json
  {"type": "shortcut", "keys": ["win", "alt", "g"]}
  ```
- **`app`** — Launch an executable
  ```json
  {"type": "app", "path": "notepad.exe"}
  ```
- **`command`** — Run a shell command or URI
  ```json
  {"type": "command", "cmd": "start spotify:"}
  ```
- **`mic_mute` / `mic_unmute`** — Mute or unmute the default Windows microphone system-wide
  ```json
  {"type": "mic_mute"}
  ```

### Grid Size
Change `"columns": 5` in `config.json` to adjust how many buttons appear per row.
