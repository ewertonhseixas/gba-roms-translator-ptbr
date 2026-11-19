"""Auditor de fontes .NFTR para suporte a acentuacao PT-BR."""
import struct
import sys
from pathlib import Path

PTBR_CHARS = "áéíóúâêôãõçàÁÉÍÓÚÂÊÔÃÕÇÀ"


def parse_nftr_chars(nftr_path: Path) -> set[int]:
    data = nftr_path.read_bytes()
    if data[:4] != b"RTFN":
        raise ValueError(f"{nftr_path.name}: header invalido {data[:4]!r}")

    offset = struct.unpack_from("<H", data, 0x0C)[0]
    chunk_count = struct.unpack_from("<H", data, 0x0E)[0]
    codepoints: set[int] = set()

    for _ in range(chunk_count):
        if offset + 8 > len(data):
            break
        magic = data[offset : offset + 4]
        size = struct.unpack_from("<I", data, offset + 4)[0]
        if magic == b"PAMC":
            first_char, last_char, map_type, _next_off = struct.unpack_from(
                "<HHII", data, offset + 8
            )
            body = offset + 20
            if map_type == 0:  # Direct
                first_glyph = struct.unpack_from("<H", data, body)[0]
                if first_glyph != 0xFFFF:
                    for cp in range(first_char, last_char + 1):
                        codepoints.add(cp)
            elif map_type == 1:  # Table
                count = last_char - first_char + 1
                for i in range(count):
                    glyph = struct.unpack_from("<H", data, body + i * 2)[0]
                    if glyph != 0xFFFF:
                        codepoints.add(first_char + i)
            elif map_type == 2:  # Scan
                entry_count = struct.unpack_from("<H", data, body)[0]
                for i in range(entry_count):
                    cp, glyph = struct.unpack_from("<HH", data, body + 2 + i * 4)
                    if glyph != 0xFFFF:
                        codepoints.add(cp)
        offset += size

    return codepoints


def main() -> int:
    data_dir = Path(
        "03_TRADUCAO_ROMS_NDS/jogos/Tales of Hearts - Anime Movie Edition (Japan)/extracted/nitrofs/data"
    )
    fonts = sorted(data_dir.glob("*.NFTR"))
    if not fonts:
        print("Nenhuma fonte .NFTR encontrada.")
        return 1

    for font in fonts:
        cps = parse_nftr_chars(font)
        present = [ch for ch in PTBR_CHARS if ord(ch) in cps]
        missing = [ch for ch in PTBR_CHARS if ord(ch) not in cps]
        print(f"=== {font.name} ({len(cps)} glifos mapeados) ===")
        print(f"  PT-BR presentes ({len(present)}/{len(PTBR_CHARS)}): {''.join(present) or 'nenhum'}")
        print(f"  PT-BR ausentes  ({len(missing)}/{len(PTBR_CHARS)}): {''.join(missing) or 'nenhum'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
