@echo off
chcp 65001 >nul
cd /d "%~dp0..\02_TRADUCAO_ROMS_GBA\jogos\Summon_Night_Swordcraft_Story_1"
echo ========================================================
echo   Iniciando validator_ui (Summon Night 1 - Traducao GBA)
echo ========================================================
python -X utf8 tools\translation_validator_app.py
pause
