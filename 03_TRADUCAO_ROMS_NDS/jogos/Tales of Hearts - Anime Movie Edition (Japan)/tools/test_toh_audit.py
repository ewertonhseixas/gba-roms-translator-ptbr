"""Regression tests for indexed map extraction and the three reported lines."""
from pathlib import Path
import struct
import unittest

from toh_full_audit import fps4, unpack
from toh_extended_map_extractor import collect_dialogue, decode_lz10


class AuditTests(unittest.TestCase):
    def test_lz10_literals_and_overlapping_reference(self):
        self.assertEqual(decode_lz10(b'\x10\x06\0\0\x10ABC\0\x02')[0], b'ABCABC')
        self.assertEqual(decode_lz10(b'\x10\x03\0\0\0ABCDEF')[0], b'ABC')
        with self.assertRaises(ValueError):
            decode_lz10(b'\x10\x03\0\0\0ABCDEF', extended=True)

    def test_offset_only_table_uses_final_boundary(self):
        header = b'FPS4' + struct.pack('<IIIHHII', 3, 28, 40, 4, 1, 0, 0)
        blob = header + struct.pack('<III', 40, 43, 46) + b'ABCDEF'
        rows = list(fps4(blob, blob))
        self.assertEqual([r[4] for r in rows], [b'ABC', b'DEF'])

    def test_paired_table_and_bounds(self):
        header = b'FPS4' + struct.pack('<IIIHHII', 2, 28, 0, 8, 3, 0, 0)
        index = header + struct.pack('<4I', 0, 3, 3, 3)
        self.assertEqual([r[4] for r in fps4(index, b'ABCDEF')], [b'ABC', b'DEF'])
        with self.assertRaises(ValueError):
            list(fps4(index, b'ABC'))

    def test_real_map_keeps_story_script_separate(self):
        folder = Path(__file__).resolve().parents[1] / 'extracted/m_unpacked'
        index = (folder / 'FSHT00.B').read_bytes()
        payload = (folder / 'FSHT00.MAPBIN').read_bytes()
        scripts = {name: (offset, unpack(data)[0])
                   for name, offset, _, _, data in fps4(index, payload)
                   if name.endswith('.SCP')}
        self.assertEqual(scripts['FSHT00P.SCP'][0], 0x8280)
        self.assertNotIn(b'Thorn Forest Princess', scripts['FSHT00.SCP'][1])
        data = scripts['FSHT00P.SCP'][1]
        rows = {r['id']: r for r in collect_dialogue(data, len(data))}
        expected = {
            'S000101': ('0x1B174', 'Thorn Forest Princess\nasleep a thousand years.'),
            'S000505': ('0x1B449', '......Find it!\n......Seize it!\n......For the sake of it!!'),
            'S010105': ('0x1B5C1', 'Owww... Oh, right. Gramps and I\nwere sword training and he\nbeat me again.'),
        }
        for key, (offset, text) in expected.items():
            self.assertEqual(rows[key]['offset'], offset)
            self.assertEqual(rows[key]['text'], text)


if __name__ == '__main__':
    unittest.main()
