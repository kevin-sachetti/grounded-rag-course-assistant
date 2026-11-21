@echo off
chcp 65001 >nul
title Grounded RAG Assistant
cd /d "%~dp0"

echo.
echo  Desligando o Grounded RAG Assistant...
docker compose down
echo.
echo  Desligado. Os materiais e as conversas ficam salvos para a próxima vez.
echo.
pause
