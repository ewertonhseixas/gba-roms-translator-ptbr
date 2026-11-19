"""Injetor seguro in-place (preserva ARM9/Overlays intactos) para Tales of Hearts (NDS)."""
import re
import shutil
import struct
import sys
import unicodedata
from pathlib import Path
import ndspy.lz10
import ndspy.rom

BASE_DIR = Path(
    "03_TRADUCAO_ROMS_NDS/jogos/Tales of Hearts - Anime Movie Edition (Japan)"
)
ROM_EN = BASE_DIR / "rom/Tales of Hearts - Anime Movie Edition (EN).nds"
ROM_PTBR = BASE_DIR / "build/Tales of Hearts - Anime Movie Edition (PT-BR).nds"
M_DEC_DIR = BASE_DIR / "extracted/m_mapbin_dec"

ROW_RE = re.compile(
    r"^\|\s*`([^`]+)`\s*\|\s*`(0x[0-9A-Fa-f]+)`\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|$"
)


def _encode_safe(ptbr: str, max_len: int) -> bytes:
    ptbr_ascii = (
        unicodedata.normalize("NFKD", ptbr)
        .encode("ascii", errors="ignore")
        .decode("ascii")
    )
    b = ptbr_ascii.encode("ascii")
    if len(b) > max_len:
        return b[:max_len]
    return b.ljust(max_len, b" ")


def main() -> int:
    if not ROM_EN.exists():
        print(f"ROM base nao encontrada: {ROM_EN}")
        return 1

    ROM_PTBR.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROM_EN, ROM_PTBR)

    rom = ndspy.rom.NintendoDSRom.fromFile(str(ROM_EN))
    raw_rom = bytearray(ROM_PTBR.read_bytes())
    fat_off = struct.unpack_from("<I", raw_rom, 0x48)[0]

    dat_updates: dict[str, list[tuple[int, str, str]]] = {}
    mapbin_updates: dict[str, list[tuple[int, str, str]]] = {}

    md_dir = BASE_DIR / "ARQUIVOS md"
    for md_file in sorted(md_dir.glob("lote-*.md")):
        for line in md_file.read_text(encoding="utf-8").splitlines():
            m = ROW_RE.match(line)
            if not m:
                continue
            rel, off_str, orig, ptbr = m.groups()
            ptbr = ptbr.strip()
            if not ptbr:
                continue
            entry = (int(off_str, 16), orig.strip(), ptbr)
            if rel.endswith(".MAPBIN"):
                mapbin_updates.setdefault(rel, []).append(entry)
            else:
                dat_updates.setdefault(rel, []).append(entry)

    # 1. Injetar .dat diretamente no NitroFS
    injected_dat = 0
    for rel, entries in dat_updates.items():
        fid = rom.filenames.idOf(rel)
        if fid is None:
            continue
        start_off, end_off = struct.unpack_from("<II", raw_rom, fat_off + fid * 8)
        for off, orig, ptbr in entries:
            max_len = len(orig.encode("ascii", errors="ignore"))
            ptbr_b = _encode_safe(ptbr, max_len)
            abs_off = start_off + off
            if abs_off + max_len <= end_off:
                raw_rom[abs_off : abs_off + max_len] = ptbr_b
                injected_dat += 1

    # 2. Injetar .MAPBIN comprimidos em LZ10 dentro de m/m.dat (via m/m.b)
    injected_mapbin = 0
    if mapbin_updates:
        mb_fid = rom.filenames.idOf("m/m.b")
        mdat_fid = rom.filenames.idOf("m/m.dat")
        mb_start, mb_end = struct.unpack_from("<II", raw_rom, fat_off + mb_fid * 8)
        mdat_start, mdat_end = struct.unpack_from("<II", raw_rom, fat_off + mdat_fid * 8)

        file_count, header_size, _ = struct.unpack_from("<III", raw_rom, mb_start + 4)
        entry_size = struct.unpack_from("<H", raw_rom, mb_start + 16)[0]

        mb_index: dict[str, tuple[int, int, int]] = {}
        for i in range(file_count):
            e_off = mb_start + header_size + i * entry_size
            f_off, f_comp, f_size = struct.unpack_from("<III", raw_rom, e_off)
            name = (
                raw_rom[e_off + 12 : e_off + entry_size]
                .split(b"\x00", 1)[0]
                .decode("ascii", errors="ignore")
                .strip()
            )
            if name:
                mb_index[name] = (e_off, f_off, f_comp)

        for name, entries in mapbin_updates.items():
            if name not in mb_index:
                continue
            dec_path = M_DEC_DIR / name
            if not dec_path.exists():
                continue
            buf = bytearray(dec_path.read_bytes())
            cnt = 0
            for off, orig, ptbr in entries:
                max_len = len(orig.encode("ascii", errors="ignore"))
                if off + max_len <= len(buf):
                    buf[off : off + max_len] = _encode_safe(ptbr, max_len)
                    cnt += 1
            comp = ndspy.lz10.compress(bytes(buf))
            e_off, f_off, f_comp = mb_index[name]
            if len(comp) <= f_comp:
                raw_rom[mdat_start + f_off : mdat_start + f_off + len(comp)] = comp
                struct.pack_into("<I", raw_rom, e_off + 4, len(comp))
                injected_mapbin += cnt
                print(f"MAPBIN {name}: {cnt} falas ({len(comp)}/{f_comp} bytes)")
            else:
                print(f"AVISO {name}: comprimido ({len(comp)}) > original ({f_comp}), pulado.")

    ROM_PTBR.write_bytes(raw_rom)
    print(f"Textos .dat injetados: {injected_dat} linhas")
    print(f"Textos .MAPBIN injetados: {injected_mapbin} linhas")
    print(f"ROM PT-BR compilada: {ROM_PTBR} ({ROM_PTBR.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
