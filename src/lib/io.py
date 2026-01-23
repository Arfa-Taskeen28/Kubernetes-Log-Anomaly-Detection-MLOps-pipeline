from pathlib import Path

def read_lines(path: str) -> list[str]:
    p = Path(path)
    text = p.read_text(encoding="utf-8", errors="ignore")
    lines = [l for l in text.splitlines() if l.strip()]
    return lines
