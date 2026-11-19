@echo off
chcp 65001 >nul
cd /d "%~dp0..\03_TRADUCAO_ROMS_NDS\jogos\Tales of Hearts - Anime Movie Edition (Japan)"
echo ========================================================
echo   Iniciando validator_ui (Tales of Hearts - Traducao NDS)
echo ========================================================
python -X utf8 tools\translation_validator_app.py
pause
