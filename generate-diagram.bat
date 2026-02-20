@echo off
REM Generate architecture diagram using Python diagrams library

echo Generating RDS Diagnostics Tool Architecture Diagram...
echo.

REM Set Graphviz path
set "GRAPHVIZ_BIN=C:\Users\thiagarajan.b\OneDrive - IDP Education Ltd\Management\KiroImmersionDay\Graphviz-14.1.2-win64\bin"
set "PATH=%GRAPHVIZ_BIN%;%PATH%"

REM Check if Python is available
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python from: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

REM Check if diagrams library is installed
python -c "import diagrams" >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python diagrams library is not installed
    echo.
    echo Installing diagrams library...
    pip install diagrams
    if %ERRORLEVEL% NEQ 0 (
        echo ERROR: Failed to install diagrams library
        pause
        exit /b 1
    )
)

REM Generate diagram using Python script
echo Generating architecture diagram...
python generate_architecture_diagram.py
if %ERRORLEVEL% EQU 0 (
    echo.
    echo SUCCESS: Architecture diagram generated!
    echo Output: architecture_diagram.png
    echo.
    echo Opening diagram...
    start architecture_diagram.png
) else (
    echo.
    echo ERROR: Failed to generate diagram
    pause
    exit /b 1
)

echo.
pause
