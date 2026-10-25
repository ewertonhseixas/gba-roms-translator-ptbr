@echo off
chcp 65001 >nul
title Compilador de ROM PT-BR
cd /d "%~dp0"
echo Compilando a ROM traduzida e gerando o patch...
if exist tools\build_ptbr_rom.py (
    python -X utf8 tools\build_ptbr_rom.py
) else (
    echo [AVISO] O script tools\build_ptbr_rom.py sera gerado na etapa de extracao tecnica da ROM.
)
pause
