"""
Never Focus State Manager
Centralized state manager for Pomodoro / Focus Mode across Never Suite apps.
"""

import os
import sys
import time
import json
import tempfile
import winsound
import threading

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "never_focus_state.json")

DEFAULT_STATE = {
    "active": False,
    "paused": False,
    "mode": "work",            # "work" | "break"
    "duration_mins": 25,
    "started_at": 0.0,
    "end_timestamp": 0.0,
    "remaining_seconds": 1500,
    "completed_sessions": 0,
    "last_updated": 0.0
}

_lock = threading.Lock()

def get_state_file_path():
    return STATE_FILE

def read_state():
    """Read the current focus state safely."""
    with _lock:
        if not os.path.exists(STATE_FILE):
            write_state(DEFAULT_STATE)
            return dict(DEFAULT_STATE)

        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            # Fallback if file was mid-write or corrupt
            return dict(DEFAULT_STATE)

        # Merge defaults for any missing keys
        state = dict(DEFAULT_STATE)
        state.update(data)

        # Check for natural expiration if active and not paused
        if state["active"] and not state["paused"]:
            now = time.time()
            rem = state["end_timestamp"] - now
            if rem <= 0:
                # Timer naturally completed
                state["remaining_seconds"] = 0
            else:
                state["remaining_seconds"] = round(rem, 1)

        return state

def write_state(state):
    """Write focus state atomically."""
    with _lock:
        state["last_updated"] = time.time()
        try:
            # Write to temporary file first then replace
            dir_name = os.path.dirname(STATE_FILE)
            fd, tmp_path = tempfile.mkstemp(dir=dir_name, prefix="focus_tmp_", suffix=".json", text=True)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, STATE_FILE)
        except Exception as e:
            # Fallback direct write
            try:
                with open(STATE_FILE, "w", encoding="utf-8") as f:
                    json.dump(state, f, indent=2, ensure_ascii=False)
            except Exception:
                pass
    return state

def start_session(duration_mins=25, mode="work"):
    """Start a focus or break session."""
    now = time.time()
    curr = read_state()
    completed = curr.get("completed_sessions", 0)
    
    end_time = now + (duration_mins * 60)
    state = {
        "active": True,
        "paused": False,
        "mode": mode,
        "duration_mins": duration_mins,
        "started_at": now,
        "end_timestamp": end_time,
        "remaining_seconds": duration_mins * 60,
        "completed_sessions": completed,
        "last_updated": now
    }
    return write_state(state)

def pause_session():
    """Pause the active focus session."""
    state = read_state()
    if state["active"] and not state["paused"]:
        now = time.time()
        rem = max(0.0, state["end_timestamp"] - now)
        state["paused"] = True
        state["remaining_seconds"] = round(rem, 1)
        write_state(state)
    return state

def resume_session():
    """Resume a paused focus session."""
    state = read_state()
    if state["active"] and state["paused"]:
        now = time.time()
        rem = state.get("remaining_seconds", 0.0)
        state["paused"] = False
        state["end_timestamp"] = now + rem
        write_state(state)
    return state

def stop_session():
    """Stop/cancel focus mode."""
    curr = read_state()
    completed = curr.get("completed_sessions", 0)
    state = dict(DEFAULT_STATE)
    state["completed_sessions"] = completed
    return write_state(state)

def complete_session():
    """Mark session as completed and transition (work -> 5m break, break -> idle work)."""
    curr = read_state()
    mode = curr.get("mode", "work")
    completed = curr.get("completed_sessions", 0)

    # Play gentle celebratory chime
    play_bell_sound()

    if mode == "work":
        # Switch to 5 min break
        return start_session(duration_mins=5, mode="break")
    else:
        # Break finished: increment completed sessions, reset to idle
        state = dict(DEFAULT_STATE)
        state["completed_sessions"] = completed + 1
        return write_state(state)

def play_bell_sound():
    """Play notification / bell sound in background thread."""
    def _chime():
        try:
            # Ascending melodic chime: C6 -> E6 -> G6
            winsound.Beep(1046, 160)
            winsound.Beep(1318, 160)
            winsound.Beep(1568, 300)
        except Exception:
            try:
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            except Exception:
                pass
    threading.Thread(target=_chime, daemon=True).start()

def is_active():
    """Quick check if focus or break is currently running."""
    st = read_state()
    if not st.get("active"):
        return False
    if st.get("paused"):
        return True
    return time.time() < st.get("end_timestamp", 0)

def format_time(seconds):
    """Format seconds into MM:SS."""
    sec = max(0, int(seconds))
    m = sec // 60
    s = sec % 60
    return f"{m:02d}:{s:02d}"

if __name__ == "__main__":
    cmd = sys.argv[1].lower() if len(sys.argv) > 1 else "status"
    if cmd == "start":
        mins = int(sys.argv[2]) if len(sys.argv) > 2 else 25
        m = sys.argv[3] if len(sys.argv) > 3 else "work"
        st = start_session(mins, m)
        print(f"Started {m} session for {mins} minutes.")
    elif cmd == "pause":
        pause_session()
        print("Focus paused.")
    elif cmd == "resume":
        resume_session()
        print("Focus resumed.")
    elif cmd == "stop":
        stop_session()
        print("Focus stopped.")
    elif cmd == "chime":
        play_bell_sound()
        time.sleep(1)
        print("Played chime.")
    else:
        st = read_state()
        print(json.dumps(st, indent=2))
