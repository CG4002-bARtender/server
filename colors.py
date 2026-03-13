"""ANSI colour helpers for terminal output."""

RESET  = "\033[0m"
BOLD   = "\033[1m"
RED    = "\033[31m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
CYAN   = "\033[36m"
MAGENTA= "\033[35m"
DIM    = "\033[2m"


def tag(label: str, color: str) -> str:
    return f"{BOLD}{color}[{label}]{RESET}"


AUDIO   = tag("AUDIO",   CYAN)
HALL    = tag("HALL",    YELLOW)
GESTURE = tag("GESTURE", MAGENTA)
RECIPE  = tag("RECIPE",  GREEN)
GAME    = tag("GAME",    BOLD)
ERROR   = tag("ERROR",   RED)
INFO    = tag("INFO",    DIM)
