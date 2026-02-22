Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' Aguardar um pouco para garantir que a janela está aberta e mensagens foram exibidas
WScript.Sleep 5000

' Encontrar a janela pelo título
strWindowTitle = "Sistema de Finanças Pessoais"
objShell.AppActivate strWindowTitle

' Minimizar usando Alt+Espaço+N
objShell.SendKeys "% "
WScript.Sleep 100
objShell.SendKeys "n"

