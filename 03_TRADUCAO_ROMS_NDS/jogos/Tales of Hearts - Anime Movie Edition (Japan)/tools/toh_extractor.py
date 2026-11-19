"""Extrator de arquivos FPS4 e strings de script para Tales of Hearts (NDS)."""
import re
import struct
import sys
from pathlib import Path

BASE_DIR = Path(
    "03_TRADUCAO_ROMS_NDS/jogos/Tales of Hearts - Anime Movie Edition (Japan)"
)
DATA_DIR = BASE_DIR / "extracted/nitrofs/data"
OUT_FPS4 = BASE_DIR / "extracted/fps4_unpacked"
OUT_MD = BASE_DIR / "ARQUIVOS md"

ASCII_RUN_RE = re.compile(rb"[\x20-\x7e]{4,}")


def unpack_fps4(fps4_path: Path, dest_dir: Path) -> int:
    data = fps4_path.read_bytes()
    if data[:4] != b"FPS4":
        return 0
    file_count, header_size, data_start, entry_size = struct.unpack_from("<IIII", data, 4)
    dest_dir.mkdir(parents=True, exist_ok=True)
    extracted = 0
    for i in range(file_count):
        off = header_size + i * entry_size
        if off + 12 > len(data):
            break
        f_off, f_comp_size, f_size = struct.unpack_from("<III", data, off)
        if f_off == 0xFFFFFFFF or f_size == 0:
            continue
        name = f"file_{i:04d}.bin"
        if entry_size >= 0x2C:
            raw_name = data[off + 12 : off + entry_size].split(b"\x00", 1)[0]
            decoded = raw_name.decode("ascii", errors="ignore").strip()
            if decoded and re.fullmatch(r"[A-Za-z0-9._/\-\\ ]+", decoded):
                name = decoded.replace("/", "_").replace("\\", "_")
        (dest_dir / name).write_bytes(data[f_off : f_off + f_size])
        extracted += 1
    return extracted


def extract_sample_scripts(limit: int = 20) -> Path:
    s_dir = DATA_DIR / "s"
    script_files = sorted(f for f in s_dir.iterdir() if f.is_file())[:limit]
    out_file = OUT_MD / "01-amostra-scripts-s.md"
    lines = [
        "# 📜 Amostra de Scripts (`data/s/`) — Tales of Hearts (EN -> PT-BR)",
        "",
        "| Arquivo | Offset | Texto Original (EN) | Tradução (PT-BR) |",
        "| :--- | :--- | :--- | :--- |",
    ]
    total_strings = 0
    for sf in script_files:
        raw = sf.read_bytes()
        for m in ASCII_RUN_RE.finditer(raw):
            text = m.group(0).decode("ascii").replace("|", "\\|").strip()
            if len(text) >= 4:
                lines.append(f"| `{sf.name}` | `0x{m.start():X}` | {text} | |")
                total_strings += 1
                if total_strings >= 150:
                    break
        if total_strings >= 150:
            break

    OUT_MD.mkdir(parents=True, exist_ok=True)
    out_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_file


def main() -> int:
    fps4_count = 0
    for f in DATA_DIR.rglob("*"):
        if f.is_file() and f.stat().st_size >= 16 and f.read_bytes()[:4] == b"FPS4":
            rel = f.relative_to(DATA_DIR)
            n = unpack_fps4(f, OUT_FPS4 / rel)
            print(f"FPS4: {rel} -> {n} arquivos")
            fps4_count += 1

    sample_md = extract_sample_scripts(limit=20)
    print(f"Total de arquivos FPS4 desempacotados: {fps4_count}")
    print(f"Amostra de scripts gerada em: {sample_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
