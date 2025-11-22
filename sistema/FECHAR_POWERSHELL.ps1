
Get-Process | Where-Object {$_.ProcessName -eq "cmd" -or $_.ProcessName -eq "conhost"} | ForEach-Object {
    try {
        $_.Kill()
        Write-Host "Processo $($_.ProcessName) PID $($_.Id) fechado"
    } catch {
        Write-Host "Erro ao fechar $($_.ProcessName) PID $($_.Id): $_"
    }
}
Get-Process | Where-Object {$_.ProcessName -eq "python"} | ForEach-Object {
    try {
        $_.Kill()
        Write-Host "Processo Python PID $($_.Id) fechado"
    } catch {
        Write-Host "Erro ao fechar Python PID $($_.Id): $_"
    }
}
