Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

strScriptDir = objFSO.GetParentFolderName(WScript.ScriptFullName)
strProjectDir = objFSO.GetParentFolderName(strScriptDir)
strBatchFile = objFSO.BuildPath(strScriptDir, "Iniciar_Sistema.bat")

If Not objFSO.FileExists(strBatchFile) Then
    MsgBox "[ERRO] Arquivo de inicializacao nao encontrado!" & vbCrLf & _
           "[INFO] Caminho esperado: " & strBatchFile, vbCritical, "Erro"
    WScript.Quit 1
End If

If Not objFSO.FolderExists(strProjectDir) Then
    MsgBox "[ERRO] Diretorio do projeto nao encontrado!" & vbCrLf & _
           "[INFO] Caminho esperado: " & strProjectDir, vbCritical, "Erro"
    WScript.Quit 1
End If

objShell.CurrentDirectory = strProjectDir
objShell.Run Chr(34) & strBatchFile & Chr(34), 0, False