ECHO OFF

::SET /P python_path= Sökväg till python.exe:
::SET /P install_dir= Sökväg till installationsmapp:

SET python_path=C:\Python36\python.exe
SET install_dir=C:\mw\test_install_pre_system_svea

ECHO Path to python.exe is: %python_path%
ECHO Path to install dir:  %install_dir%


::############################################################################
cd %install_dir%

::############################################################################
:: Create venv
if exist venv (
     ECHO - Pythonmiljo finns redan
) else (
    ECHO - Skapar pythonmiljo...
    %python_path% -m venv venv
)
CALL venv\Scripts\activate
python -m pip install --upgrade pip


::############################################################################
for %%a in (
  SHARKtools 
  pre_system_svea
  sharkpylib
  ctdpy
  svepa
  ctd_processing
) do (
if exist %%a (
    cd %%a
    git pull
    ECHO - %%a är uppdaterad...
    cd %install_dir%
) else (
    git clone "https://github.com/sharksmhi/%%a.git"	
    ECHO - %%a har klonats...
)
:: Installera requiremnts.txt 
pip install -r "%%a/requirements.txt"
)


::############################################################################
cd SHARKtools 
cd plugins
::############################################################################
if exist SHARKtools_pre_system_Svea (
    cd SHARKtools_pre_system_Svea
    git pull
    ECHO - Plugin SHARKtools_pre_system_Svea är uppdaterad...
    cd %install_dir%
) else (
    git clone https://github.com/sharksmhi/SHARKtools_pre_system_Svea.git
    ECHO - Plugin SHARKtools_pre_system_Svea har klonats...
)



::############################################################################
:: Skapa körpar fil
cd %install_dir%
if not exist run.bat (
    echo CALL venv\Scripts\activate>> run.bat
    echo cd SHARKtools>> run.bat
    for %%a in (
      pre_system_svea
      sharkpylib
      ctdpy
      svepa
      ctd_processing
    ) do echo set PYTHONPATH=%%PYTHONPATH%%;%install_dir%\%%a>> run.bat
    echo main.py>> run.bat
)

ECHO 
ECHO 
ECHO 
echo %PYTHONPATH%
echo
echo
ECHO Instllationen är klar!
pause