@echo off
chcp 65001 >nul
cd /d "%~dp0..\02_TRADUCAO_ROMS_GBA\jogos\Summon_Night_Swordcraft_Story_3"
echo ========================================================
echo   Iniciando GBA Localization Studio v2.0 (Summon Night 3)
echo ========================================================
python -X utf8 tools\translation_validator_app.py
pause
