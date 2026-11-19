"""Read-only ROM audit, including the paired m/*.B + *.MAPBIN archives.

No third-party dependencies. Outputs are diagnostic corpora, not builder input.
"""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import re
import struct

from toh_extended_map_extractor import decode_lz10, collect_dialogue


def fps4(index, payload):
    if index[:4] != b'FPS4':
        raise ValueError('Missing FPS4 signature')
    count, head = struct.unpack_from('<II', index, 4)
    stride, mask = struct.unpack_from('<HH', index, 16)
    if stride < 4 or head + count * stride > len(index) or not mask & 1:
        raise ValueError('Invalid FPS4 table')
    entries = []
    for i in range(count):
        at = head + i * stride
        off = struct.unpack_from('<I', index, at)[0]
        cursor = at + 4
        stored = struct.unpack_from('<I', index, cursor)[0] if mask & 2 else None
        cursor += 4 if mask & 2 else 0
        size = struct.unpack_from('<I', index, cursor)[0] if mask & 4 else stored
        cursor += 4 if mask & 4 else 0
        name = (index[cursor:at + stride].split(b'\0')[0].decode('ascii')
                if mask & 8 else f'member_{i:04d}.bin')
        entries.append((name, off, stored, size))
    for i, (name, off, stored, size) in enumerate(entries):
        if off == 0xffffffff:
            continue
        if stored is None:
            # Offset-only tables have a final boundary entry, not a final file.
            if i + 1 == len(entries):
                continue
            stored = entries[i + 1][1] - off
            size = stored
        if not stored:
            continue
        if stored < 0 or off + stored > len(payload):
            raise ValueError(f'Member outside payload: {name}')
        yield name, off, stored, size, payload[off:off + stored]


def rom_files(rom):
    fnt_off, fnt_size, fat_off, fat_size = struct.unpack_from('<4I', rom, 0x40)
    fnt = rom[fnt_off:fnt_off + fnt_size]
    def walk(directory=0, prefix=''):
        off, fid, _ = struct.unpack_from('<IHH', fnt, directory * 8)
        while fnt[off]:
            n = fnt[off]
            off += 1
            name = fnt[off:off + (n & 127)].decode('ascii')
            off += n & 127
            if n & 128:
                child = struct.unpack_from('<H', fnt, off)[0] & 4095
                off += 2
                yield from walk(child, prefix + name + '/')
            else:
                if fid * 8 + 8 > fat_size:
                    raise ValueError('Invalid FAT id')
                start, end = struct.unpack_from('<II', rom, fat_off + fid * 8)
                if not 0 <= start <= end <= len(rom):
                    raise ValueError('Invalid FAT span')
                yield prefix + name, rom[start:end]
                fid += 1
    return dict(walk())


def lz11(data):
    size = int.from_bytes(data[1:4], 'little')
    pos = 4
    if not size:
        size = int.from_bytes(data[4:8], 'little')
        pos = 8
    if not 0 < size <= 64 * 1024 * 1024:
        raise ValueError('Invalid LZ11 size')
    out = bytearray()
    while len(out) < size:
        flags = data[pos]
        pos += 1
        for bit in range(7, -1, -1):
            if len(out) >= size:
                break
            if not flags & (1 << bit):
                out.append(data[pos]); pos += 1
                continue
            a = data[pos]; pos += 1
            tag = a >> 4
            b = data[pos]; pos += 1
            if tag == 0:
                c = data[pos]; pos += 1
                length = ((a & 15) << 4 | b >> 4) + 0x11
                dist = ((b & 15) << 8 | c) + 1
            elif tag == 1:
                c, d = data[pos:pos + 2]; pos += 2
                length = ((a & 15) << 12 | b << 4 | c >> 4) + 0x111
                dist = ((c & 15) << 8 | d) + 1
            else:
                length = tag + 1
                dist = ((a & 15) << 8 | b) + 1
            if dist > len(out):
                raise ValueError('Invalid LZ11 reference')
            for _ in range(length):
                out.append(out[-dist])
    return bytes(out[:size])


def unpack(data):
    if data[:1] == b'\x10':
        return decode_lz10(data)[0], 'LZ10'
    if data[:1] == b'\x11':
        return lz11(data), 'LZ11'
    return data, 'raw'


