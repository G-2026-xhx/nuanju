$action = New-ScheduledTaskAction -Execute "python" -Argument "C:\Users\徐华祥\ai-site\daily_push.py"
$trigger = New-ScheduledTaskTrigger -Daily -At "15:30"
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries
Register-ScheduledTask -TaskName "NuanTongDailyPush" -Action $action -Trigger $trigger -Settings $settings -Force
Write-Host "OK"
