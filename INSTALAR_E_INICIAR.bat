@echo off
setlocal
title Instalador - Extrator Automatico
cd /d "%~dp0"

set "PYTHON_EXE="

if exist "%LocalAppData%\Programs\Python\Python312\python.exe" (
    set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python312\python.exe"
)

if not defined PYTHON_EXE if exist "C:\Users\Admin\AppData\Local\Programs\Python\Python312\python.exe" (
    set "PYTHON_EXE=C:\Users\Admin\AppData\Local\Programs\Python\Python312\python.exe"
)

if not defined PYTHON_EXE if exist "C:\Users\Leandro\AppData\Local\Programs\Python\Python312\python.exe" (
    set "PYTHON_EXE=C:\Users\Leandro\AppData\Local\Programs\Python\Python312\python.exe"
)

if not defined PYTHON_EXE if exist "%ProgramFiles%\Python312\python.exe" (
    set "PYTHON_EXE=%ProgramFiles%\Python312\python.exe"
)

if not defined PYTHON_EXE (
    for /f "delims=" %%P in ('py -3.12 -c "import sys; print(sys.executable)" 2^>nul') do (
        if not defined PYTHON_EXE set "PYTHON_EXE=%%P"
    )
)

if not defined PYTHON_EXE (
    for /f "delims=" %%P in ('where python.exe 2^>nul') do (
        if not defined PYTHON_EXE set "PYTHON_EXE=%%P"
    )
)

if defined PYTHON_EXE (
    "%PYTHON_EXE%" -c "import sys; assert sys.version_info >= (3, 10)" >nul 2>&1
    if errorlevel 1 set "PYTHON_EXE="
)

if not defined PYTHON_EXE (
    echo.
    echo O Python 3.12 nao foi localizado automaticamente.
    echo Uma janela sera aberta. Selecione o arquivo python.exe.
    echo.
    for /f "usebackq delims=" %%P in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "Add-Type -AssemblyName System.Windows.Forms; $d=New-Object System.Windows.Forms.OpenFileDialog; $d.Title='Selecione o python.exe do Python 3.12'; $d.Filter='Executavel do Python (python.exe)|python.exe'; if($d.ShowDialog() -eq 'OK'){Write-Output $d.FileName}"`) do (
        if not defined PYTHON_EXE set "PYTHON_EXE=%%P"
    )
)

if not defined PYTHON_EXE (
    echo.
    echo ERRO: Nenhum python.exe foi selecionado.
    echo.
    pause
    exit /b 1
)

"%PYTHON_EXE%" -c "import sys; assert sys.version_info >= (3, 10)" >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERRO: O arquivo selecionado nao e um Python compativel.
    echo Selecione o python.exe da pasta Python312.
    echo.
    pause
    exit /b 1
)

if not exist "%~dp0extrator_automatico.py" (
    echo.
    echo ERRO: extrator_automatico.py nao esta na mesma pasta do instalador.
    echo Extraia todo o ZIP antes de executar este arquivo.
    echo.
    pause
    exit /b 1
)

echo Instalando o Extrator Automatico...
"%PYTHON_EXE%" "%~dp0extrator_automatico.py" --instalar

if errorlevel 1 (
    echo.
    echo A instalacao encontrou um erro.
    pause
    exit /b 1
)

echo.
echo Instalacao concluida.
timeout /t 2 /nobreak >nul
exit /b 0
