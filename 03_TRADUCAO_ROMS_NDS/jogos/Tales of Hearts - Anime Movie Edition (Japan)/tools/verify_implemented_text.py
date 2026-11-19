"""Verify translated strings and relocated pointers in the actual built ROM."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct

from toh_full_audit import rom_files, fps4, unpack
from toh_text_builder_v2 import BASE, rows_from_md, crc16, encode, decomp_exec


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('build', type=Path)
    parser.add_argument('--md-dir', type=Path)
    parser.add_argument('--resolved-from', type=Path,
                        help='Verify that all real blockers in an older build are now applied')
    args = parser.parse_args()
    folder = args.build
    path = folder / 'Tales_of_Hearts_PTBR_HQ_TEXT_TEST.nds'
    rom = path.read_bytes()
    files = rom_files(rom)
    sources = {**files, **decomp_exec(rom)}
    applied = json.loads((folder / 'applied.json').read_text('utf-8'))
    blocked = json.loads((folder / 'blocked.json').read_text('utf-8'))
    superseded = json.loads((folder / 'superseded.json').read_text('utf-8'))
    needed = {r['compiled_source'] for r in applied}
    if any(s.startswith('fc/') for s in needed):
        for name, _, _, _, data in fps4(files['fc/fcscr.b'], files['fc/fcscr.dat']):
            key = 'fc/' + name
            if key in needed:
                sources[key] = unpack(data)[0]
    outer = {n: d for n, _, _, _, d in fps4(files['m/m.b'], files['m/m.dat'])}
    for archive in sorted({s.split('/')[1] for s in needed if s.startswith('m/')}):
        for name, _, _, _, data in fps4(outer[archive], outer[archive[:-2] + '.MAPBIN']):
            key = 'm/' + archive + '/' + name
            if key in needed:
                sources[key] = unpack(data)[0]
    intro = []
    for row in applied:
        body = sources[row['compiled_source']]
        start = row['destination']
        expected = bytes.fromhex(row['string_hex'])
        if body[start:start + len(expected)] != expected:
            raise ValueError(f'Text mismatch: {row["md"]}:{row["line"]}')
        pool = struct.unpack_from('<I', body, 12)[0] if body[:4] == b'TSS\0' else 0
        for pointer in row['reference_positions']:
            if isinstance(pointer, int) and struct.unpack_from('<I', body, pointer)[0] != start - pool:
                raise ValueError(f'Relocated pointer mismatch: {row["md"]}:{row["line"]}')
        if row['compiled_source'] == 'm/FSHT00.B/FSHT00P.SCP':
            intro.append({'line': row['line'], 'translation': row['translation']})
    current = rows_from_md(args.md_dir)
    identities = {(r['md'], r['line']) for r in current}
    accounted = {(r['md'], r['line']) for r in applied + blocked + superseded}
    if identities != accounted:
        raise ValueError(f'Unaccounted rows: {sorted(identities - accounted)}')
    by_identity = {(r['md'], r['line']): r for r in current}
    for row in applied + blocked + superseded:
        live = by_identity[(row['md'], row['line'])]
        if any(row[k] != live[k] for k in ('source', 'offset', 'original', 'translation')):
            raise ValueError('Build is stale relative to Markdown sources')
    if struct.unpack_from('<H', rom, 0x15e)[0] != crc16(rom[:0x15e]):
        raise ValueError('Invalid NDS header CRC')
    if not any(r['translation'] in ('Acorde, Shing|!', 'Acorde, Shing!') for r in intro):
        raise ValueError('Missing repaired introduction line')
    resolved_blockers = []
    if args.resolved_from:
        previous = json.loads((args.resolved_from / 'blocked.json').read_text('utf-8'))
        active = {(r['md'], r['line']): r for r in applied}
        for row in previous:
            if row['reason'] == 'Legacy row points into compressed/container/audio bytes':
                continue
            identity = row['md'], row['line']
            if identity not in active:
                raise ValueError(f'Previously blocked translation still missing: {identity}')
            resolved_blockers.append({'md': row['md'], 'line': row['line'],
                                      'source': active[identity]['compiled_source']})
        original = rom_files((BASE / 'rom/Tales of Hearts - Anime Movie Edition (EN).nds').read_bytes())
        key = 'item/TODS9_ValueData.dat'
        before, after = original[key], files[key]
        table, pool = struct.unpack_from('<II', before, 4)
        if after[:table] != before[:table]:
            raise ValueError('VALU header changed during string relocation')
        for record in range(table, pool, 16):
            if after[record + 8:record + 16] != before[record + 8:record + 16]:
                raise ValueError('VALU item metadata changed')
            for field in (record, record + 4):
                dest = struct.unpack_from('<I', after, field)[0]
                if not pool <= dest < len(after) or after.find(b'\0', dest) < 0:
                    raise ValueError('VALU item pointer is invalid')
        dest = struct.unpack_from('<I', after, table)[0]
        if after[dest:after.find(b'\0', dest)] != encode('Mapa-Múndi'):
            raise ValueError('World Map translation or its live item pointer is invalid')
    result = dict(rom=str(path.resolve()), sha256=hashlib.sha256(rom).hexdigest(),
                  applied_verified=len(applied), intro_verified=len(intro),
                  all_current_rows_accounted=True, source_files_current=True,
                  relocated_pointers_verified=True, header_crc_valid=True,
                  blocked_reasons=dict(Counter(r['reason'] for r in blocked)),
                  intro=intro, emulator_visual_test=False)
    if args.resolved_from:
        result['resolved_blockers'] = resolved_blockers
        result['value_table_header_metadata_and_pointers_verified'] = True
    (folder / 'implementation_verification.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'intro'}, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