def md_index(folder):
    entries = defaultdict(list)
    failures = []
    files = [f for f in folder.glob('*.md') if f.is_file()]
    for f in files:
        try:
            lines = f.read_text(encoding='utf-8-sig').splitlines()
        except (OSError, UnicodeError) as exc:
            failures.append({'source': str(f), 'error': str(exc)})
            continue
        for line_no, line in enumerate(lines, 1):
            m = re.match(r'^\|\s*`([^`]+)`\s*\|\s*`(0x[\da-fA-F]+)`\s*\|', line)
            if not m:
                continue
            cells = re.split(r'(?<!\\)\|', line[m.end():])
            if not cells:
                continue
            original = cells[0].strip().replace(r'\|', '|')
            entries[(m[1], int(m[2], 16))].append((f.name, line_no, original))
    return files, entries, failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    base = Path(__file__).resolve().parents[1]
    rom = args.rom.read_bytes()
    files = rom_files(rom)
    md_files, md, md_failures = md_index(base / 'ARQUIVOS md')
    stats = Counter()
    errors, members, voices, pools, raw_candidates, archives = [], [], [], [], [], []
    missing_lines = []
    other_tss = []
    other_pools = []
    errors.extend(md_failures)
    used_md = set()
    mapdata = dict((n, (off, stored, size, data)) for n, off, stored, size, data
                   in fps4(files['m/m.b'], files['m/m.dat']))
    maps = sorted(n for n in mapdata if n.endswith('.B'))
    for map_no, name in enumerate(maps, 1):
        stem = Path(name).stem
        payload_name = stem + '.MAPBIN'
        try:
            inner = list(fps4(mapdata[name][3], mapdata[payload_name][3]))
        except Exception as exc:
            errors.append({'source': name, 'error': str(exc)})
            continue
        for child, off, stored, size, packed in inner:
            source = f'm/{name}/{child}'
            try:
                data, codec = unpack(packed)
            except Exception as exc:
                errors.append({'source': source, 'error': str(exc)})
                continue
            stats[Path(child).suffix] += 1
            stats[codec] += 1
            row = {'map': name, 'member': child, 'member_offset': off,
                   'stored_size': stored, 'index_size': size, 'decoded_size': len(data),
                   'codec': codec, 'magic': data[:4].hex(), 'voice_count': 0,
                   'ascii_lines': 0, 'existing_lines': 0, 'missing_lines': 0}
            if data[:4] == b'TSS\0':
                stats['tss'] += 1
                target = args.output / 'scripts' / stem / child
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
                pool_start = struct.unpack_from('<I', data, 12)[0]
                pool_size = struct.unpack_from('<I', data, 24)[0]
                if not 32 <= pool_start <= pool_start + pool_size <= len(data):
                    errors.append({'source': source, 'error': 'Invalid TSS string pool'})
                    members.append(row)
                    continue
                pool_end = pool_start + pool_size
                for match in re.finditer(rb'[^\x00]+', data[pool_start:pool_end]):
                    raw = match[0]
                    if len(raw) < 3:
                        continue
                    text = raw.decode('cp932', errors='backslashreplace')
                    pools.append({'source': source, 'offset': pool_start + match.start(),
                                  'text': text,
                                  'japanese_candidate': bool(re.search('[\u3040-\u30ff\u4e00-\u9fff]', text))})
                for match in re.finditer(rb'[\x20-\x7e]{3,}', data[pool_start:pool_end]):
                    raw = match[0]
                    if not re.search(rb'[A-Za-z]', raw):
                        continue
                    pos = pool_start + match.start()
                    text = raw.decode('ascii')
                    # Legacy MAPBIN dumps actually contain only the member at offset zero.
                    keys = [(child, pos), (source, pos)]
                    if off == 0:
                        keys.append((payload_name, pos))
                    matches = [(key, entry) for key in keys for entry in md.get(key, [])
                               if entry[2] == text.strip()]
                    found = bool(matches)
                    if not found:
                        missing_lines.append({'source': source, 'offset': pos, 'text': text})
                    used_md.update(key for key, _ in matches)
                    row['ascii_lines'] += 1
                    row['existing_lines' if found else 'missing_lines'] += 1
                for v in collect_dialogue(data, len(data)):
                    pos = int(v['offset'], 16)
                    if not pool_start <= pos < pool_end:
                        continue
                    v.update(source=source, member_offset=off)
                    v.pop('beyond_declared_size', None)
                    v.pop('marker_offset', None)
                    voices.append(v)
                    row['voice_count'] += 1
                row['pool_start'] = pool_start
                row['pool_size'] = pool_size
            members.append(row)
        if map_no % 50 == 0:
            print(f'Maps: {map_no}/{len(maps)}', flush=True)

    def scan_asset(source, packed, depth=0):
        try:
            data, codec = unpack(packed)
        except Exception as exc:
            errors.append({'source': source, 'error': str(exc)})
            return
        if data[:4] == b'TSS\0':
            start, length = struct.unpack_from('<I', data, 12)[0], struct.unpack_from('<I', data, 24)[0]
            if not 32 <= start <= start + length <= len(data):
                errors.append({'source': source, 'error': 'Invalid secondary TSS pool'})
                return
            out = args.output / 'other_scripts'
            out.mkdir(exist_ok=True)
            safe_name = hashlib.sha256(source.encode()).hexdigest()[:12] + '_' + Path(source).name
            (out / safe_name).write_bytes(data)
            text_rows = list(re.finditer(rb'[ -~]{3,}', data[start:start + length]))
            matches = 0
            for match in text_rows:
                pos = start + match.start()
                text = match[0].decode('ascii')
                if not re.search('[A-Za-z]', text):
                    continue
                found = any(e[2] == text.strip() for key in [(Path(source).name, pos), (source, pos)]
                            for e in md.get(key, []))
                matches += found
                other_pools.append({'source': source, 'offset': pos, 'text': text, 'in_md': found})
            other_tss.append({'source': source, 'decoded_size': len(data),
                              'pool_start': start, 'pool_size': length,
                              'ascii_candidates': sum(r['source'] == source for r in other_pools),
                              'matching_md_lines': matches,
                              'voice_occurrences': len(collect_dialogue(data, len(data)))})
        if data[:4] == b'FPS4':
            if depth >= 12:
                errors.append({'source': source, 'error': 'Recursion limit'})
                return
            try:
                children = list(fps4(data, data))
                archives.append({'source': source, 'members': len(children), 'nested': True})
                for child, off, stored, size, content in children:
                    scan_asset(source + '/' + child, content, depth + 1)
            except Exception as exc:
                errors.append({'source': source, 'error': str(exc)})
            return
        for match in re.finditer(rb'[ -~]{12,}', data):
            text = match[0].decode('ascii')
            if len(re.findall(r'[A-Za-z]{2,}', text)) >= 3:
                raw_candidates.append({'source': source, 'offset': match.start(), 'text': text})

    # Inventory all NitroFS files. Voice and movie bytes are assets, not scripts.
    inventory = []
    for name, data in sorted(files.items()):
        kind = ('CRI audio' if data[:4] == b'\x80\0\0\x20' and b'(c)CRI' in data[:128]
                else 'movie' if name.endswith('.mods')
                else 'FPS4 index/container' if data[:4] == b'FPS4'
                else 'other')
        inventory.append({'path': name, 'size': len(data), 'kind': kind,
                          'magic': data[:4].hex()})
        paired_payload = name.endswith('.dat') and name[:-4] + '.b' in files
        if kind == 'FPS4 index/container' and not paired_payload:
            partner = name[:-2] + '.dat' if name.lower().endswith('.b') else None
            payload = files.get(partner, data)
            try:
                inner = list(fps4(data, payload))
                archives.append({'source': name, 'partner': partner if partner in files else None,
                                 'members': len(inner)})
                # m/ has already been expanded by its two levels above.
                if name != 'm/m.b':
                    for child, off, stored, size, packed in inner:
                        scan_asset(f'{name}/{child}', packed)
            except Exception as exc:
                errors.append({'source': name, 'error': str(exc)})
        if kind != 'other' or name.startswith('m/') or paired_payload:
            continue
        scan_asset(name, data)

    for name, off_field, size_field in [('arm9', 0x20, 0x2c), ('arm7', 0x30, 0x3c)]:
        off = struct.unpack_from('<I', rom, off_field)[0]
        size = struct.unpack_from('<I', rom, size_field)[0]
        for match in re.finditer(rb'[ -~]{12,}', rom[off:off + size]):
            text = match[0].decode('ascii')
            if len(re.findall(r'[A-Za-z]{2,}', text)) >= 3:
                raw_candidates.append({'source': name + ' (raw, BLZ not decoded)',
                                       'offset': match.start(), 'text': text})

    overlays = []
    ov_off, ov_size = struct.unpack_from('<II', rom, 0x50)
    fat_off = struct.unpack_from('<I', rom, 0x48)[0]
    for at in range(ov_off, ov_off + ov_size, 32):
        entry = struct.unpack_from('<8I', rom, at)
        begin, end = struct.unpack_from('<II', rom, fat_off + entry[6] * 8)
        overlays.append({'id': entry[0], 'ram_size': entry[2], 'file_id': entry[6],
                         'stored_bytes': end - begin,
                         'compressed_flag': bool(entry[7] & 0x1000000)})

    def json_file(name, value):
        (args.output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    def jsonl_file(name, values):
        with (args.output / name).open('w', encoding='utf-8') as f:
            for value in values:
                f.write(json.dumps(value, ensure_ascii=False) + '\n')
    summary = {'rom': str(args.rom.resolve()), 'sha256': hashlib.sha256(rom).hexdigest(),
               'rom_bytes': len(rom), 'nitrofs_files': len(files),
               'inventory_kinds': dict(Counter(r['kind'] for r in inventory)),
               'map_archives': len(maps), 'members': len(members), 'member_stats': dict(stats),
               'scripts_with_voices': sum(m['voice_count'] > 0 for m in members),
               'scripts_at_nonzero_offset': sum(m['magic'] == '54535300' and m['member_offset'] > 0 for m in members),
               'voice_occurrences': len(voices), 'unique_voice_ids': len(set(v['id'] for v in voices)),
               'pool_entries': len(pools), 'japanese_pool_candidates': sum(p['japanese_candidate'] for p in pools),
               'ascii_pool_lines': sum(m['ascii_lines'] for m in members),
               'existing_ascii_pool_lines': sum(m['existing_lines'] for m in members),
               'missing_ascii_pool_lines': sum(m['missing_lines'] for m in members),
               'md_files': len(md_files), 'md_offset_keys': len(md), 'md_matched_keys': len(used_md),
               'other_text_candidates': len(raw_candidates), 'other_tss_scripts': len(other_tss),
               'other_tss_ascii_candidates': len(other_pools),
               'other_tss_matching_md_lines': sum(r['in_md'] for r in other_pools),
               'errors': len(errors),
               'limitations': ['ASCII lines and Japanese entries are candidates, not confirmed translatable boxes.',
                               'No image OCR, no movie subtitle verification, no runtime pointer validation.',
                               'ARM9/ARM7 and overlays inventoried; BLZ text not decoded.',
                               'FPS4 mask 1/3/7/15 layouts supported; unrecognized non-FPS4 containers are not decoded.',
                               'Recovered scripts are not compatible with the existing builder.']}
    summary['arm9_overlays'] = len(overlays)
    summary['arm9_compressed_overlays'] = sum(r['compressed_flag'] for r in overlays)
    json_file('overlays.json', overlays)
    json_file('summary.json', summary)
    json_file('errors.json', errors)
    json_file('archives.json', archives)
    json_file('inventory.json', inventory)
    json_file('other_tss.json', other_tss)
    jsonl_file('other_tss_strings.jsonl', other_pools)
    jsonl_file('dialogue.jsonl', voices)
    jsonl_file('missing_ascii_lines.jsonl', missing_lines)
    jsonl_file('string_pools.jsonl', pools)
    jsonl_file('other_text_candidates.jsonl', raw_candidates)
    with (args.output / 'members.csv').open('w', newline='', encoding='utf-8-sig') as f:
        fields = sorted(set().union(*(m.keys() for m in members)))
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader(); writer.writerows(members)
    print(json.dumps(summary, ensure_ascii=True, indent=2), flush=True)


if __name__ == '__main__':
    main()
