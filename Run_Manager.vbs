Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
pyScript = scriptDir & "\server_manager.py"

If fso.FileExists("C:\Python314\pythonw.exe") Then
    WshShell.Run """C:\Python314\pythonw.exe"" """ & pyScript & """", 0, False
Else
    WshShell.Run "pythonw """ & pyScript & """", 0, False
End If
