@echo off
chcp 65001 >nul
cd /d "%~dp0.."
echo ========================================================
echo   GBA Pixel Studio - Editor de Imagens e Text-in-Tiles
echo   Traducao e ROM Hacking GBA (Summon Night 1, 2 e outros)
echo ========================================================
python -X utf8 "02_TRADUCAO_ROMS_GBA\_ferramentas_gerais\image_editor\image_editor_server.py"
pause
