import os, json, re
from datetime import datetime
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

RESET        = "\033[0m" ; BOLD         = "\033[1m" ; DIM          = "\033[2m"
RED          = "\033[91m"; GREEN        = "\033[92m"; YELLOW       = "\033[93m"
BLUE         = "\033[94m"; CYAN         = "\033[96m"; WHITE        = "\033[97m"
BLACK        = "\033[30m"; BG_RED       = "\033[41m"; BG_GREEN     = "\033[42m"
BG_YELLOW    = "\033[43m"; BG_BLUE      = "\033[44m"; BG_DARK_RED  = "\033[48;5;88m"
BG_DARK_BLUE = "\033[48;5;18m"

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

_fernet = Fernet(os.getenv("LOG_KEY").encode())


def write_log(level, message, parts=None):
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "level":     level.upper(),
        "message":   message,
    }
    if parts:
        entry["parts"] = parts
    encrypted = _fernet.encrypt(json.dumps(entry).encode())
    with open(os.path.join(LOG_DIR, "BOB_TRUST.log"), "ab") as f:
        f.write(encrypted + b"\n")


def read_logs():
    entries = []
    try:
        with open(os.path.join(LOG_DIR, "BOB_TRUST.log"), "rb") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(_fernet.decrypt(line).decode()))
                    except Exception:
                        pass
    except FileNotFoundError:
        pass
    return entries


TAGS = {
    "ready":   f"{BG_DARK_BLUE}{BLACK}{BOLD} READY {RESET}",
    "info":    f"{BG_DARK_BLUE}{WHITE}{BOLD} INFO  {RESET}",
    "success": f"{BG_DARK_BLUE}{WHITE}{BOLD} DONE  {RESET}",
    "error":   f"{BG_DARK_RED}{WHITE}{BOLD} ERROR {RESET}",
    "warn":    f"{BG_DARK_RED}{WHITE}{BOLD} WARN  {RESET}",
}

MSG_BUILDERS = {
    "ready": lambda msg, lp: (
        lambda url=msg.split("http")[-1] if "http" in msg else msg:
            f"{WHITE}{BOLD}Bob Identity Trust{RESET} :{RESET}  {CYAN}http{url}{RESET}"
    )(),
    "info": lambda msg, lp: (
        f"{WHITE}login{RESET}  home·{RESET}  {CYAN}{lp.get('email', msg)}{RESET}  home#{lp.get('user_id', '?')}{RESET}"
        if lp and "email" in str(lp)
        else f"{WHITE}{msg}{RESET}"
    ),
    "success": lambda msg, lp: (
        f"{GREEN}{lp.get('method', '').upper()} verified{RESET}  home· user #{lp.get('user_id', '?')}{RESET}"
        if lp else f"{GREEN}{msg}{RESET}"
    ),
    "error": lambda msg, lp: (
        f"{RED}{lp.get('method', lp.get('command', '')).upper()} failed{RESET}"
        f" · user #{lp.get('user_id', '?')} · {lp.get('message', msg)[:48]}{RESET}"
        if lp else f"{RED}{msg}{RESET}"
    ),
    "warn": lambda msg, lp: f"{YELLOW}{msg}{RESET}",
}

_W = 72


def _divider(char="─"):
    return f"{char * _W}"


def log(level, *parts, log_parts=None):
    now      = datetime.now().strftime("%H:%M:%S")
    key      = level.lower()
    badge    = TAGS.get(key, f"{WHITE}{BOLD} {key.upper():<5} {RESET}")
    ts       = f"[{now}]"
    clean_msg = re.sub(r"\033\[[0-9;]*m", "", " ".join(str(p) for p in parts))

    builder = MSG_BUILDERS.get(key, lambda msg, lp: f"{WHITE}{msg}{RESET}")
    msg     = builder(clean_msg, log_parts)

    print(f" {ts} {badge} {msg}")

    if key == "ready":
        return

    write_log(level, clean_msg, parts=log_parts)