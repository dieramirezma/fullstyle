@echo off
echo Running FullStyle Chatbot Tests...
python -m pytest

if %ERRORLEVEL% == 0 (
    echo All tests passed!
) else (
    echo Some tests failed.
)
pause
