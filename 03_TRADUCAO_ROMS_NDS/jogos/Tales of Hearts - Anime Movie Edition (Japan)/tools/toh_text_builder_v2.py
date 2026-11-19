"""Indexed text reinsertion; never truncates text or patches compressed fragments.

TSS strings grow by appending to the data pool and updating typed string operands
and data references. Raw tables use validated absolute string references.
All applied rows, blocked rows and precedence decisions are written to JSON.
"""
import argparse
from collections import defaultdict, deque, Counter
import hashlib
import json
from pathlib import Path
import re
import struct
import textwrap
import unicodedata

from toh_full_audit import fps4, rom_files, unpack
from toh_movie_release import file_ids
from toh_extended_map_extractor import decode_lz10
try:
    import ndspy.codeCompression as cc
except ImportError:
    import toh_blz as cc

BASE = Path(__file__).resolve().parents[1]
ACCENTS = 'áéíóúâêôãõçàÁÉÍÓÚÂÊÔÃÕÇÀüÜºª'
# Unmapped two-byte slots within the standard Shift-JIS lead-byte range.
CHAR_CODES = {c: 0xec40 + i for i, c in enumerate(ACCENTS)}
EXEC_EMPTY_REFS = {}


def protect_executable_empty_strings(rom, executables):
    """A referenced NUL is a live empty string, never spare translation capacity."""
    pointers = set()
    for data in executables.values():
        pointers.update(struct.unpack_from('<I', data, p)[0] for p in range(0,len(data)-3,4))
    bases = {'arm9':struct.unpack_from('<I',rom,0x28)[0]}
    off,size=struct.unpack_from('<II',rom,0x50)
    for at in range(off,off+size,32):
        ident,ram=struct.unpack_from('<II',rom,at)
        bases[f'ov_{ident:02d}']=ram
    EXEC_EMPTY_REFS.clear()
    for source,data in executables.items():
        base=bases[source]
        EXEC_EMPTY_REFS[source]=sorted(ptr-base for ptr in pointers
                                       if base<=ptr<base+len(data) and data[ptr-base]==0)


