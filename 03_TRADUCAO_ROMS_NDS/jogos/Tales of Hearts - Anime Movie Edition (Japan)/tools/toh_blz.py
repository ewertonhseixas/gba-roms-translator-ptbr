"""Small dependency-free backwards-LZ codec for Nitro executables.

Used only when ndspy is unavailable; all builds verify the decompression roundtrip.
"""
from collections import defaultdict, deque


def decompress(data):
    data = bytes(data)
    for appended in range(0, 33, 4):
        buf = data[:-appended] if appended else data
        if len(buf) < 8:
            continue
        length = int.from_bytes(buf[-8:-5], 'little')
        head = buf[-5]
        extra = int.from_bytes(buf[-4:], 'little')
        if not (8 <= head <= 32 and head <= length <= len(buf) and 0 < extra < 0x1000000):
            continue
        if any(v != 255 for v in buf[len(buf)-head:len(buf)-8]):
            continue
        stop, read, write = len(buf)-length, len(buf)-head, len(buf)+extra
        out = bytearray(buf) + bytearray(extra)
        try:
            while read > stop and write > stop:
                read -= 1
                flags = buf[read]
                for bit in range(7, -1, -1):
                    if read <= stop or write <= stop:
                        break
                    if flags & (1 << bit):
                        read -= 2
                        count = (buf[read+1] >> 4) + 3
                        distance = ((buf[read+1] & 15) << 8 | buf[read]) + 3
                        for _ in range(count):
                            write -= 1
                            out[write] = out[write+distance]
                    else:
                        read -= 1
                        write -= 1
                        out[write] = buf[read]
            if write != stop:
                continue
            return bytes(out) + (data[-appended:] if appended else b'')
        except (IndexError, ValueError):
            continue
    return data


def compress(data, isArm9=False):
    data = bytes(data)
    reverse = data[::-1]
    maximum = len(data) - (0x4000 if isArm9 else 0)
    positions = defaultdict(lambda: deque(maxlen=96))
    stream, i, best = bytearray(), 0, None
    while i < maximum:
        flag_at = len(stream)
        stream.append(0)
        for bit in range(7, -1, -1):
            if i >= maximum:
                break
            length, distance = 0, 0
            key = reverse[i:i+3]
            if len(key) == 3:
                for previous in reversed(positions[key]):
                    dist = i-previous
                    if dist > 4098:
                        break
                    if dist < 3:
                        continue
                    count = 3
                    while count < 18 and i+count < maximum and reverse[previous+count] == reverse[i+count]:
                        count += 1
                    if count > length:
                        length, distance = count, dist
                        if length == 18:
                            break
            take = length if length >= 3 else 1
            if length >= 3:
                stream[flag_at] |= 1 << bit
                distance -= 3
                stream.extend([((length-3) << 4) | (distance >> 8), distance & 255])
            else:
                stream.append(reverse[i])
            for at in range(i, i+take):
                positions[reverse[at:at+3]].append(at)
            i += take
        prefix = len(data)-i
        padding = -(prefix+len(stream)+8) % 4
        size = prefix+len(stream)+padding+8
        if size < len(data) and (best is None or size < best[0]):
            best = size, prefix, len(stream), padding
    if best is None:
        return data
    size, prefix, used, padding = best
    header = padding+8
    packed = (data[:prefix] + bytes(stream[:used][::-1]) + b'\xff'*padding
              + (used+header).to_bytes(3,'little') + bytes([header])
              + (len(data)-size).to_bytes(4,'little'))
    if decompress(packed) != data:
        raise ValueError('BLZ compression roundtrip failed')
    return packed
