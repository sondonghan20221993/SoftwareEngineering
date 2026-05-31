@echo off
echo [1/3] PyInstaller 설치 확인 중...
pip install pyinstaller >nul 2>&1

echo [2/3] exe 빌드 중... (시간이 걸릴 수 있습니다)
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

echo [3/3] 완료!
echo.
echo 실행 파일 위치: dist\DroneEval.exe
pause
