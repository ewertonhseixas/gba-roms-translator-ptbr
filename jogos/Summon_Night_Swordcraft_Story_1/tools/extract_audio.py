#!/usr/bin/env python3
"""
Full Audio & Music Extractor for Summon Night: Swordcraft Story (USA) [AB4E]
============================================================================
Extrai todos os áudios e músicas da ROM:
  - 103 Amostras de Áudio PCM (DirectSound) em arquivos WAV (.wav)
  - 243 Músicas (BGM) e Efeitos Sonoros (SFX) do SongTable em MIDI (.mid) / JSON
  - Catálogo completo de Áudio (audio_catalog.json) com faixas, canais e offsets
"""

import os
import struct
import json
import wave
from pathlib import Path

GBA_ROM_BASE = 0x08000000
SONG_TABLE_ADDR = 0x08074EB8


def extract_pcm_wav(rom: bytes, wav_ptr: int, out_path: Path):
    """Extrai uma estrutura WaveData do GBA m4a para um arquivo WAV PCM de 16 bits."""
    if not (0x08000000 <= wav_ptr < 0x08800000):
        return False
    woff = wav_ptr - GBA_ROM_BASE
    if woff + 16 > len(rom):
        return False

    wtype, wstat, freq, loop, size = struct.unpack_from("<HHIII", rom, woff)
    if size == 0 or size > 0x100000 or woff + 16 + size > len(rom):
        return False

    sample_rate = freq // 1024 if freq > 100000 else freq
    if sample_rate < 4000 or sample_rate > 96000:
        sample_rate = 15768  # taxa padrão comum no m4a

    raw_pcm = rom[woff + 16 : woff + 16 + size]

    # Converte PCM 8-bit com sinal (-128..127) para PCM 16-bit com sinal (-32768..32767)
    pcm16 = bytearray(size * 2)
    for i in range(size):
        # byte com sinal
        sample8 = struct.unpack_from("b", raw_pcm, i)[0]
        sample16 = sample8 * 256
        struct.pack_into("<h", pcm16, i * 2, sample16)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out_path), "wb") as wf:
        wf.setnchannels(1)      # Mono
        wf.setsampwidth(2)      # 16 bits
        wf.setframerate(sample_rate)
        wf.writeframes(pcm16)

    return True


