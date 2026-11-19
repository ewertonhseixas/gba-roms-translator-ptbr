"""Extract indexed SCP members from a paired .B/.MAPBIN archive.

The former extended-stream recovery was diagnostic and produced invalid offsets.
Always honor member boundaries from the FPS4 index. No reinsertion support.
"""
import argparse
import json
import re
from pathlib import Path


def decode_lz10(data: bytes, extended: bool = False) -> tuple[bytes, int]:
    if extended:
        raise ValueError("Do not decode across archive members; use the paired .B index")
    if len(data) < 4 or data[0] != 0x10:
        raise ValueError("Expected an LZ10 stream")
    declared = int.from_bytes(data[1:4], "little")
    if not declared:
        raise ValueError("Empty LZ10 size")
    out = bytearray()
    pos = 4
    while pos < len(data) and (extended or len(out) < declared):
        flags = data[pos]
        pos += 1
        for bit in range(7, -1, -1):
            if not extended and len(out) >= declared:
                return bytes(out[:declared]), declared
            if pos == len(data):
                if extended:
                    return bytes(out), declared
                raise ValueError("Truncated literal/command")
            if flags & (1 << bit):
                if pos + 2 > len(data):
                    raise ValueError("Truncated back-reference")
                a, b = data[pos:pos + 2]
                pos += 2
                distance = ((a & 15) << 8 | b) + 1
                if distance > len(out):
                    raise ValueError(f"Invalid back-reference at {pos - 2:#x}")
                for _ in range((a >> 4) + 3):
                    out.append(out[-distance])
            else:
                out.append(data[pos])
                pos += 1
            if len(out) > 64 * 1024 * 1024:
                raise ValueError("Recovery size exceeds safety limit")
    if len(out) < declared:
        raise ValueError("Stream ends before declared size")
    return bytes(out if extended else out[:declared]), declared


def collect_dialogue(data: bytes, declared: int) -> list[dict]:
    # Voice IDs anchor actual dialogue rather than arbitrary ASCII byte runs.
    rows = []
    for match in re.finditer(rb"\t\((S\d{6})\)", data):
        start = match.end()
        end = data.find(b"\0", start)
        if end < 0:
            continue
        next_id = re.search(rb"\t\(S\d{6}\)", data[start:end])
        if next_id:
            end = start + next_id.start()
        raw = data[start:end]
        if any(c not in (10, 12) and not 32 <= c <= 126 for c in raw):
            continue
        rows.append({
            "id": match[1].decode(),
            "offset": f"0x{start:X}",
            "marker_offset": f"0x{match.start():X}",
            "beyond_declared_size": start >= declared,
            "text": raw.decode("ascii").rstrip(),
        })
    return rows


def main() -> None:
    from toh_full_audit import fps4, unpack
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="MAPBIN payload, with sibling .B index")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    index = args.input.with_suffix(".B").read_bytes()
    payload = args.input.read_bytes()
    entries = list(fps4(index, payload))
    recovered = []
    scripts = []
    for name, off, stored, size, packed in entries:
        if Path(name).suffix != ".SCP":
            continue
        data, codec = unpack(packed)
        if data[:4] != b"TSS\0":
            raise ValueError(f"Expected TSS script: {name}")
        scripts.append((name, data))
        for row in collect_dialogue(data, len(data)):
            row.pop("beyond_declared_size", None)
            row.update(member=name, member_offset=f"0x{off:X}")
            recovered.append(row)
    args.output.mkdir(parents=True, exist_ok=False)
    for name, data in scripts:
        (args.output / Path(name).name).write_bytes(data)
    (args.output / "dialogue.json").write_text(
        json.dumps(recovered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["EXTRACAO POR INDICE FPS4 - SEM SUPORTE NO BUILDER ATUAL", ""]
    for row in recovered:
        lines.extend([f"{row['member']} | {row['id']} | {row['offset']}", row["text"], ""])
    (args.output / "dialogue.txt").write_text("\n".join(lines), encoding="utf-8")
    print(f"Scripts: {len(scripts)}; voice entries: {len(recovered)}")


if __name__ == "__main__":
    main()
