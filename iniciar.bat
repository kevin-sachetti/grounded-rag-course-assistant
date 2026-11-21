@echo off
chcp 65001 >nul
title Grounded RAG Assistant
cd /d "%~dp0"

echo.
echo  Grounded RAG Assistant
echo  ======================
echo.

rem 1) Docker instalado?
where docker >nul 2>nul
if errorlevel 1 (
  echo  O Docker Desktop não está instalado.
  echo  Baixe e instale em: https://www.docker.com/products/docker-desktop/
  echo  Depois de instalar, abra o Docker Desktop uma vez e rode este arquivo de novo.
  echo.
  pause
  exit /b 1
)

rem 2) Docker aberto? Se não, abre e espera até 3 minutos.
docker info >nul 2>nul
if not errorlevel 1 goto docker_ok
echo  Abrindo o Docker Desktop...
if exist "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" start "" "%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
echo  Aguardando o Docker iniciar (pode levar 1 a 2 minutos)...
for /l %%i in (1,1,60) do (
  ping -n 4 127.0.0.1 >nul
  docker info >nul 2>nul && goto docker_ok
)
echo.
echo  O Docker não respondeu. Abra o Docker Desktop manualmente,
echo  espere ele ficar pronto e rode este arquivo de novo.
echo.
pause
exit /b 1

:docker_ok
echo  Docker pronto.
echo.

rem 3) Sobe o sistema. Com placa NVIDIA, tenta usar a placa; se falhar, sobe só com o processador.
echo  Subindo o sistema. Na primeira vez, o download dos modelos pode levar
echo  de 10 a 30 minutos, conforme a internet. Nas próximas, é rápido.
echo.
where nvidia-smi >nul 2>nul
if errorlevel 1 goto sem_placa
echo  Placa de vídeo NVIDIA encontrada: tentando usar a placa.
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d --build
if not errorlevel 1 goto subiu
echo.
echo  Não foi possível usar a placa. Subindo só com o processador...
:sem_placa
docker compose up -d --build
if errorlevel 1 (
  echo.
  echo  Algo deu errado ao subir o sistema. Veja as mensagens acima.
  echo.
  pause
  exit /b 1
)

:subiu
rem 4) Espera a interface responder e abre o navegador.
echo.
echo  Aguardando o sistema ficar pronto...
for /l %%i in (1,1,200) do (
  curl -s -f -o nul http://localhost:8080/api/health && goto pronto
  ping -n 4 127.0.0.1 >nul
)
echo  O sistema está demorando para responder. Tente abrir http://localhost:8080 em alguns minutos.
echo.
pause
exit /b 0

:pronto
echo.
echo  Pronto! Abrindo http://localhost:8080
echo  Na primeira vez, o primeiro material enviado também baixa os modelos de busca (~4,5 GB).
echo  Para desligar, use o parar.bat.
start "" http://localhost:8080
echo.
pause