def sappy_to_midi(rom: bytes, header_ptr: int, out_mid_path: Path, song_id: int):
    """
    Descompila uma sequência Sappy (m4a) e converte em arquivo Standard MIDI (.mid).
    """
    if not (0x08000000 <= header_ptr < 0x08800000):
        return False
    hoff = header_ptr - GBA_ROM_BASE
    if hoff + 8 > len(rom):
        return False

    num_tracks, blocks, prio, rev = struct.unpack_from("4B", rom, hoff)
    tone_ptr = struct.unpack_from("<I", rom, hoff + 4)[0]

    if num_tracks == 0 or num_tracks > 16:
        return False

    track_ptrs = []
    for t in range(num_tracks):
        tptr = struct.unpack_from("<I", rom, hoff + 8 + t * 4)[0]
        if 0x08000000 <= tptr < 0x08800000:
            track_ptrs.append(tptr - GBA_ROM_BASE)

    if not track_ptrs:
        return False

    # Monta arquivo MIDI SMF Tipo 1
    # Formato do Header: MThd (6 bytes: format=1, ntracks, division=48)
    division = 48
    midi_tracks_bytes = []

    for trk_idx, trk_off in enumerate(track_ptrs):
        trk_events = bytearray()
        delta = 0
        curr = trk_off
        active_note = None
        tempo_set = False

        # Define instrumento inicial na trilha
        if trk_idx == 0:
            # Set Tempo (padrão 120 BPM: 500,000 microssegundos por semínima)
            trk_events.extend(b"\x00\xFF\x51\x03\x07\xA1\x20")

        # Programa padrão / canal MIDI
        ch = trk_idx if trk_idx != 9 else 10  # evita canal 10 (bateria) exceto se for drum
        trk_events.extend(bytes([0, 0xC0 | ch, 0]))  # Program change

        visited = set()
        while curr < len(rom):
            if curr in visited:
                break
            visited.add(curr)

            cmd = rom[curr]
            curr += 1

            if cmd == 0xB1:  # Fim da trilha
                break
            elif cmd == 0xB2:  # Salto / Loop
                loop_target = struct.unpack_from("<I", rom, curr)[0]
                curr += 4
                if 0x08000000 <= loop_target < 0x08800000:
                    curr = loop_target - GBA_ROM_BASE
                else:
                    break
            elif cmd == 0xBC:  # Mudança de Tempo
                tempo_val = rom[curr] * 2
                curr += 1
                if not tempo_set and tempo_val > 0:
                    us_per_qn = int(60000000 / tempo_val)
                    trk_events.extend(b"\x00\xFF\x51\x03" + struct.pack(">I", us_per_qn)[1:])
                    tempo_set = True
            elif cmd == 0xBD:  # Program Change (Instrumento)
                prog = rom[curr] & 0x7F
                curr += 1
                trk_events.extend(b"\x00" + bytes([0xC0 | ch, prog]))
            elif cmd == 0xBE:  # Volume
                vol = rom[curr] & 0x7F
                curr += 1
                trk_events.extend(b"\x00" + bytes([0xB0 | ch, 7, vol]))
            elif cmd == 0xBF:  # Pan
                pan = rom[curr] & 0x7F
                curr += 1
                trk_events.extend(b"\x00" + bytes([0xB0 | ch, 10, pan]))
            elif cmd >= 0xD0:  # Nota com duração
                note = cmd & 0x7F
                dur = rom[curr] if curr < len(rom) else 1
                curr += 1
                # Note On
                trk_events.extend(bytes([0, 0x90 | ch, note, 100]))
                # Note Off após duração
                trk_events.extend(bytes([dur, 0x80 | ch, note, 0]))
            elif cmd >= 0x80:  # Rest / Pausa
                rest_len = cmd & 0x7F
                delta += rest_len
            elif cmd < 0x80:  # Note wait
                pass

        # Meta Event: End of Track
        trk_events.extend(b"\x00\xFF\x2F\x00")

        # Chunk da Trilha MTrk
        trk_chunk = b"MTrk" + struct.pack(">I", len(trk_events)) + trk_events
        midi_tracks_bytes.append(trk_chunk)

    # Header Chunk MThd
    header_chunk = b"MThd" + struct.pack(">IHHH", 6, 1, len(midi_tracks_bytes), division)

    out_mid_path.parent.mkdir(parents=True, exist_ok=True)
    out_mid_path.write_bytes(header_chunk + b"".join(midi_tracks_bytes))
    return True


