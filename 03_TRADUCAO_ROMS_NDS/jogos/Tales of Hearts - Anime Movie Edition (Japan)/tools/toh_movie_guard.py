"""Validate the DS MODS packet structure and native quantizer range, frame by frame.

The desktop FFmpeg decoder accepts quantizers that exceed the DS decoder tables.
An old MOV002 used Q56/Q57 from frame 853 and was therefore not DS-compatible.
"""
import hashlib
import struct


def audit_movie(data):
    if data[:6]!=b'MODSN3':raise ValueError('Unsupported MODS revision')
    frames=struct.unpack_from('<I',data,8)[0]
    biggest,audio_offset,key_offset,key_count=struct.unpack_from('<4I',data,32)
    if not frames or not key_count or key_offset+key_count*8>len(data):
        raise ValueError('Invalid MODS index')
    keys=[struct.unpack_from('<II',data,key_offset+i*8) for i in range(key_count)]
    if keys[0][0]!=0:raise ValueError('Missing first keyframe')
    expected_keys=dict(keys);at=keys[0][1];quantizer=0;maximum=0;largest=0
    for frame in range(frames):
        if at%4 or at+8>len(data):raise ValueError(f'Invalid frame offset: {frame}')
        size=struct.unpack_from('<I',data,at)[0]>>14
        if size<2 or at+4+size>len(data):raise ValueError(f'Truncated frame: {frame}')
        payload=data[at+4:at+4+min(size,16)]
        bits=''.join(f'{int.from_bytes(payload[i:i+2],"little"):016b}'
                     for i in range(0,len(payload)-1,2))
        intra=bits[0]=='1'
        if intra:
            quantizer=int(bits[3:9],2)
        else:
            cursor=1;zeros=0
            while cursor<len(bits) and bits[cursor]=='0':zeros+=1;cursor+=1
            if cursor+zeros>=len(bits):raise ValueError(f'Invalid quantizer prefix: {frame}')
            value=int(bits[cursor:cursor+zeros+1],2)
            quantizer+=((1-value) if value&1 else value)//2
        if not 0<=quantizer<=52:
            raise ValueError(f'DS-incompatible quantizer Q{quantizer} at frame {frame}')
        if frame in expected_keys and (expected_keys[frame]!=at or not intra):
            raise ValueError(f'Invalid keyframe entry: {frame}')
        maximum=max(maximum,quantizer);largest=max(largest,size+4);at+=4+size
    if largest>biggest:raise ValueError('Declared frame buffer is too small')
    if at!=(audio_offset or key_offset):raise ValueError('Invalid end of frame stream')
    return dict(frames=frames,max_quantizer=maximum,max_packet=largest,
                keyframes=key_count,sha256=hashlib.sha256(data).hexdigest())
