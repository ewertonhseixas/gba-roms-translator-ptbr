@echo off
chcp 65001 >nul
cd /d "%~dp0..\03_TRADUCAO_ROMS_NDS\jogos\Summon Night (Japan)"
echo ========================================================
echo   Iniciando validator_ui (Summon Night 1 - Traducao NDS)
echo ========================================================
python -X utf8 tools\translation_validator_app.py
pause
