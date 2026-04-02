@echo off
echo ============================================
echo   MySQL Root Password Reset Script v3
echo ============================================
echo.

:: Check admin rights
net session >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Run as Administrator! Right-click -^> Run as administrator
    pause
    exit /b 1
)

echo [Step 1] Stopping MySQL service...
net stop MySQL80
timeout /t 4 /nobreak > nul

echo [Step 2] Starting MySQL with skip-grant-tables (no networking restriction)...
start "" /b "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqld" --defaults-file="C:\ProgramData\MySQL\MySQL Server 8.0\my.ini" --skip-grant-tables --shared-memory
echo Waiting 15 seconds for MySQL to fully start...
timeout /t 15 /nobreak > nul

echo [Step 3] Resetting password via shared memory...
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql" -u root --protocol=memory -e "FLUSH PRIVILEGES; ALTER USER 'root'@'localhost' IDENTIFIED BY 'root';" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Password reset via shared memory - OK!
    goto stopsafe
)

echo Trying via TCP...
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql" -u root -e "FLUSH PRIVILEGES; ALTER USER 'root'@'localhost' IDENTIFIED BY 'root';" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Password reset via TCP - OK!
    goto stopsafe
)

echo Trying via named pipe...
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql" -u root --protocol=pipe -e "FLUSH PRIVILEGES; ALTER USER 'root'@'localhost' IDENTIFIED BY 'root';" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Password reset via pipe - OK!
    goto stopsafe
)

echo ERROR: Could not connect to MySQL in safe mode.
echo Increasing wait time and retrying...
timeout /t 10 /nobreak > nul
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql" -u root --protocol=memory -e "FLUSH PRIVILEGES; ALTER USER 'root'@'localhost' IDENTIFIED BY 'root';"
if %ERRORLEVEL% EQU 0 (
    echo Password reset on retry - OK!
) else (
    echo FAILED to reset password. Please use MySQL Installer to reconfigure.
    taskkill /f /im mysqld.exe > nul 2>&1
    net start MySQL80
    pause
    exit /b 1
)

:stopsafe
echo [Step 4] Stopping safe-mode MySQL...
taskkill /f /im mysqld.exe > nul 2>&1
timeout /t 5 /nobreak > nul

echo [Step 5] Starting MySQL service normally...
net start MySQL80
timeout /t 5 /nobreak > nul

echo [Step 6] Testing connection...
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql" -u root -proot -e "SELECT 'SUCCESS - Connected!' AS Status;" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================
    echo   SUCCESS! MySQL password is now: root
    echo ============================================
) else (
    echo.
    echo WARNING: Test connection failed.
)
echo.
pause
