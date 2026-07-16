Set objShell = CreateObject("WScript.Shell")

objShell.CurrentDirectory = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\") - 1)

objShell.Run "venv\Scripts\uvicorn backend.app.main:app --host 0.0.0.0 --port 5000", 0, False

WScript.Sleep 2000

objShell.Run "http://localhost:5000", 1, False 

