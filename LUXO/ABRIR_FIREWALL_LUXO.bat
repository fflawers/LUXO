@echo off
echo Abriendo puerto 8550 para LUXO...
netsh advfirewall firewall add rule name="LUXO-Puerto-8550-IN" dir=in action=allow protocol=TCP localport=8550 profile=any
netsh advfirewall firewall add rule name="LUXO-Puerto-8550-OUT" dir=out action=allow protocol=TCP localport=8550 profile=any
echo.
echo ==========================================
echo  LISTO - Puerto 8550 abierto para LUXO
echo ==========================================
echo.
echo Accede desde tu celular o computadora:
echo   http://192.168.1.78:8550
echo.
pause
