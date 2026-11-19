#!/usr/bin/env python3
"""
NDS NitroFS & NARC Extractor
Extrai arm9.bin, arm7.bin, overlays e todo o sistema de arquivos NitroFS de uma ROM .nds.
Com --unpack-narc, também descompacta arquivos .narc para inspeção de textos e gráficos.
"""

import argparse
from pathlib import Path
import ndspy.rom
import ndspy.narc
import ndspy.lz10


def walk_nitrofs(root_filenames, folder=None, prefix=""):
    """Percorre recursivamente o NitroFS retornando (caminho_relativo, file_id)."""
    if folder is None:
        folder = root_filenames
    results = []
    for name in folder.files:
        full_path = f"{prefix}/{name}" if prefix else name
        fid = root_filenames.idOf(full_path)
        results.append((full_path, fid))
    for sub_name, sub_folder in folder.folders:
        sub_prefix = f"{prefix}/{sub_name}" if prefix else sub_name
        results.extend(walk_nitrofs(root_filenames, sub_folder, sub_prefix))
    return results


def unpack_narc_file(narc_bytes: bytes, dest_dir: Path) -> int:
    """Descompacta um arquivo NARC (com suporte a LZ10) para dest_dir."""
    if narc_bytes[:1] == b"\x10":
        narc_bytes = ndspy.lz10.decompress(narc_bytes)
    narc = ndspy.narc.NARC(narc_bytes)
    dest_dir.mkdir(parents=True, exist_ok=True)
    count = 0

    def _walk_narc(folder, prefix=""):
        nonlocal count
        for name in folder.files:
            rel = f"{prefix}/{name}" if prefix else name
            fid = narc.filenames.idOf(rel)
            out_file = dest_dir / rel
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_bytes(narc.files[fid])
            count += 1
        for sub_name, sub_folder in folder.folders:
            sub_prefix = f"{prefix}/{sub_name}" if prefix else sub_name
            _walk_narc(sub_folder, sub_prefix)

    if narc.filenames.files or narc.filenames.folders:
        _walk_narc(narc.filenames)
    else:
        for idx, data in enumerate(narc.files):
            (dest_dir / f"{idx:04d}.bin").write_bytes(data)
            count += 1

    return count


def extract_rom(rom_path: Path, out_dir: Path, unpack_narc: bool = False):
    rom = ndspy.rom.NintendoDSRom.fromFile(str(rom_path))

    # 1. Binários principais (ARM9, ARM7, Overlays)
    bin_dir = out_dir / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    (bin_dir / "arm9.bin").write_bytes(rom.arm9)
    (bin_dir / "arm7.bin").write_bytes(rom.arm7)

    ov9 = rom.loadArm9Overlays()
    if ov9:
        ov9_dir = bin_dir / "overlays_arm9"
        ov9_dir.mkdir(exist_ok=True)
        for ov_id, ov in ov9.items():
            (ov9_dir / f"overlay_{ov_id:04d}.bin").write_bytes(ov.data)

    # 2. NitroFS
    nitro_dir = out_dir / "nitrofs"
    files = walk_nitrofs(rom.filenames)
    extracted_count = 0
    narc_count = 0
    narc_inner_count = 0
    narc_errors = 0

    narc_out_root = out_dir / "narc_unpacked"

    for rel_path, fid in files:
        if fid >= len(rom.files):
            continue
        data = rom.files[fid]
        dest = nitro_dir / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        extracted_count += 1

        if unpack_narc and rel_path.lower().endswith(".narc"):
            narc_count += 1
            try:
                inner = unpack_narc_file(data, narc_out_root / rel_path)
                narc_inner_count += inner
            except Exception:
                narc_errors += 1

    print(f"Extração concluída em: {out_dir}")
    print(f"- ARM9/ARM7 + {len(ov9)} overlays salvos em: {bin_dir}")
    print(f"- NitroFS: {extracted_count:,} arquivos salvos em: {nitro_dir}")
    if unpack_narc:
        print(
            f"- NARCs descompactados: {narc_count:,} "
            f"({narc_inner_count:,} arquivos internos, {narc_errors} erros)"
        )


def main():
    parser = argparse.ArgumentParser(description="Extrator de NitroFS e NARCs para ROMs NDS")
    parser.add_argument("rom", type=Path, help="Caminho para o arquivo .nds")
    parser.add_argument("-o", "--output", type=Path, required=True, help="Pasta de destino (ex: extracted/)")
    parser.add_argument("--unpack-narc", action="store_true", help="Descompacta arquivos .narc encontrados")
    args = parser.parse_args()

    if not args.rom.exists():
        raise FileNotFoundError(f"ROM não encontrada: {args.rom}")

    extract_rom(args.rom, args.output, args.unpack_narc)


if __name__ == "__main__":
    main()
