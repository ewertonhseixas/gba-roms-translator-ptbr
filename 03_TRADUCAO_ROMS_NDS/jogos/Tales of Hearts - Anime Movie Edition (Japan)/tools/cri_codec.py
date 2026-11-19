"""Codec CRIWARE (CRILAYLA / (c)CRI) para scripts de Tales of Hearts (NDS)."""
import struct
import sys
from pathlib import Path


def decompress_crilayla(data: bytes) -> bytes:
    """Descomprime um bloco CRILAYLA / (c)CRI."""
    cri_idx = data.find(b"(c)CRI")
    if cri_idx == -1:
        raise ValueError("Assinatura (c)CRI nao encontrada.")

    # Cabecalho de 30 bytes antes de (c)CRI:
    # 0x08: compressed_size (BE), 0x0C: uncompressed_size (BE)
    comp_size, uncomp_size = struct.unpack_from(">II", data, 0x08)
    raw_start = cri_idx + 6
    # Stream comprimido termina em raw_start + comp_size (ou len(data))
    stream = data[raw_start:]

    out = bytearray(uncomp_size)
    # Leitura de bits de tras para frente (CRILAYLA padrao)
    src_end = min(len(stream), comp_size)
    bit_pos = 0
    byte_pos = src_end - 1

    def get_bits(n: int) -> int:
        nonlocal bit_pos, byte_pos
        val = 0
        for _ in range(n):
            if byte_pos < 0:
                return val
            bit = (stream[byte_pos] >> (7 - bit_pos)) & 1
            val = (val << 1) | bit
            bit_pos += 1
            if bit_pos == 8:
                bit_pos = 0
                byte_pos -= 1
        return val

    dst_pos = uncomp_size - 1
    while dst_pos >= 0 and byte_pos >= 0:
        if get_bits(1) == 0:
            out[dst_pos] = get_bits(8)
            dst_pos -= 1
        else:
            offset = get_bits(13) + 3
            length = 3
            for bits in (2, 3, 5, 8):
                chunk = get_bits(bits)
                length += chunk
                if chunk != (1 << bits) - 1:
                    break
            else:
                while True:
                    chunk = get_bits(8)
                    length += chunk
                    if chunk != 255:
                        break
            for _ in range(length):
                if dst_pos < 0:
                    break
                src_idx = dst_pos + offset
                out[dst_pos] = out[src_idx] if src_idx < uncomp_size else 0
                dst_pos -= 1

    return bytes(out)


def main() -> int:
    s_dir = Path(
        "03_TRADUCAO_ROMS_NDS/jogos/Tales of Hearts - Anime Movie Edition (Japan)/extracted/nitrofs/data/s"
    )
    sample = s_dir / "C0101"
    dec = decompress_crilayla(sample.read_bytes())
    out_path = sample.parent.parent / "C0101.dec"
    out_path.write_bytes(dec)
    print(f"Descomprimido: {sample.name} -> {out_path.name} ({len(dec)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
