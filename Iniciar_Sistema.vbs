Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' Obter o diretório onde o script está localizado
strScriptPath = objFSO.GetParentFolderName(WScript.ScriptFullName)
strProjectDir = strScriptPath

' Se o script estiver na área de trabalho, tentar encontrar o projeto
If Right(strScriptPath, 1) = "\" Then
    strProjectDir = Left(strScriptPath, Len(strScriptPath) - 1)
End If

' Verificar se o diretório existe
If Not objFSO.FolderExists(strProjectDir) Then
    ' Tentar caminho padrão
    strProjectDir = "C:\PROJETOS\Flask\SFP_alfa"
End If

' Verificar se o diretório existe
If Not objFSO.FolderExists(strProjectDir) Then
    MsgBox "[ERRO] Diretório do projeto não encontrado!" & vbCrLf & _
           "[INFO] Caminho tentado: " & strProjectDir & vbCrLf & _
           "[INFO] Por favor, edite o script e ajuste o caminho do projeto", vbCritical, "Erro"
    WScript.Quit
End If

' Verificar se o virtualenv existe
strVenvPath = strProjectDir & "\venv\Scripts\activate.bat"
If Not objFSO.FileExists(strVenvPath) Then
    MsgBox "[ERRO] Virtualenv não encontrado!" & vbCrLf & _
           "[INFO] Execute: python -m venv venv", vbCritical, "Erro"
    WScript.Quit
End If

' Mudar para o diretório do projeto
objShell.CurrentDirectory = strProjectDir

' Criar um arquivo batch temporário que será executado de forma oculta
strBatchFile = objFSO.GetSpecialFolder(2) & "\" & objFSO.GetTempName & ".bat"

Set objFile = objFSO.CreateTextFile(strBatchFile, True)
objFile.WriteLine "@echo off"
objFile.WriteLine "title Sistema de Finanças Pessoais"
objFile.WriteLine "cd /d """ & strProjectDir & """"
objFile.WriteLine "call venv\Scripts\activate.bat"
objFile.WriteLine "python run.py"
objFile.Close

' Executar o batch de forma oculta (0 = oculto)
objShell.Run """" & strBatchFile & """", 0, False

' Aguardar um pouco e depois deletar o arquivo temporário
WScript.Sleep 2000
On Error Resume Next
objFSO.DeleteFile strBatchFile
On Error Goto 0

