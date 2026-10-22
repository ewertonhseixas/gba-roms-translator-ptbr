@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================================================
echo  COMPILANDO ROM PT-BR A PARTIR DOS ARQUIVOS .MD (SUMMON NIGHT GBA)
echo ========================================================================
python -u -X utf8 tools/build_ptbr_rom.py
echo.
pause
