#!/usr/bin/env python3
"""
NDS ROM Injector & Builder — Summon Night (NDS)
Injeta traduções de 03-mensagens-do-sistema.md (arm9_dec.bin / overlays) e arquivos .rtz
recompilados no NitroFS, gerando uma nova ROM .nds em build/ sem alterar a original.
"""

import argparse
import re
from pathlib import Path
import ndspy.rom
import ndspy.codeCompression

from translation_markdown import batch_lines, plain_translation, split_md_row

ROW_RE = re.compile(
    r"^([^\s`]+)\s+`0x([0-9A-Fa-f]+)`\s*\((\d+)B\)$"
)


def inject_system_md(md_path: Path, bin_dir: Path) -> tuple[bytes, dict[int, bytes]]:
    arm9_dec_path = bin_dir / "arm9_dec.bin"
    arm9_data = bytearray(arm9_dec_path.read_bytes())

    overlays: dict[int, bytearray] = {}
    ov_dir = bin_dir / "overlays_arm9"
    if ov_dir.exists():
        for ov_file in ov_dir.glob("overlay_*.bin"):
            ov_id = int(ov_file.stem.split("_")[1])
            overlays[ov_id] = bytearray(ov_file.read_bytes())

    injected = 0
    deferred = 0

    for line in batch_lines(md_path):
        if not line.startswith("|"):
            continue
        cells = split_md_row(line)
        if len(cells) != 5:
            continue
        m = ROW_RE.match(cells[0])
        if not m:
            continue
        target_name = m.group(1)
        offset = int(m.group(2), 16)
        max_bytes = int(m.group(3))
        pt_text = plain_translation(cells[3])
        if not pt_text:
            continue

        pt_text = pt_text.replace("<br>", "\n")
        try:
            encoded = pt_text.encode("cp1252")
        except UnicodeEncodeError:
            deferred += 1
            continue
        if len(encoded) > max_bytes:
            deferred += 1
            continue
        padded = encoded.ljust(max_bytes, b"\x00")

        if target_name in ("arm9_dec.bin", "arm9.bin"):
            # Proteção: área < 0x097000 contém código executável ARM9
            if offset < 0x097000:
                continue
            arm9_data[offset : offset + max_bytes] = padded
            injected += 1
        elif target_name.startswith("overlay_"):
            ov_id = int(target_name.split("_")[1].split(".")[0])
            if ov_id in overlays:
                overlays[ov_id][offset : offset + max_bytes] = padded
                injected += 1

    print(f"Sistema/Menus injetados: {injected} strings ({deferred} mantidas no original)")
    # Zera compressedStaticEnd no ModuleParams (0xbb0) para bootar arm9 descomprimido
    magic = bytes.fromhex("2106c0dedec00621")
    m_idx = arm9_data.find(magic)
    if m_idx >= 8:
        arm9_data[m_idx - 8 : m_idx - 4] = b"\x00\x00\x00\x00"
    return bytes(arm9_data), {k: bytes(v) for k, v in overlays.items()}


def build_rom(
    orig_rom: Path,
    out_rom: Path,
    system_md: Path,
    bin_dir: Path,
    rtz_patched_dir: Path | None = None,
    font_nftr: Path | None = None,
    narc_patched_dir: Path | None = None,
):
    rom = ndspy.rom.NintendoDSRom.fromFile(str(orig_rom))

    if system_md.exists():
        arm9_comp, _ = inject_system_md(system_md, bin_dir)
        rom.arm9 = arm9_comp

    if font_nftr and font_nftr.exists():
        fid = rom.filenames.idOf("font12jp.NFTR")
        if fid is not None and fid < len(rom.files):
            rom.files[fid] = font_nftr.read_bytes()
            print(f"Fonte PT-BR injetada no NitroFS: font12jp.NFTR <- {font_nftr.name}")

    rtz_count = 0
    if rtz_patched_dir and rtz_patched_dir.exists():
        for rtz_file in rtz_patched_dir.rglob("*.rtz"):
            rel = str(rtz_file.relative_to(rtz_patched_dir)).replace("\\", "/")
            fid = rom.filenames.idOf(rel)
            if fid is not None and fid < len(rom.files):
                rom.files[fid] = rtz_file.read_bytes()
                rtz_count += 1
        print(f"RTZs atualizados no NitroFS: {rtz_count}")

    narc_count = 0
    if narc_patched_dir and narc_patched_dir.exists():
        for narc_file in narc_patched_dir.rglob("*.narc"):
            rel = str(narc_file.relative_to(narc_patched_dir)).replace("\\", "/")
            fid = rom.filenames.idOf(rel)
            if fid is not None and fid < len(rom.files):
                rom.files[fid] = narc_file.read_bytes()
                narc_count += 1
        print(f"NARCs de UI atualizados no NitroFS: {narc_count}")

    out_rom.parent.mkdir(parents=True, exist_ok=True)
    rom.saveToFile(str(out_rom))
    print(f"ROM compilada com sucesso: {out_rom} ({out_rom.stat().st_size / (1024*1024):.2f} MB)")


def main():
    base = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Injetor e Empacotador de ROM NDS")
    parser.add_argument("--rom", type=Path, default=base / "rom" / "Summon Night (Japan).nds")
    parser.add_argument("--out", type=Path, default=base / "build" / "Summon Night (PT-BR).nds")
    parser.add_argument("--system-md", type=Path, default=base / "ARQUIVOS md" / "03-mensagens-do-sistema.md")
    parser.add_argument("--bin-dir", type=Path, default=base / "extracted" / "bin")
    parser.add_argument("--rtz-dir", type=Path, default=base / "build" / "rtz_patched")
    parser.add_argument("--font-nftr", type=Path, default=base / "build" / "font12jp_ptbr.NFTR")
    parser.add_argument("--narc-dir", type=Path, default=base / "build" / "narc_patched")
    args = parser.parse_args()

    build_rom(args.rom, args.out, args.system_md, args.bin_dir, args.rtz_dir, args.font_nftr, args.narc_dir)


if __name__ == "__main__":
    main()
