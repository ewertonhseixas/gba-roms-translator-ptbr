#!/usr/bin/env python3
"""Compile and verify PT-BR text, UI graphics and synopsis before publishing."""
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from toh_ui_localization import apply

TOOLS_DIR=Path(__file__).resolve().parent
BASE_DIR=TOOLS_DIR.parent
BUILD_DIR=BASE_DIR/'build'

def main():
    base_rom=BUILD_DIR/'movie_quality_2026-11-17/release/Tales_of_Hearts_PTBR_HQ_TEST.nds'
    if not base_rom.is_file():base_rom=BASE_DIR/'rom/Tales of Hearts - Anime Movie Edition (EN).nds'
    canonical=BUILD_DIR/'Tales of Hearts - Anime Movie Edition (PT-BR).nds'
    stamp=datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    stage=BUILD_DIR/('validator_build_'+stamp)
    cmd=[sys.executable,'-X','utf8',str(TOOLS_DIR/'toh_text_builder_v2.py'),'--base',str(base_rom),'--output',str(stage)]
    if canonical.is_file():cmd.extend(['--reuse',str(canonical)])
    result=subprocess.run(cmd,cwd=BASE_DIR)
    if result.returncode:return result.returncode
    built=stage/'Tales_of_Hearts_PTBR_HQ_TEXT_TEST.nds'
    if not built.is_file():raise FileNotFoundError(built)
    apply(built,built,stage/'ui_localization')
    result=subprocess.run([sys.executable,'-X','utf8',str(TOOLS_DIR/'verify_implemented_text.py'),str(stage)],cwd=BASE_DIR)
    if result.returncode:return result.returncode
    summary_path=stage/'summary.json'
    if summary_path.exists():
        import hashlib
        summary=json.loads(summary_path.read_text(encoding='utf8'))
        summary['rom_sha256']=hashlib.sha256(built.read_bytes()).hexdigest()
        summary['output_sha256']=summary['rom_sha256']
        ui=json.loads((stage/'ui_localization/ui_localization_report.json').read_text(encoding='utf8'))
        summary['changed_files']=sorted(set(summary['changed_files']+ui['changed_files']+ui['changed_executables']))
        summary['used_rom_bytes']=int.from_bytes(built.read_bytes()[0x80:0x84],'little')
        summary['ui_localization_report']='ui_localization/ui_localization_report.json'
        summary_path.write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8')
    latest=BUILD_DIR/'validator_build_latest'
    if latest.exists():latest.rename(BUILD_DIR/('validator_build_previous_'+stamp))
    stage.rename(latest)
    built=latest/built.name
    verification_path=latest/'implementation_verification.json'
    verification=json.loads(verification_path.read_text(encoding='utf8'))
    verification['rom']=str(built)
    verification_path.write_text(json.dumps(verification,ensure_ascii=False,indent=2),encoding='utf8')
    temporary=BUILD_DIR/('Tales_of_Hearts_publish_'+stamp+'.nds')
    shutil.copy2(built,temporary)
    temporary.replace(canonical)
    print('ROM PT-BR compilada e verificada:',canonical)
    return 0

if __name__=='__main__':sys.exit(main())