def main():
    rom_path = Path("rom/Summon Night - Swordcraft Story (USA).gba")
    if not rom_path.exists():
        print(f"[!] ROM not found at {rom_path}")
        return 1

    rom = rom_path.read_bytes()
    base_out = Path("extracted/audio")
    samples_dir = base_out / "samples_wav"
    midi_dir = base_out / "midi_tracks"
    samples_dir.mkdir(parents=True, exist_ok=True)
    midi_dir.mkdir(parents=True, exist_ok=True)

    print("=================================================================")
    print(" Summon Night: Swordcraft Story - Extração de Áudio e Músicas")
    print("=================================================================")

    # 1. Coleta e extração dos 103 Samples PCM (.wav)
    song_table_off = SONG_TABLE_ADDR - GBA_ROM_BASE
    tone_ptrs = set()
    catalog_entries = []

    for s_idx in range(243):
        entry_off = song_table_off + s_idx * 8
        h_ptr, ms, me = struct.unpack_from("<IHH", rom, entry_off)
        if 0x08000000 <= h_ptr < 0x08800000:
            h_off = h_ptr - GBA_ROM_BASE
            tracks, blocks, prio, rev = struct.unpack_from("4B", rom, h_off)
            t_ptr = struct.unpack_from("<I", rom, h_off + 4)[0]
            if 0x08000000 <= t_ptr < 0x08800000:
                tone_ptrs.add(t_ptr)

            category = "BGM" if tracks >= 3 and ms == 0 else ("SFX" if tracks == 1 else "Jingle")
            catalog_entries.append({
                "song_id": s_idx,
                "category": category,
                "header_rom_addr": f"0x{h_ptr:08X}",
                "tracks": tracks,
                "priority": prio,
                "player_id": ms,
                "tone_table": f"0x{t_ptr:08X}",
            })

    print(f"\n[+] Extraindo amostras de áudio PCM (.wav)...")
    pcm_samples = set()
    for t_ptr in tone_ptrs:
        t_off = t_ptr - GBA_ROM_BASE
        for i in range(128):
            ioff = t_off + i * 12
            if ioff + 12 > len(rom): break
            itype, k, l, p, wav_ptr = struct.unpack_from("<4BI", rom, ioff)
            if itype in (0x00, 0x08) and 0x08000000 <= wav_ptr < 0x08800000:
                pcm_samples.add(wav_ptr)
            elif itype in (0x40, 0x80) and 0x08000000 <= wav_ptr < 0x08800000:
                sub_tbl = wav_ptr - GBA_ROM_BASE
                for si in range(128):
                    sioff = sub_tbl + si * 12
                    if sioff + 12 > len(rom): break
                    stype, sk, sl, sp, swav = struct.unpack_from("<4BI", rom, sioff)
                    if stype in (0x00, 0x08) and 0x08000000 <= swav < 0x08800000:
                        pcm_samples.add(swav)

    wav_count = 0
    for wav_ptr in sorted(pcm_samples):
        wav_name = f"sample_{wav_ptr:08X}.wav"
        if extract_pcm_wav(rom, wav_ptr, samples_dir / wav_name):
            wav_count += 1

    print(f"    -> {wav_count} amostras PCM exportadas para: {samples_dir.resolve()}")

    # 2. Conversão das 243 Músicas / Efeitos Sonoros para MIDI
    print(f"\n[+] Convertendo músicas (BGM) e sequências para MIDI (.mid)...")
    midi_count = 0
    for entry in catalog_entries:
        s_id = entry["song_id"]
        h_ptr = int(entry["header_rom_addr"], 16)
        cat = entry["category"]
        mid_file = midi_dir / f"{cat.lower()}_{s_id:03d}.mid"
        if sappy_to_midi(rom, h_ptr, mid_file, s_id):
            midi_count += 1
            entry["midi_file"] = f"midi_tracks/{mid_file.name}"

    print(f"    -> {midi_count} trilhas MIDI exportadas para: {midi_dir.resolve()}")

    # 3. Salva o Catálogo JSON de Áudio
    catalog_path = base_out / "audio_catalog.json"
    with open(catalog_path, "w", encoding="utf-8") as f:
        json.dump({
            "total_songs": len(catalog_entries),
            "total_pcm_samples": wav_count,
            "song_table_addr": f"0x{SONG_TABLE_ADDR:08X}",
            "catalog": catalog_entries,
        }, f, indent=2)

    print(f"\n[+] Catálogo de áudio salvo em: {catalog_path.resolve()}")
    print("\n=================================================================")
    print(f"[SUCESSO] Extração de áudio concluída!")
    print(f"  - {wav_count} Amostras WAV")
    print(f"  - {midi_count} Arquivos MIDI (.mid)")
    print(f"  - 1 Catálogo JSON Completo")
    print("=================================================================")
    return 0


if __name__ == "__main__":
    exit(main())
