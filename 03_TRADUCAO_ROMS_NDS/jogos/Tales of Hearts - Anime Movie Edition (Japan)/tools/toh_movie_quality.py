"""Lossless subtitle preparation and conservative MODS video experiments.

Copies original compressed audio, forces original keyframe positions, checks
packet sizes, alignment and exact audio packet hashes. Never modifies a ROM.
"""
import argparse
import hashlib
import json
from pathlib import Path
from toh_movie_guard import audit_movie
import struct
import subprocess
import time

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE.parents[1]
ENC = ROOT / '_ferramentas_nds/mobipeg/ffmpeg.exe'
PROBE = ROOT / '_ferramentas_nds/mobipeg/ffprobe.exe'
FF = ROOT / '_ferramentas_nds/ffmpeg.exe'
COLOR = "format=gbrp,geq=g='(r(X,Y)+2*g(X,Y)+b(X,Y))/4':b='(2*g(X,Y)-r(X,Y)-b(X,Y))/4+128':r='(r(X,Y)-b(X,Y))/2+128',mergeplanes=0x000102:yuv444p,format=yuv420p"


def header(path):
    data = path.read_bytes()
    frames, w, h, fps = struct.unpack_from('<4I', data, 8)
    audio, channels, rate = struct.unpack_from('<HHI', data, 24)
    biggest, audio_off, key_off, key_count = struct.unpack_from('<4I', data, 32)
    keys = [struct.unpack_from('<II', data, key_off + i * 8) for i in range(key_count)]
    pos = keys[0][1]
    sizes = []
    for i in range(frames):
        if pos % 4:
            raise ValueError(f'Unaligned frame {i}')
        value = struct.unpack_from('<I', data, pos)[0]
        size = value >> 14
        if not size or pos + size + 4 > len(data):
            raise ValueError(f'Invalid frame {i}')
        sizes.append(size)
        pos += size + 4
    if audio_off and pos != audio_off:
        raise ValueError('Frame/audio-codebook boundary mismatch')
    return dict(frames=frames, width=w, height=h, fps_raw=fps,
                duration=frames / (fps / 16777216), audio_codec=audio,
                channels=channels, sample_rate=rate,
                keyframes=[k[0] for k in keys], max_packet=max(sizes),
                file_size=len(data), data_end=pos, header_biggest=biggest)


def audio_packets(path):
    cmd = [str(PROBE), '-v', 'error', '-select_streams', 'a', '-show_packets',
           '-show_entries', 'packet=size,data_hash', '-show_data_hash', 'sha256',
           '-of', 'json', str(path)]
    return json.loads(subprocess.check_output(cmd))['packets']


def video_sizes(path):
    cmd = [str(PROBE), '-v', 'error', '-select_streams', 'v', '-show_packets',
           '-show_entries', 'packet=size', '-of', 'json', str(path)]
    return [int(p['size']) for p in json.loads(subprocess.check_output(cmd))['packets']]


def pcm_hash(path):
    cmd = [str(ENC), '-nostdin', '-v', 'error', '-i', str(path), '-map', '0:a:0',
           '-c:a', 'pcm_s16le', '-f', 'hash', '-hash', 'sha256', '-']
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    if result.stderr.strip():
        raise ValueError('Audio decoder reported errors: ' + result.stderr[:300])
    return result.stdout.strip()


def exact_video_sizes(path, folder):
    """Force decoder-backed splitting, avoiding FastAudio's heuristic branch.

    Probe-only SX headers/codebook are never shipped. Audio is not decoded
    from this temporary file; its sole purpose is precise video boundaries.
    """
    meta = header(path)
    if meta['audio_codec'] != 2:
        return video_sizes(path)
    template = (BASE / 'extracted/movies/MOV001_JP.mods').read_bytes()
    ao, ko = struct.unpack_from('<II', template, 36)
    codebook = template[ao:ko]
    source = path.read_bytes()
    key_off = struct.unpack_from('<I', source, 40)[0]
    end = meta['data_end']
    fake = bytearray(source[:end] + codebook + source[key_off:])
    struct.pack_into('<H', fake, 24, 1)
    struct.pack_into('<II', fake, 36, end, end + len(codebook))
    probe = folder / (path.stem + '_sx_boundary_probe.mods')
    probe.write_bytes(fake)
    return video_sizes(probe)


def streaming_peaks(path):
    data = path.read_bytes()
    meta = header(path)
    pos = struct.unpack_from('<I', data, struct.unpack_from('<I', data, 40)[0] + 4)[0]
    sizes = []
    for _ in range(meta['frames']):
        size = 4 + (struct.unpack_from('<I', data, pos)[0] >> 14)
        sizes.append(size)
        pos += size
    peaks = {}
    for length in (6, 24, 48):
        current = sum(sizes[:length])
        maximum = current
        for i in range(length, len(sizes)):
            current += sizes[i] - sizes[i - length]
            maximum = max(maximum, current)
        peaks[str(length)] = maximum
    return peaks


