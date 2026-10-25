@echo off
chcp 65001 >nul
title Validador e Editor Visual de Traducao GBA
cd /d "%~dp0"
echo Iniciando o Validador e Editor de Traducao...
python -X utf8 tools\translation_validator_app.py
pause
