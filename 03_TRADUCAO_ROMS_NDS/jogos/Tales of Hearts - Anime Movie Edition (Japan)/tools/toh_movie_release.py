"""Compare HQ movies and build an isolated ROM, without moving any file spans."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess

from toh_movie_quality import BASE, ENC, header

NAMES = ('MOV001', 'MOV002', 'MOV006', 'MOV007')


def file_ids(rom):
    off, size = struct.unpack_from('<II', rom, 0x40)
    fnt = rom[off:off + size]
    def walk(directory=0, prefix=''):
        pos, fid, _ = struct.unpack_from('<IHH', fnt, directory * 8)
        while fnt[pos]:
            n = fnt[pos]; pos += 1
            name = fnt[pos:pos + (n & 127)].decode('ascii'); pos += n & 127
            if n & 128:
                child = struct.unpack_from('<H', fnt, pos)[0] & 4095; pos += 2
                yield from walk(child, prefix + name + '/')
            else:
                yield prefix + name, fid
                fid += 1
    return dict(walk())


def measure(folder, name):
    results = {}
    reference = folder / (name + '_original_lossless.mkv')
    graph = ('[0:v]crop=256:128:0:0,format=yuv420p,settb=1/24000,setpts=N*1001[a];'
             '[1:v]crop=256:128:0:0,format=yuv420p,settb=1/24000,setpts=N*1001[b];'
             '[a][b]ssim')
    for label, path in [('previous', BASE / 'build/movies_mods' / (name + '.mods')),
                        ('hq', folder / (name + '_HQ.mods'))]:
        cmd = [str(ENC), '-nostdin', '-v', 'info', '-i', str(path), '-i', str(reference),
               '-filter_complex', graph, '-an', '-f', 'null', '-']
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        (folder / (name + '_ssim_' + label + '.log')).write_text(result.stderr, encoding='utf-8')
        match = re.search(r'All:([0-9.]+)', result.stderr)
        if not match:
            raise ValueError('SSIM result missing')
        results[label] = float(match[1])
    if results['hq'] <= results['previous']:
        raise ValueError(f'{name}: quality did not improve')
    print(name, json.dumps(results), flush=True)
    return results


def build(folder, metrics):
    source_path = BASE / 'build/Tales of Hearts - Anime Movie Edition (PT-BR).nds'
    source = source_path.read_bytes()
    original_hash = hashlib.sha256(source).hexdigest()
    rom = bytearray(source)
    ids = file_ids(source)
    fat = struct.unpack_from('<I', source, 0x48)[0]
    allowed = []
    changes = []
    release = folder / 'release'
    release.mkdir(exist_ok=True)
    for name in NAMES:
        validation = json.loads((folder / (name + '_validation.json')).read_text(encoding='utf-8'))
        if not all(validation['checks'].values()):
            raise ValueError(name + ': failed validation')
        candidate = folder / (name + '_HQ.mods')
        data = candidate.read_bytes()
        if hashlib.sha256(data).hexdigest() != validation['candidate_sha256']:
            raise ValueError(name + ': file changed after validation')
        fid = ids['movie/' + name + '.mods']
        at = fat + fid * 8
        start, end = struct.unpack_from('<II', source, at)
        if len(data) > end - start:
            raise ValueError(name + ': exceeds original ROM file span')
        rom[start:end] = data + b'\0' * (end - start - len(data))
        struct.pack_into('<I', rom, at + 4, start + len(data))
        allowed.extend([(at, at + 8), (start, end)])
        changes.append({'name': name, 'file_id': fid, 'start': start,
                        'old_end': end, 'new_end': start + len(data),
                        'source_file_sha256': hashlib.sha256(source[start:end]).hexdigest(),
                        'new_file_sha256': hashlib.sha256(data).hexdigest()})
        shutil.copy2(candidate, release / (name + '.mods'))
    cursor = 0
    for start, end in sorted(allowed):
        if rom[cursor:start] != source[cursor:start]:
            raise ValueError('Unexpected ROM mutation')
        cursor = end
    if rom[cursor:] != source[cursor:] or len(rom) != len(source):
        raise ValueError('Unexpected ROM size or tail mutation')
    destination = release / 'Tales_of_Hearts_PTBR_HQ_TEST.nds'
    destination.write_bytes(rom)
    check = destination.read_bytes()
    for change in changes:
        span = check[change['start']:change['new_end']]
        if hashlib.sha256(span).hexdigest() != change['new_file_sha256']:
            raise ValueError('Written ROM movie verification failed')
    if hashlib.sha256(source_path.read_bytes()).hexdigest() != original_hash:
        raise ValueError('Source ROM changed during build')
    report = {'base_rom': str(source_path), 'base_sha256': original_hash,
              'output_rom': str(destination), 'output_sha256': hashlib.sha256(check).hexdigest(),
              'rom_size_unchanged': len(check), 'only_four_movie_spans_and_fat_changed': True,
              'base_rom_unchanged': True, 'hardware_tested': False,
              'quality_reference': 'Top 256x128 pixels, all frames; native decoded Japanese originals.',
              'previous_reference': 'build/movies_mods (not necessarily videos in the base ROM).',
              'metrics': metrics, 'changes': changes}
    (folder / 'release_validation.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder', type=Path)
    args = parser.parse_args()
    folder = args.folder.resolve()
    metrics = {name: measure(folder, name) for name in NAMES}
    report = build(folder, metrics)
    print(json.dumps(report, ensure_ascii=True, indent=2), flush=True)


if __name__ == '__main__':
    main()
