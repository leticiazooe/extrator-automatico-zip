@echo off
setlocal
title Desinstalar - Extrator Automatico

set "STARTUP_FILE=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\ExtratorAutomatico.vbs"

if exist "%STARTUP_FILE%" del /q "%STARTUP_FILE%"

echo.
echo A inicializacao automatica foi removida.
echo O monitor atual sera encerrado quando voce reiniciar ou sair do Windows.
echo.
pause
