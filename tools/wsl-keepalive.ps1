# 让 WSL 一直醒着（否则空闲约 40 秒后 WSL 会自动关闭，中间件全"消失"）
# 原理：起一个隐藏的 `wsl ... sleep infinity` 进程，只要它还在，WSL 虚拟机就不会休眠。
# 用法：powershell -ExecutionPolicy Bypass -File tools\wsl-keepalive.ps1

$distro = "Ubuntu-22.04"

# 已经有 keepalive 在跑吗？
$running = Get-CimInstance Win32_Process -Filter "Name='wsl.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like "*sleep*infinity*" -and $_.CommandLine -like "*$distro*" }

if ($running) {
    Write-Host "  [OK]  WSL 保活进程已在运行（pid $($running.ProcessId -join ',')）" -ForegroundColor Green
} else {
    Start-Process -FilePath "wsl.exe" `
        -ArgumentList "-d", $distro, "-u", "root", "--", "sleep", "infinity" `
        -WindowStyle Hidden
    Start-Sleep -Seconds 3
    Write-Host "  [OK]  已启动 WSL 保活进程（隐藏窗口）" -ForegroundColor Green
}