def decomp_exec(rom):
    """Decompress arm9 and overlays ov_00..ov_30 from a ROM byte buffer."""
    execs = {}
    arm9_off, _, _, arm9_size = struct.unpack_from('<4I', rom, 0x20)
    execs['arm9'] = cc.decompress(rom[arm9_off:arm9_off + arm9_size])
    fat, size = struct.unpack_from('<II', rom, 0x48)
    spans = [struct.unpack_from('<II', rom, fat + i * 8) for i in range(size // 8)]
    ov_off, ov_size = struct.unpack_from('<II', rom, 0x50)
    for i in range(ov_size // 32):
        ov_id, _, _, _, _, _, fid, comp_flags = struct.unpack_from('<8I', rom, ov_off + i * 32)
        a, z = spans[fid]
        buf = bytearray(rom[a:z])
        comp_size = comp_flags & 0xFFFFFF
        if comp_flags & 0x01000000:
            hlen = buf[comp_size - 5]
            if hlen > 8:
                buf[comp_size - hlen:comp_size - 8] = b'\xff' * (hlen - 8)
            execs[f'ov_{ov_id:02d}'] = cc.decompress(bytes(buf[:comp_size]))
        else:
            execs[f'ov_{ov_id:02d}'] = bytes(buf)
    return execs


def encode(text):
    text = unicodedata.normalize('NFC', text)
    for a, b in [('’', "'"), ('‘', "'"), ('“', '"'), ('”', '"'),
                 ('—', '-'), ('–', '-'), ('…', '...'), ('\xa0', ' ')]:
        text = text.replace(a, b)
    out = bytearray()
    for c in text:
        if c in CHAR_CODES:
            out.extend(struct.pack('>H', CHAR_CODES[c]))
        else:
            out.extend(c.encode('cp932', errors='strict'))
    return bytes(out)


def clean(cell):
    body = cell[1:-1] if len(cell) >= 2 and cell.startswith(' ') and cell.endswith(' ') else cell.strip()
    parts = []
    for part in body.split('<br>'):
        if part.startswith('`') and part.endswith('`') and len(part) >= 2:
            part = part[1:-1]
        elif part.startswith('**') and part.endswith('**') and len(part) >= 4:
            part = part[2:-2]
        parts.append(part)
    value=re.sub(r'\\+\|', '|', '\n'.join(parts)).replace('<page>', '\f')
    return re.sub(r'<c([0-9]+)>',lambda m:'\x03('+m[1]+')',value)


def reflow(text):
    pages = []
    for page in text.split('\f'):
        page_lines = page.split('\n')
        # If the page already respects <=35 chars on every line and <=3 lines (or is a 4+ line choice menu), preserve its exact breaks.
        if all(len(re.sub(r'^\t?\(?[A-Za-z0-9_]+\)', '', ln)) <= 35 for ln in page_lines) and (len(page_lines) <= 3 or len(page_lines) >= 4):
            pages.append(page)
            continue
        lines = []
        for line in page_lines:
            marker = re.match(r'^(\t?\(?[A-Za-z0-9_]+\))', line)
            prefix = marker[0] if marker else ''
            body = line[len(prefix):]
            wrapped = textwrap.wrap(body, width=35, break_long_words=False,
                                    break_on_hyphens=False, replace_whitespace=False) or ['']
            wrapped[0] = prefix + wrapped[0]
            lines.extend(wrapped)
        pages.extend('\n'.join(lines[i:i + 3]) for i in range(0, len(lines), 3))
    return '\f'.join(pages)


def compress(data):
    """Greedy LZ10, with a bounded dictionary and 4096-byte window."""
    out = bytearray(b'\x10' + len(data).to_bytes(3, 'little'))
    positions = defaultdict(lambda: deque(maxlen=64))
    i = 0
    while i < len(data):
        flag_at = len(out); out.append(0)
        for bit in range(7, -1, -1):
            if i >= len(data):
                break
            length, distance = 0, 0
            if i + 3 <= len(data):
                key = data[i:i + 3]
                for prev in reversed(positions[key]):
                    if i - prev > 4096:
                        break
                    n = 3
                    while n < 18 and i + n < len(data) and data[prev + n] == data[i + n]:
                        n += 1
                    if n > length:
                        length, distance = n, i - prev
                        if n == 18:
                            break
            take = length if length >= 3 else 1
            if length >= 3:
                out[flag_at] |= 1 << bit
                d = distance - 1
                out.extend([((length - 3) << 4) | (d >> 8), d & 255])
            else:
                out.append(data[i])
            for pos in range(i, i + take):
                if pos + 3 <= len(data):
                    positions[data[pos:pos + 3]].append(pos)
            i += take
    if decode_lz10(bytes(out))[0] != data:
        raise ValueError('LZ10 round-trip failed')
    return bytes(out)


def rows_from_md(folder=None):
    rows = []
    for path in sorted((Path(folder) if folder else BASE / 'ARQUIVOS md').glob('*.md')):
        if not path.is_file():
            continue
        for line_no, line in enumerate(path.read_text(encoding='utf-8-sig').splitlines(), 1):
            m = re.match(r'^\|\s*`([^`]+)`\s*\|\s*`(0x[0-9A-Fa-f]+)`\s*\|', line)
            if not m:
                continue
            cells = re.split(r'(?<!\\)\|', line[m.end():])
            if len(cells) >= 2 and cells[1].strip():
                rows.append(dict(md=path.name, line=line_no, source=m[1],
                                 offset=int(m[2], 16), original=clean(cells[0]),
                                 translation=clean(cells[1])))
    return rows


def patch_strings(data, rows, source, applied, blocked):
    if source == 'arm9' or source.startswith('ov_'):
        out = bytearray(data)
        for row in sorted(rows, key=lambda r: r['resolved_offset']):
            at = row['resolved_offset']
            original = row['original'].encode('cp932')
            if data[at:at + len(original)] != original:
                blocked.append(dict(row, reason='Original executable text mismatch'))
                continue
            old_end = data.find(b'\0', at)
            if old_end < 0:
                blocked.append(dict(row, reason='No valid NUL-delimited executable string'))
                continue
            nul_end = old_end
            while nul_end < len(data) and data[nul_end] == 0:
                nul_end += 1
            max_cap = nul_end - at - 1
            for protected in EXEC_EMPTY_REFS.get(source, ()):
                if old_end <= protected < nul_end:
                    max_cap = min(max_cap, protected-at)
            try:
                enc = encode(row['translation'])
            except UnicodeError as exc:
                blocked.append(dict(row, reason=str(exc)))
                continue
            if len(enc) > max_cap:
                blocked.append(dict(row, reason=f'Executable string exceeds in-place capacity ({len(enc)} > {max_cap})'))
                continue
            clear_end = max(old_end, at + len(enc))
            out[at:clear_end] = enc.ljust(clear_end - at, b'\0')
            applied.append(dict(row, compiled_source=source, string_start=at,
                                destination=at, string_hex=enc.hex(),
                                reference_positions=['in_place_exec']))
        return bytes(out)
    tss = data[:4] == b'TSS\0'
    pool = struct.unpack_from('<I', data, 12)[0] if tss else 0
    reference_start = 0
    reference_fields = None
    if source == 'TODS3_SormaSkillData.dat':
        pool=struct.unpack_from('<I',data,20)[0]
        assert data[16:20]==b'MASL'
        reference_fields=sorted({at+field for at in range(20,pool-11,4)
                                if all(pool-1<=struct.unpack_from('<I',data,at+field)[0]<len(data)
                                       for field in (0,4,8)) for field in (0,4,8)})
        # The final linked/assist arte table stores one name pointer per
        # 24-byte record rather than a name/reading/description triple.
        linked_fields=range(0x24d4,0x2c55,24)
        assert all(pool<=struct.unpack_from('<I',data,at)[0]<len(data) for at in linked_fields)
        reference_fields=sorted(set(reference_fields)|set(linked_fields))
    if source == 'btl/prm/To9_EnemyData.dat':
        table=struct.unpack_from('<I',data,8)[0]
        records_end=struct.unpack_from('<I',data,16)[0]
        pool=struct.unpack_from('<I',data,12)[0]
        count=struct.unpack_from('<H',data,4)[0]
        assert table+count*116==records_end and records_end<=pool<len(data)
        reference_fields=[record+field for record in range(table,records_end,116) for field in (0,84)]
        assert all(pool<=struct.unpack_from('<I',data,at)[0]<len(data) for at in reference_fields)
    layouts = {b'VALU': 16, b'ACCE': 40, b'ITEM': 28, b'MATE': 16, b'SORM': 124}
    if data[12:16] in layouts or data[:4] == b'GSD\xff' or data[:4] == b'd\x00{\x00':
        # VALU records end in non-text flag bytes. The first string starts at
        # the declared pool, not at the last NUL inside those flags.
        if data[:4] == b'GSD\xff':
            count = struct.unpack_from('<H', data, 4)[0]
            table, stride = 16, 12
            value_pool = table + count * stride
            field_offsets = (0, 4)
        elif data[:4] == b'd\x00{\x00':
            table, value_pool = struct.unpack_from('<II', data, 4)
            stride = 16
            field_offsets = (0,)
        else:
            table, value_pool = struct.unpack_from('<II', data, 4)
            count = struct.unpack_from('<H', data, 2)[0]
            stride = layouts[data[12:16]]
            field_offsets = (0, 4)
        if table != 16 or (data[:4] != b'd\x00{\x00' and value_pool != table + count * stride) or value_pool > len(data):
            raise ValueError('Unexpected named-item record layout')
        reference_fields = []
        for record in range(table, value_pool, stride):
            for off in field_offsets:
                field = record + off
                pointer = struct.unpack_from('<I', data, field)[0]
                if not value_pool <= pointer < len(data):
                    raise ValueError('VALU string pointer outside pool')
                reference_fields.append(field)
        pool = value_pool
        reference_start = table
    groups = defaultdict(list)
    # Newer complete-box edits supersede older overlapping line fragments.
    accepted = []
    for row in sorted(rows, key=lambda r: (r['md'], r['line']), reverse=True):
        a, z = row['resolved_offset'], row['resolved_offset'] + len(row['original'].encode('cp932'))
        if any(a < bz and ba < z for ba, bz in accepted):
            row['overlap_superseded'] = True
            continue
        accepted.append((a, z))
    for row in rows:
        if row.get('overlap_superseded'):
            continue
        at = row['resolved_offset']
        start = max(pool, data.rfind(b'\0', pool, at) + 1)
        end = data.find(b'\0', at)
        if end < 0 or (tss and start < pool):
            blocked.append(dict(row, reason='No valid NUL-delimited string'))
            continue
        groups[start, end].append(row)
    out = bytearray(data)
    occupied = list(groups)
    min_text = min((a for a, z in occupied), default=len(data))
    rebuild_pool = (struct.unpack_from('<I', data, 8)[0] if (data[:4] in (b'OTLE', b'BTLM') or data[4:8] == b'STRT')
                    else struct.unpack_from('<I', data, 20)[0]
                    if data[24:28] == b'TITL' else None)
    rebuilt = []
    for (start, end), group in sorted(groups.items()):
        replacement = data[start:end]
        try:
            for row in sorted(group, key=lambda r: r['resolved_offset'], reverse=True):
                at = row['resolved_offset'] - start
                original = row['original'].encode('cp932')
                if replacement[at:at + len(original)] != original:
                    raise ValueError('Overlapping or changed original text')
                pt = row['translation']
                # Some old batches dropped the voice marker from the editable
                # cell. Preserve the engine's original control marker.
                for marker in re.findall(r'\(?[SBC]\d{6}[a-z]?\)', row['original']):
                    if marker not in pt:
                        if not marker.startswith('(') and (at == 0 or replacement[at - 1:at] != b'('):
                            marker = '(' + marker
                        elif marker.startswith('(') and at > 0 and replacement[at - 1:at] == b'(':
                            marker = marker[1:]
                        pt = marker + pt
                if tss:
                    pt = reflow(pt)
                replacement = replacement[:at] + encode(pt) + replacement[at + len(original):]
            replacement = replacement.rstrip(b' ')
        except (ValueError, UnicodeError) as exc:
            blocked.extend(dict(r, reason=str(exc)) for r in group)
            continue
        refs = []
        old_relative = start - pool
        if rebuild_pool is not None:
            rebuilt.append((start, end, replacement, group))
            continue
        if len(replacement) <= end - start:
            destination = start
            out[start:end] = replacement.ljust(end - start, b' ')
        else:
            if tss:
                # Typed bytecode string operands; integer pushes are NOT patched.
                for pos in range(32, pool - 7, 4):
                    if data[pos:pos + 4] == b'\0\0\x82\x02' and struct.unpack_from('<I', data, pos + 4)[0] == old_relative:
                        refs.append(pos + 4)
                # Data references live outside string bodies, not in bytecode.
                for pos in range((pool + 3) & ~3, len(data) - 3, 4):
                    if struct.unpack_from('<I', data, pos)[0] != old_relative:
                        continue
                    if any(a <= pos < z for a, z in occupied):
                        continue
                    refs.append(pos)
            else:
                for pos in (reference_fields if reference_fields is not None
                            else range(reference_start, min_text - 3, 4)):
                    if struct.unpack_from('<I', data, pos)[0] == start:
                        refs.append(pos)
            if not refs:
                if data[:4] == b'd\x00{\x00' and start == 0x915:
                    # Unreferenced dead string at the end of TODS3_CureStoneData.dat
                    pass
                else:
                    blocked.extend(dict(r, reason='Expansion requires a proven string reference') for r in group)
                    continue
            destination = len(out)
            out.extend(replacement + b'\0')
            out.extend(b'\0' * (-len(out) % 4))
            value = destination - pool if tss else destination
            for pos in refs:
                struct.pack_into('<I', out, pos, value)
        for row in group:
            applied.append(dict(row, compiled_source=source,
                                string_start=start, destination=destination,
                                string_hex=replacement.hex(), reference_positions=refs))
    if tss:
        struct.pack_into('<I', out, 24, len(out) - pool)
    if rebuild_pool is not None:
        # Outline paragraphs contain NUL-delimited display lines; only the
        # paragraph has a table reference. Rebuild the whole string pool and
        # relocate all original metadata references, including interior ones.
        result = bytearray(data[:rebuild_pool])
        cursor = rebuild_pool
        spans = []
        for start, end, replacement, group in rebuilt:
            result.extend(data[cursor:start])
            destination = len(result)
            result.extend(replacement)
            spans.append((start, end, destination, len(replacement)))
            for row in group:
                applied.append(dict(row, compiled_source=source, string_start=start,
                                    destination=destination, string_hex=replacement.hex(),
                                    reference_positions=['rebuilt_table']))
            cursor = end
        result.extend(data[cursor:])
        def relocate(pos):
            shift = 0
            for a, z, dest, length in spans:
                if pos < a: break
                if pos < z: return dest + min(pos - a, length)
                shift += length - (z - a)
            return pos + shift
        if data[:4] in (b'OTLE', b'BTLM') or data[4:8] == b'STRT':
            for at in range(8, rebuild_pool - 3, 4):
                value = struct.unpack_from('<I', data, at)[0]
                if rebuild_pool <= value < len(data):
                    struct.pack_into('<I', result, at, relocate(value))
        else:
            table_start = struct.unpack_from('<I', data, 16)[0]
            if (rebuild_pool - table_start) % 20:
                raise ValueError('Unexpected TITL record layout')
            for at in range(table_start, rebuild_pool, 20):
                for field in (at, at + 4):
                    value = struct.unpack_from('<I', data, field)[0]
                    if value < len(data) - rebuild_pool:
                        struct.pack_into('<I', result, field, relocate(rebuild_pool + value) - rebuild_pool)
        out = result
    return bytes(out)


def patch_archive(index, payload, replacements):
    """Rebuild the paired FPS4 archive, retaining names and the sentinel."""
    out_index = bytearray(index)
    count, head = struct.unpack_from('<II', index, 4)
    stride = struct.unpack_from('<H', index, 16)[0]
    result = bytearray()
    for i in range(count):
        at = head + i * stride
        off, stored, size = struct.unpack_from('<III', index, at)
        name = index[at + 12:at + stride].split(b'\0')[0].decode('ascii')
        if not stored or off == 0xffffffff:
            if not name:
                struct.pack_into('<III', out_index, at, len(result), 0, 0)
            continue
        body = replacements.get(name, payload[off:off + size])
        result.extend(b'\0' * (-len(result) % 16))
        new_off = len(result)
        result.extend(body)
        result.extend(b'\0' * (-len(result) % 16))
        struct.pack_into('<III', out_index, at, new_off, len(result) - new_off, len(body))
    return bytes(out_index), bytes(result)


def patch_font(data):
    """Add accented glyphs to the reachable catch-all map and rebuild links."""
    from nftr_ptbr_injector import _draw_accent
    head, count = struct.unpack_from('<HH', data, 12)
    chunks = []
    at = head
    cmap = {}
    for _ in range(count):
        size = struct.unpack_from('<I', data, at + 4)[0]
        chunks.append([at, bytearray(data[at:at + size])])
        if data[at:at + 4] == b'PAMC':
            first, last, typ = struct.unpack_from('<HHI', data, at + 8)
            if typ == 0:
                glyph = struct.unpack_from('<H', data, at + 20)[0]
                for cp in range(first, last + 1):
                    cmap[cp] = glyph + cp - first
            elif typ == 1:
                for j, cp in enumerate(range(first, last + 1)):
                    g = struct.unpack_from('<H', data, at + 20 + j * 2)[0]
                    if g != 65535: cmap[cp] = g
            elif typ == 2:
                n = struct.unpack_from('<H', data, at + 20)[0]
                for j in range(n):
                    cp, g = struct.unpack_from('<HH', data, at + 22 + j * 4)
                    cmap[cp] = g
        at += size
    glyph_chunk = next(c for _, c in chunks if c[:4] == b'PLGC')
    widths = next(c for _, c in chunks if c[:4] == b'HDWC')
    width, height, cell_size = struct.unpack_from('<BBH', glyph_chunk, 8)
    bpp = glyph_chunk[14]
    glyph_count = (len(glyph_chunk) - 16) // cell_size
    # CGLP has alignment padding, which is not part of the final glyph cell.
    del glyph_chunk[16 + glyph_count * cell_size:]
    original_width_count = struct.unpack_from('<H', widths, 10)[0] - struct.unpack_from('<H', widths, 8)[0] + 1
    del widths[16 + original_width_count * 3:]
    entries = []
    for char, cp in CHAR_CODES.items():
        if cp in cmap:
            raise ValueError('Private font code collision')
        base_char = {'º': 'o', 'ª': 'a'}.get(char, unicodedata.normalize('NFKD', char)[0])
        if ord(base_char) not in cmap:
            raise ValueError('Missing ASCII glyph')
        g = cmap[ord(base_char)]
        cell = bytearray(glyph_chunk[16 + g * cell_size:16 + (g + 1) * cell_size])
        advance = widths[16 + g * 3:19 + g * 3]
        accent = ('cedilla' if char.lower() == 'ç' else 'tilde' if char.lower() in 'ãõ'
                  else 'circ' if char.lower() in 'âêô' else 'grave' if char.lower() == 'à'
                  else 'acute')
        if char in 'ºª':
            from nftr_ptbr_injector import _get_pixel, _set_pixel
            old_cell = bytes(cell)
            cell = bytearray(len(cell))
            for y in range(max(1, height * 2 // 3)):
                for x in range(max(1, advance[1] * 2 // 3)):
                    _set_pixel(cell, width, bpp, x, y,
                               _get_pixel(old_cell, width, bpp, min(width - 1, x * 3 // 2), min(height - 1, y * 3 // 2)))
        elif char.lower() == 'ü':
            # Existing drawing helper has no diaeresis: draw its two dots.
            from nftr_ptbr_injector import _set_pixel
            for x in (max(1, advance[1] // 2 - 1), min(width - 1, advance[1] // 2 + 1)):
                _set_pixel(cell, width, bpp, x, 0, (1 << bpp) - 1)
        else:
            if char.isupper() and accent != 'cedilla':
                from nftr_ptbr_injector import _get_pixel, _set_pixel
                # Reserve two rows above capitals for a separate accent.
                old_cell = bytes(cell)
                ink_rows = [y for y in range(height) if any(
                    _get_pixel(old_cell, width, bpp, x, y) for x in range(width))]
                shift = max(0, 2 - min(ink_rows)) if ink_rows else 0
                if shift and max(ink_rows) + shift < height:
                    cell = bytearray(cell_size)
                    for y in ink_rows:
                        for x in range(width):
                            _set_pixel(cell, width, bpp, x, y + shift,
                                       _get_pixel(old_cell, width, bpp, x, y))
            _draw_accent(cell, width, height, bpp, advance[1], accent)
        glyph_chunk.extend(cell)
        widths.extend(advance)
        entries.append((cp, glyph_count + len(entries)))
    glyph_chunk.extend(b'\0' * (-len(glyph_chunk) % 4))
    struct.pack_into('<I', glyph_chunk, 4, len(glyph_chunk))
    widths.extend(b'\0' * (-len(widths) % 4))
    struct.pack_into('<I', widths, 4, len(widths))
    first_glyph = struct.unpack_from('<H', widths, 8)[0]
    struct.pack_into('<H', widths, 10, first_glyph + original_width_count + len(entries) - 1)
    # The original scan map covers 0000-FFFF. A new map appended after it is
    # unreachable to the first-matching-range lookup used by the runtime.
    scan = next(c for _, c in chunks if c[:4] == b'PAMC'
                and struct.unpack_from('<HHI', c, 8) == (0, 65535, 2))
    previous_count = struct.unpack_from('<H', scan, 20)[0]
    previous = [struct.unpack_from('<HH', scan, 22 + i * 4)
                for i in range(previous_count)]
    combined = sorted(previous + entries)
    scan[:] = scan[:20] + struct.pack('<H', len(combined))
    for cp, glyph in combined: scan.extend(struct.pack('<HH', cp, glyph))
    scan.extend(b'\0' * (-len(scan) % 4))
    struct.pack_into('<I', scan, 4, len(scan))
    offsets, cursor = {}, head
    for old, chunk in chunks:
        if old is not None: offsets[old + 8] = cursor + 8
        cursor += len(chunk)
    cmap_chunks = [c for _, c in chunks if c[:4] == b'PAMC']
    chunk_offsets = {}; cursor = head
    for _, chunk in chunks:
        chunk_offsets[id(chunk)] = cursor + 8; cursor += len(chunk)
    for _, chunk in chunks:
        if chunk[:4] == b'FNIF':
            for pos in (16, 20, 24):
                pointer = struct.unpack_from('<I', chunk, pos)[0]
                struct.pack_into('<I', chunk, pos, offsets[pointer])
        elif chunk[:4] == b'HDWC':
            pointer = struct.unpack_from('<I', chunk, 12)[0]
            if pointer: struct.pack_into('<I', chunk, 12, offsets[pointer])
    for i, chunk in enumerate(cmap_chunks):
        struct.pack_into('<I', chunk, 16, chunk_offsets[id(cmap_chunks[i + 1])] if i + 1 < len(cmap_chunks) else 0)
    result = bytearray(data[:head])
    for _, chunk in chunks: result.extend(chunk)
    struct.pack_into('<I', result, 8, len(result))
    struct.pack_into('<H', result, 14, len(chunks))
    return bytes(result)


def crc16(data):
    value = 65535
    for c in data:
        value ^= c
        for _ in range(8): value = (value >> 1) ^ (0xa001 if value & 1 else 0)
    return value


def write_rom(base, replacements, output, exec_replacements=None):
    ids = file_ids(base)
    fat, size = struct.unpack_from('<II', base, 0x48)
    spans = [struct.unpack_from('<II', base, fat + i * 8) for i in range(size // 8)]
    changed_ids = {ids[name]: data for name, data in replacements.items()}
    first = min(spans[fid][0] for fid in changed_ids)
    result = bytearray(base)
    if exec_replacements:
        if 'arm9' in exec_replacements:
            arm9_off, _, arm9_ram, arm9_size = struct.unpack_from('<4I', base, 0x20)
            ov_off = struct.unpack_from('<I', base, 0x50)[0]
            comp_arm9 = bytearray(cc.compress(exec_replacements['arm9'], isArm9=True))
            struct.pack_into('<I', comp_arm9, 0xBB4, arm9_ram + len(comp_arm9))
            arm9_buf = bytearray(exec_replacements['arm9'])
            struct.pack_into('<I', arm9_buf, 0xBB4, arm9_ram + len(comp_arm9))
            exec_replacements['arm9'] = bytes(arm9_buf)
            if arm9_off + len(comp_arm9) > ov_off:
                raise ValueError('Compressed ARM9 exceeds slot before overlay table')
            clear_end = max(arm9_off + arm9_size, arm9_off + len(comp_arm9))
            result[arm9_off:clear_end] = comp_arm9.ljust(clear_end - arm9_off, b'\xff')
            struct.pack_into('<I', result, 0x2c, len(comp_arm9))
        ov_off, ov_size = struct.unpack_from('<II', base, 0x50)
        arm7_off = struct.unpack_from('<I', base, 0x30)[0]
        for i in range(ov_size // 32):
            ov_id, _, _, _, _, _, fid, comp_flags = struct.unpack_from('<8I', base, ov_off + i * 32)
            key = f'ov_{ov_id:02d}'
            if key not in exec_replacements:
                continue
            comp_ov = cc.compress(exec_replacements[key], isArm9=False)
            a, z = spans[fid]
            next_start = spans[fid + 1][0] if fid + 1 < ov_size // 32 else arm7_off
            if a + len(comp_ov) > next_start:
                raise ValueError(f'Compressed {key} exceeds in-place slot ({len(comp_ov)} > {next_start - a})')
            clear_end = max(z, a + len(comp_ov))
            result[a:clear_end] = comp_ov.ljust(clear_end - a, b'\xff')
            struct.pack_into('<II', result, fat + fid * 8, a, a + len(comp_ov))
            new_flags = (comp_flags & 0xFF000000) | len(comp_ov)
            struct.pack_into('<I', result, ov_off + i * 32 + 28, new_flags)
            spans[fid] = (a, a + len(comp_ov))
    cursor = first
    for fid in sorted(range(len(spans)), key=lambda i: spans[i][0]):
        a, z = spans[fid]
        if a < first or z <= a:
            continue
        cursor = (cursor + 511) & ~511
        data = changed_ids.get(fid, base[a:z])
        if cursor + len(data) > len(base):
            raise ValueError('Rebuilt NitroFS exceeds existing ROM capacity')
        result[cursor:cursor + len(data)] = data
        struct.pack_into('<II', result, fat + fid * 8, cursor, cursor + len(data))
        cursor += len(data)
    struct.pack_into('<I', result, 0x80, cursor)
    struct.pack_into('<H', result, 0x15e, crc16(result[:0x15e]))
    # Verify every FAT file, including every unchanged movie and overlay.
    for fid, (a, z) in enumerate(spans):
        if z <= a: continue
        x, y = struct.unpack_from('<II', result, fat + fid * 8)
        expected = changed_ids.get(fid, result[a:z] if fid < 31 else base[a:z])
        if result[x:y] != expected:
            raise ValueError(f'File verification failed: {fid}')
    for off_field, size_field in [(0x30, 0x3c)]:
        a = struct.unpack_from('<I', base, off_field)[0]
        n = struct.unpack_from('<I', base, size_field)[0]
        if result[a:a + n] != base[a:a + n]: raise ValueError('ARM7 executable changed')
    output.write_bytes(result)
    return cursor


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--reuse', type=Path, help='Reuse compressed scripts only after exact decompressed comparison')
    parser.add_argument('--md-dir', type=Path, help='Read a staged Markdown folder for validation before migration')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    original_rom = (BASE / 'rom/Tales of Hearts - Anime Movie Edition (EN).nds').read_bytes()
    original = rom_files(original_rom)
    cached_scripts = {}
    if args.reuse:
        cached_files = rom_files(args.reuse.read_bytes())
        cached_outer = {n: d for n, _, _, _, d in fps4(cached_files['m/m.b'], cached_files['m/m.dat'])}
        for name in cached_outer:
            if name.endswith('.B'):
                for child, _, _, _, packed in fps4(cached_outer[name], cached_outer[name[:-2] + '.MAPBIN']):
                    if child.endswith('.SCP'):
                        cached_scripts['m/' + name + '/' + child] = packed
        for child, _, _, _, packed in fps4(cached_files['fc/fcscr.b'], cached_files['fc/fcscr.dat']):
            if child.endswith('.FCBIN'):
                cached_scripts['fc/' + child] = packed
    outer = {name: data for name, _, _, _, data in fps4(original['m/m.b'], original['m/m.dat'])}
    fc_children = list(fps4(original['fc/fcscr.b'], original['fc/fcscr.dat']))
    sources, map_members, archives = decomp_exec(original_rom), defaultdict(list), {}
    protect_executable_empty_strings(original_rom,sources)
    for child, _, _, _, data in fc_children:
        if child.endswith('.FCBIN'):
            sources['fc/' + child] = unpack(data)[0]
    for name in outer:
        if name.endswith('.B'):
            payload = outer[name[:-2] + '.MAPBIN']
            children = list(fps4(outer[name], payload))
            archives[name] = children
            for child, off, _, _, data in children:
                if child.endswith('.SCP'):
                    key = 'm/' + name + '/' + child
                    sources[key] = unpack(data)[0]
                    map_members[name[:-2] + '.MAPBIN'].append((key, off))
    basename = defaultdict(list)
    for name in original: basename[Path(name).name].append(name)
    rows = rows_from_md(args.md_dir)
    selected, blocked, superseded = {}, [], []
    for row in rows:
        source, at = row['source'], row['offset']
        if source in sources:
            choices = [source]
        elif source.endswith('.MAPBIN'):
            choices = [key for key, off in map_members.get(source, []) if off == 0]
        elif source in original or len(basename[source]) == 1:
            key = source if source in original else basename[source][0]
            if original[key][:1] in (b'\x10', b'\x11') or original[key][:4] in (b'FPS4', b'\x80\0\0\x20'):
                blocked.append(dict(row, reason='Legacy row points into compressed/container/audio bytes'))
                continue
            sources.setdefault(key, original[key]); choices = [key]
        else:
            choices = []
        needle = row['original'].encode('cp932')
        matches = []
        for key in choices:
            data = sources[key]
            if data[at:at + len(needle)] == needle: matches.append((key, at))
        if not matches and source.endswith('.MAPBIN') and row['md'].startswith('lote-72'):
            for key, _ in map_members.get(source, []):
                pos = sources[key].find(needle)
                if pos >= 0 and sources[key].find(needle, pos + 1) < 0: matches.append((key, pos))
        if len(matches) != 1:
            blocked.append(dict(row, reason='Original text/source/offset mismatch'))
            continue
        key, pos = matches[0]
        row.update(resolved_source=key, resolved_offset=pos)
        identity = key, pos, needle
        if identity in selected: superseded.append(selected[identity])
        selected[identity] = row
    grouped = defaultdict(list)
    for row in selected.values(): grouped[row['resolved_source']].append(row)
    applied, modified = [], {}
    for i, (source, entries) in enumerate(sorted(grouped.items()), 1):
        patched = patch_strings(sources[source], entries, source, applied, blocked)
        if patched != sources[source]: modified[source] = patched
        if i % 30 == 0: print(f'Patched sources: {i}/{len(grouped)}', flush=True)
    superseded.extend(row for row in selected.values() if row.get('overlap_superseded'))
    exec_replacements = {k: v for k, v in modified.items() if k == 'arm9' or k.startswith('ov_')}
    replacements = {k: v for k, v in modified.items() if not k.startswith('m/') and not k.startswith('fc/') and k not in exec_replacements}
    fc_changed = {}
    for child, _, _, _, _ in fc_children:
        key = 'fc/' + child
        if key in modified:
            cached = cached_scripts.get(key)
            fc_changed[child] = cached if cached and unpack(cached)[0] == modified[key] else compress(modified[key])
    if fc_changed:
        fc_index, fc_payload = patch_archive(original['fc/fcscr.b'], original['fc/fcscr.dat'], fc_changed)
        replacements['fc/fcscr.b'], replacements['fc/fcscr.dat'] = fc_index, fc_payload
    outer_changes = {}
    for name, children in archives.items():
        changed = {}
        for child, _, _, _, _ in children:
            key = 'm/' + name + '/' + child
            if key in modified:
                cached = cached_scripts.get(key)
                changed[child] = cached if cached and unpack(cached)[0] == modified[key] else compress(modified[key])
        if changed:
            index, payload = patch_archive(outer[name], outer[name[:-2] + '.MAPBIN'], changed)
            outer_changes[name] = index
            outer_changes[name[:-2] + '.MAPBIN'] = payload
    if outer_changes:
        index, payload = patch_archive(original['m/m.b'], original['m/m.dat'], outer_changes)
        replacements['m/m.b'], replacements['m/m.dat'] = index, payload
    for name in ['trialFont10.NFTR', 'trialFont12.NFTR']:
        replacements[name] = patch_font(original[name])
    # Verify every inserted string through the rebuilt nested archives.
    verified_sources = {**replacements, **exec_replacements}
    if fc_changed:
        for child, _, _, _, packed in fps4(replacements['fc/fcscr.b'], replacements['fc/fcscr.dat']):
            key = 'fc/' + child
            if key in modified: verified_sources[key] = unpack(packed)[0]
    if outer_changes:
        final_outer = {n: d for n, _, _, _, d in fps4(replacements['m/m.b'], replacements['m/m.dat'])}
        for name in archives:
            if name not in outer_changes: continue
            for child, _, _, _, packed in fps4(final_outer[name], final_outer[name[:-2] + '.MAPBIN']):
                key = 'm/' + name + '/' + child
                if key in modified: verified_sources[key] = unpack(packed)[0]
    for row in applied:
        body = verified_sources.get(row['compiled_source'], sources[row['compiled_source']])
        needle = bytes.fromhex(row['string_hex']); dest = row['destination']
        if body[dest:dest + len(needle)] != needle:
            raise ValueError(f'Inserted text verification failed: {row["md"]}:{row["line"]} {row["compiled_source"]} at {dest:#x}; expected={needle.hex()} actual={body[dest:dest+len(needle)].hex()}')
    base = args.base.read_bytes()
    out_rom = args.output / 'Tales_of_Hearts_PTBR_HQ_TEXT_TEST.nds'
    used = write_rom(base, replacements, out_rom, exec_replacements=exec_replacements)
    out_bytes = out_rom.read_bytes()
    final_files = rom_files(out_bytes)
    for name, body in replacements.items():
        if final_files[name] != body: raise ValueError('Final ROM file differs')
    if exec_replacements:
        final_execs = decomp_exec(out_bytes)
        for name, body in exec_replacements.items():
            if final_execs[name] != body: raise ValueError(f'Final executable {name} differs after BLZ round-trip')
    base_files = rom_files(base)
    for movie in ['MOV001', 'MOV002', 'MOV006', 'MOV007']:
        key = 'movie/' + movie + '.mods'
        if base_files[key] != final_files[key]: raise ValueError('HQ movie changed')
    for name, value in [('applied.json', applied), ('blocked.json', blocked), ('superseded.json', superseded)]:
        (args.output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    summary = dict(md_rows=len(rows), selected_rows=len(selected), applied_rows=len(applied),
                   blocked_rows=len(blocked), superseded_rows=len(superseded),
                   blocked_reasons=dict(Counter(r['reason'] for r in blocked)),
                   changed_files=list(replacements) + sorted(exec_replacements), used_rom_bytes=used,
                   base_sha256=hashlib.sha256(base).hexdigest(),
                   output_sha256=hashlib.sha256(out_bytes).hexdigest(),
                   hq_movies_preserved=True, hardware_tested=False)
    (args.output / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=True, indent=2), flush=True)


if __name__ == '__main__':
    main()
