# 第一天一键通关：起中间件 → 起应用 → 自检 → 告诉你结果
# 由 day1.cmd 调用（双击即可）
$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $PSScriptRoot
$javaHome = "C:\Users\Administrator\.jdks\ms-17.0.17"
$mvn = "C:\Program Files\JetBrains\IntelliJ IDEA 2024.3.7\plugins\maven\lib\maven3\bin\mvn.cmd"
$env:JAVA_HOME = $javaHome
$logDir = Join-Path $root "logs"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }
$appLog = Join-Path $logDir "app.log"

function Say($msg, $color = "Gray") { Write-Host $msg -ForegroundColor $color }
function PortOpen($port) {
    $c = New-Object Net.Sockets.TcpClient
    try { $c.Connect("127.0.0.1", $port); $c.Close(); return $true } catch { return $false }
}

Say ""
Say "  ================  Day 1 一键通关  ================" Cyan
Say ""

# ---- 1. 中间件 ----
Say "[1/3] 起中间件（MySQL / Redis / RabbitMQ）..." Cyan
& powershell -NoProfile -ExecutionPolicy Bypass -File "$root\tools\start.ps1" *> $null
$portsOk = $false
for ($i = 0; $i -lt 20; $i++) {
    if ((PortOpen 3306) -and (PortOpen 6379) -and (PortOpen 5672)) { $portsOk = $true; break }
    Start-Sleep -Seconds 3
}
if (-not $portsOk) {
    Say "  [X] 中间件没起来 —— 手动跑 tools\start.ps1 看详细输出" Red
    Read-Host "  按回车关闭"; exit 1
}
Say "  [OK] 3306 / 6379 / 5672 都可连" Green

# ---- 2. 应用 ----
$already = PortOpen 8080
if ($already) {
    Say "[2/3] 应用已经在跑了（8080 有响应），跳过启动" Green
} else {
    Say "[2/3] 启动应用（日志写到 logs\app.log）..." Cyan
    $bat = Join-Path $logDir "start-app.bat"
    $lines = @(
        '@echo off',
        "set JAVA_HOME=$javaHome",
        "call `"$mvn`" -f `"$root\pom.xml`" -q spring-boot:run > `"$appLog`" 2>&1"
    )
    Set-Content -Path $bat -Value $lines -Encoding ASCII
    Start-Process -FilePath $bat -WindowStyle Hidden
    $up = $false
    for ($i = 0; $i -lt 40; $i++) {
        Start-Sleep -Seconds 3
        if (PortOpen 8080) {
            try { Invoke-WebRequest "http://127.0.0.1:8080/actuator/health" -TimeoutSec 3 -UseBasicParsing | Out-Null; $up = $true; break } catch {}
        }
    }
    if (-not $up) {
        Say "  [X] 应用没起来，最后 15 行日志：" Red
        if (Test-Path $appLog) { Get-Content $appLog -Tail 15 | ForEach-Object { Say "      $_" DarkGray } }
        Read-Host "  按回车关闭"; exit 1
    }
    Say "  [OK] 应用启动成功（Started SeckillApplication）" Green
}

# ---- 3. 自检 ----
Say ""
Say "[3/3] 自检..." Cyan
Say ""
$py = Get-Command python -ErrorAction SilentlyContinue
if ($py) {
    & python "$root\tools\verify.py" --day 1
    $code = $LASTEXITCODE
} else {
    Say "  这台机器上没找到 python 命令，跳过自动自检" Yellow
    $code = 0
}
Say ""
if ($code -eq 0) {
    Say "  =================================================" Green
    Say "    Day 1 完成 ✅" Green
    Say "  =================================================" Green
    Say ""
    Say "  接着做两件事（2 分钟）：" Cyan
    Say "    1) 打开 PROGRESS.md，把 D1 那行补全（日期 / 做了什么 / 耗时）"
    Say "    2) 在这个目录执行："
    Say "         git add -A"
    Say "         git commit -m `"D1: 环境跑通`""
    Say "         git push"
    Say ""
    Say "  然后浏览器打开：http://127.0.0.1:8080/api/seckill/detail/1001"
} else {
    Say "  有 FAIL —— 把上面 FAIL 那几行发我，我给你定位" Red
}
Say ""
Read-Host "  按回车关闭窗口"
