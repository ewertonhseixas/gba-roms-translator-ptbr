@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================================================
echo  COMPILANDO ROM PT-BR (SUMMON NIGHT: SWORDCRAFT STORY 2)
echo ========================================================================
python -u -X utf8 tools/build_ptbr_rom.py
echo.
pause
