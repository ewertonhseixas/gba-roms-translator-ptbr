"""Check live NFTR lookup order and glyph cells; render an exact pixel preview."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import zlib

from nftr_ptbr_injector import _get_pixel
from toh_full_audit import rom_files
from toh_text_builder_v2 import CHAR_CODES, encode


class Font:
    def __init__(self, data):
        self.data = data
        if data[:4] != b'RTFN' or struct.unpack_from('<I', data, 8)[0] != len(data):
            raise ValueError('Invalid NFTR header')
        at, count = struct.unpack_from('<HH', data, 12)
        self.chunks = {}
        for _ in range(count):
            size = struct.unpack_from('<I', data, at + 4)[0]
            if size < 8 or at + size > len(data) or size % 4:
                raise ValueError('Invalid NFTR chunk bounds/alignment')
            self.chunks[at + 8] = data[at:at + size]
            at += size
        if at != len(data):
            raise ValueError('NFTR chunks do not cover file')
        info = next(c for c in self.chunks.values() if c[:4] == b'FNIF')
        glyph, widths, first_map = struct.unpack_from('<III', info, 16)
        self.glyphs, self.widths = self.chunks[glyph], self.chunks[widths]
        self.width, self.height, self.cell = struct.unpack_from('<BBH', self.glyphs, 8)
        self.bpp = self.glyphs[14]
        self.first, self.last = struct.unpack_from('<HH', self.widths, 8)
        self.maps = []
        seen = set()
        while first_map:
            if first_map in seen:
                raise ValueError('Cyclic CMAP chain')
            seen.add(first_map)
            chunk = self.chunks[first_map]
            if chunk[:4] != b'PAMC':
                raise ValueError('CMAP pointer targets wrong chunk')
            self.maps.append(chunk)
            first_map = struct.unpack_from('<I', chunk, 16)[0]

    def lookup(self, cp):
        # Stop at the first matching range, including its missing-glyph result.
        for chunk in self.maps:
            first, last, kind = struct.unpack_from('<HHI', chunk, 8)
            if not first <= cp <= last:
                continue
            if kind == 0:
                return struct.unpack_from('<H', chunk, 20)[0] + cp - first
            if kind == 1:
                return struct.unpack_from('<H', chunk, 20 + (cp - first) * 2)[0]
            if kind == 2:
                count = struct.unpack_from('<H', chunk, 20)[0]
                pairs = [struct.unpack_from('<HH', chunk, 22 + i * 4) for i in range(count)]
                if pairs != sorted(pairs) or len(dict(pairs)) != len(pairs):
                    raise ValueError('Unsorted or duplicate scan codes')
                return dict(pairs).get(cp, 65535)
            raise ValueError('Unknown CMAP kind')
        return 65535

    def cell_for(self, cp):
        index = self.lookup(cp)
        if not self.first <= index <= self.last:
            raise ValueError(f'Unreachable glyph: {cp:04X}')
        start = 16 + index * self.cell
        cell = self.glyphs[start:start + self.cell]
        if len(cell) != self.cell:
            raise ValueError('Glyph outside CGLP')
        metrics = struct.unpack_from('<bBB', self.widths, 16 + (index - self.first) * 3)
        return cell, metrics


def png(path, pixels, width, height):
    def chunk(kind, body):
        return struct.pack('>I', len(body)) + kind + body + struct.pack('>I', zlib.crc32(kind + body))
    raw = b''.join(b'\0' + pixels[y * width * 3:(y + 1) * width * 3] for y in range(height))
    path.write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
                     + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b''))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    files = rom_files(args.rom.read_bytes())
    results = {}
    scale, width, height = 3, 840, 318
    pixels = bytearray([20, 22, 28] * width * height)
    for number, name in enumerate(['trialFont10.NFTR', 'trialFont12.NFTR']):
        font = Font(files[name])
        entries = []
        for char, cp in CHAR_CODES.items():
            if encode(char) != struct.pack('>H', cp) or not 0xe0 <= cp >> 8 <= 0xef:
                raise ValueError('Accent encoding is inconsistent')
            cell, metrics = font.cell_for(cp)
            ink = sum(_get_pixel(cell, font.width, font.bpp, x, y) != 0
                      for y in range(font.height) for x in range(font.width))
            if not 2 <= ink < font.width * font.height // 2:
                raise ValueError(f'Empty/solid accent glyph: {name}/{char}')
            entries.append(dict(character=char, code=f'{cp:04X}', glyph=font.lookup(cp),
                                ink_pixels=ink, advance=metrics[2], sha256=hashlib.sha256(cell).hexdigest()))
        results[name] = entries
        lines = [name, 'Princesa da Floresta, dorme há mil anos.',
                 'á é í ó ú â ê ô ã õ ç à ü', 'Á É Í Ó Ú Â Ê Ô Ã Õ Ç À Ü º ª']
        for row, text in enumerate(lines):
            cursor, top = 12, 8 + number * 52 + row * 12
            for char in text:
                cell, (left, _, advance) = font.cell_for(CHAR_CODES.get(char, ord(char)))
                for y in range(font.height):
                    for x in range(font.width):
                        if _get_pixel(cell, font.width, font.bpp, x, y):
                            for dy in range(scale):
                                for dx in range(scale):
                                    px, py = (cursor + left + x) * scale + dx, (top + y) * scale + dy
                                    if 0 <= px < width and 0 <= py < height:
                                        pos = (py * width + px) * 3
                                        pixels[pos:pos + 3] = bytes([242, 218, 153])
                cursor += advance
    png(args.output / 'accent_font_preview.png', pixels, width, height)
    (args.output / 'accent_font_verification.json').write_text(
        json.dumps(dict(fonts=results, first_matching_map_lookup=True,
                        font_glyphs_verified=56, emulator_visual_test=False), ensure_ascii=False, indent=2) + '\n', 'utf-8')
    print('Verified 56 accent glyphs across both fonts, live map reachability, widths and encoding.')


if __name__ == '__main__':
    main()
