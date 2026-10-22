import sys
sys.path.insert(0, "tools")
from pathlib import Path
from disasm_boot import disassemble_region, print_disasm_block

rom = Path("rom/Summon Night - Swordcraft Story (USA).gba").read_bytes()
print_disasm_block("SRAM Access Functions", disassemble_region(rom, 0x08000F00, 0x70, True))