def remux_original_audio(original, video, output, exact_sizes=None):
    """Keep raw audio tails/checkpoints/codebooks, not demuxer's wrapped packets.

    The decoder-backed demuxer reports exact video byte consumption. Original
    keyframe positions must match so audio state checkpoints stay at the same
    frames. Padding is added only AFTER the original audio tail.
    """
    source, encoded = original.read_bytes(), video.read_bytes()
    sh, vh = header(original), header(video)
    if sh['frames'] != vh['frames'] or sh['keyframes'] != vh['keyframes']:
        raise ValueError('Audio reassembly requires identical frames/keyframes')
    ss = exact_video_sizes(original, output.parent)
    vs = exact_sizes if exact_sizes is not None else video_sizes(video)
    if len(ss) != sh['frames'] or len(vs) != sh['frames']:
        raise ValueError('Incomplete video packet inventory')
    sp = struct.unpack_from('<I', source, struct.unpack_from('<I', source, 40)[0] + 4)[0]
    vp = struct.unpack_from('<I', encoded, struct.unpack_from('<I', encoded, 40)[0] + 4)[0]
    result = bytearray(source[:sp])
    key_offsets = []
    biggest = 0
    for i in range(sh['frames']):
        sw = struct.unpack_from('<I', source, sp)[0]
        vw = struct.unpack_from('<I', encoded, vp)[0]
        if ss[i] > sw >> 14 or vs[i] > (vw >> 14) + 2:
            raise ValueError('Video extent exceeds packet')
        original_tail = source[sp + 4 + ss[i]:sp + 4 + (sw >> 14)]
        video_payload = encoded[vp + 4:vp + 4 + min(vs[i], vw >> 14)]
        # The 16-bit video reader can consume its final read-ahead word past
        # a no-audio packet. Supply zero guard bytes rather than audio bytes.
        video_payload = video_payload.ljust(vs[i], b'\0')
        payload = video_payload + original_tail
        payload += b'\0' * (-len(payload) % 4)
        if i in sh['keyframes']:
            key_offsets.append((i, len(result)))
        result.extend(struct.pack('<I', (len(payload) << 14) | (sw & 0x3fff)))
        result.extend(payload)
        biggest = max(biggest, len(payload) + 4)
        sp += 4 + (sw >> 14)
        vp += 4 + (vw >> 14)
    original_audio_offset, original_key_offset = struct.unpack_from('<II', source, 36)
    codebook_offset = len(result) if original_audio_offset else 0
    result.extend(source[sp:original_key_offset])
    key_offset = len(result)
    for frame, offset in key_offsets:
        result.extend(struct.pack('<II', frame, offset))
    struct.pack_into('<4I', result, 32, biggest, codebook_offset, key_offset, len(key_offsets))
    output.write_bytes(result)


