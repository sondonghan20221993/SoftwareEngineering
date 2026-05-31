@echo off
echo [1/3] Installing PyInstaller...
pip install pyinstaller >nul 2>&1

echo [2/3] Building exe...
pyinstaller ^
    --onefile ^
    --windowed ^
    --name "DroneEval" ^
    --add-data "drone_eval;drone_eval" ^
    --add-data "sample_data;sample_data" ^
    --hidden-import "PyQt5.sip" ^
    --hidden-import "scipy.optimize" ^
    --hidden-import "scipy.sparse.csgraph._validation" ^
    drone_eval\main.py

echo [3/3] Done!
echo.
echo Output: dist\DroneEval.exe
pause