def run(command, folder, log_name):
    print(log_name, flush=True)
    started = time.time()
    with (folder / (log_name + '.log')).open('w', encoding='utf-8') as log:
        log.write(json.dumps([str(v) for v in command], ensure_ascii=False) + '\n')
        log.flush()
        result = subprocess.run([str(v) for v in command], cwd=folder,
                                stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(f'{log_name} failed; see log')
    print(f'{log_name}: done in {time.time() - started:.1f}s', flush=True)


def encode(name, folder, ratio):
    folder.mkdir(parents=True, exist_ok=True)
    original = BASE / 'extracted/movies' / (name + '_JP.mods')
    previous = BASE / 'build/movies_mods' / (name + '.mods')
    subtitle = BASE / 'extracted/movies' / (name + '.srt')
    meta = header(original)
    audio = audio_packets(original)
    audio_size = sum(int(p['size']) for p in audio)
    video_budget = int((original.stat().st_size - audio_size - 8192) * 8 / meta['duration'] * ratio)
    # Reserve room for the original audio packets plus mux overhead. Verify
    # actual frame sizes after encoding; these settings are not hardware proof.
    vbv = max(16000, (meta['max_packet'] - max(int(p['size']) for p in audio) - 256) * 8)
    decoded = folder / (name + '_original_lossless.mkv')
    subbed = folder / (name + '_subtitled_lossless.mkv')
    if not decoded.exists():
        run([ENC, '-nostdin', '-y', '-v', 'warning', '-i', original,
             '-map', '0:v:0', '-an', '-c:v', 'ffv1', '-level', '3',
             '-pix_fmt', 'bgr0', '-fps_mode', 'passthrough', decoded], folder, name + '_01_decode')
    if not subbed.exists():
        # Use a relative filename so libass is independent of Windows escaping.
        (folder / (name + '.srt')).write_bytes(subtitle.read_bytes())
        style = 'FontName=Arial,FontSize=18,Bold=1,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=1,MarginV=8'
        vf = f"subtitles={name}.srt:force_style='{style}'"
        run([FF, '-nostdin', '-y', '-v', 'warning', '-i', decoded,
             '-vf', vf, '-an', '-c:v', 'ffv1', '-level', '3', '-pix_fmt', 'bgr0',
             '-fps_mode', 'passthrough', subbed], folder, name + '_02_subtitles')
    output = folder / (name + '_HQ.mods')
    video_only = folder / (name + '_video_only.mods')
    force = 'expr:' + '+'.join(f'eq(n,{n})' for n in meta['keyframes'])
    audio_mode = {1: 'codebook', 2: 'fastaudio'}[meta['audio_codec']]
    common = [ENC, '-nostdin', '-y', '-v', 'info', '-i', subbed, '-i', original,
              '-map', '0:v:0', '-vf', COLOR,
              '-c:v', 'libx264', '-preset', 'slow', '-threads', '4',
              '-mobiclip', '2', '-moflex', '0', '-b:v', str(video_budget),
              '-maxrate', str(video_budget * 2), '-bufsize', str(vbv),
              '-g', '100000', '-keyint_min', '1', '-sc_threshold', '0',
              '-force_key_frames', force, '-r', '24000/1001',
              '-frames:v', str(meta['frames']), '-an',
              '-mo_audio', 'none', '-f', 'mods']
    statfile = name + '.pass'
    if not video_only.exists():
        for pass_no in (1, 2):
            run(common + ['-pass', str(pass_no), '-x264-params', 'stats=' + statfile + ':qpmax=50', video_only],
                folder, name + f'_03_pass{pass_no}')
    # No-audio MODS demuxing exposes whole padded payloads. A provisional
    # audio-bearing file makes the demuxer run the actual video decoder and
    # report consumed bytes, separating video padding from audio start.
    provisional = folder / (name + '_boundary_probe.mods')
    remux_original_audio(original, video_only, provisional)
    exact_sizes = exact_video_sizes(provisional, folder)
    remux_original_audio(original, video_only, output, exact_sizes)
    result = header(output)
    native_metadata = audit_movie(output.read_bytes())
    result_audio = audio_packets(output)
    original_pcm, candidate_pcm = pcm_hash(original), pcm_hash(output)
    original_peaks, candidate_peaks = streaming_peaks(original), streaming_peaks(output)
    checks = {
        'dimensions': (meta['width'], meta['height']) == (result['width'], result['height']),
        'nds_quantizer_range': native_metadata['max_quantizer'] <= 52,
        'frame_count': meta['frames'] == result['frames'],
        'audio_configuration': all(meta[k] == result[k] for k in ['audio_codec', 'channels', 'sample_rate']),
        'decoded_audio_identical': original_pcm == candidate_pcm,
        'fps_header_identical': meta['fps_raw'] == result['fps_raw'],
        'keyframes_identical': meta['keyframes'] == result['keyframes'],
        'packet_budget': result['max_packet'] <= meta['max_packet'],
        'original_file_budget': result['file_size'] <= meta['file_size'],
        'streaming_peaks': all(candidate_peaks[k] <= original_peaks[k] for k in original_peaks),
    }
    run([ENC, '-nostdin', '-xerror', '-v', 'error', '-i', output, '-map', '0:v:0',
         '-map', '0:a:0', '-f', 'null', '-'], folder, name + '_04_full_decode')
    report = dict(name=name, ratio=ratio, target_video_bitrate=video_budget, vbv_bits=vbv,
                  source=meta, previous=header(previous), candidate=result, checks=checks,
                  source_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),
                  audio_packet_hashes_identical=audio == result_audio,
                  audio_packet_note='Raw original audio tails copied; end padding can change packet hashes.',
                  original_pcm_hash=original_pcm, candidate_pcm_hash=candidate_pcm,
                  original_streaming_peaks=original_peaks, candidate_streaming_peaks=candidate_peaks,
                  subtitle_sha256=hashlib.sha256(subtitle.read_bytes()).hexdigest(),
                  candidate_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                  hardware_tested=False)
    (folder / (name + '_validation.json')).write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'name': name, 'checks': checks, 'bytes': result['file_size']}), flush=True)
    if not all(checks.values()):
        raise RuntimeError('Candidate failed validation; do not inject')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('names', nargs='+')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--ratio', type=float, default=0.95)
    args = parser.parse_args()
    for name in args.names:
        if name not in ('MOV001', 'MOV002', 'MOV006', 'MOV007'):
            parser.error('Unsupported movie name')
        encode(name, args.output.resolve(), args.ratio)


if __name__ == '__main__':
    main()
