# 一条命令准备今天的环境（Windows PowerShell）
# 用法：在 D:\me\seckill 目录下执行
#   powershell -ExecutionPolicy Bypass -File tools\start.ps1
#
# 它做四件事：
#   ① 唤醒 WSL 并把 MySQL/Redis/RabbitMQ 拉起来（这三个装在 WSL Ubuntu-22.04 里）
#   ② 等 Windows 侧 3 个端口真正可连（这一步是以前最常见的"明明起来了却连不上"）
#   ③ 检查 JDK 17 / Maven
#   ④ 告诉你下一步敲什么

$ErrorActionPreference = "Continue"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root

function Write-Step($msg) { Write-Host "`n== $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "  [OK]  $msg" -ForegroundColor Green }
function Write-Bad($msg)  { Write-Host "  [!!]  $msg" -ForegroundColor Red }

$distro = "Ubuntu-22.04"
$ports  = @(3306, 6379, 5672)

# ---------- 1. 起中间件 ----------
Write-Step "1/4 起中间件（WSL: $distro）"
if (-not (Get-Command wsl -ErrorAction SilentlyContinue)) {
    Write-Bad "找不到 wsl 命令。请先在 PowerShell 里跑 wsl --install"
    exit 1
}
$wslScript = "/mnt/d/me/seckill/tools/wsl-mw.sh"
if (-not (Test-Path "D:\me\seckill\tools\wsl-mw.sh")) {
    $wslScript = "/mnt/" + ($root.Substring(0,1).ToLower()) + ($root.Substring(2) -replace '\\', '/') + "/tools/wsl-mw.sh"
}
$null = & wsl -d $distro -u root -- bash $wslScript start 2>&1
if ($LASTEXITCODE -ne 0) { Write-Bad "拉起服务失败，手动看状态：wsl -d $distro -u root -- bash $wslScript status" }

# ---------- 2. 等端口 ----------
Write-Step "2/4 等端口可连（最多 90 秒）"
$deadline = (Get-Date).AddSeconds(90)
$allOk = $false
while ((Get-Date) -lt $deadline) {
    $okCount = 0
    foreach ($p in $ports) {
        $c = New-Object Net.Sockets.TcpClient
        try { $null = $c.Connect("127.0.0.1", $p); $okCount++ } catch {} finally { $c.Close() }
    }
    if ($okCount -eq $ports.Count) { $allOk = $true; break }
    Start-Sleep -Seconds 3
}
if ($allOk) {
    Write-Ok "3306(MySQL) / 6379(Redis) / 5672(RabbitMQ) 都可连"
} else {
    Write-Bad "端口没全通。多半是 WSL 没起来：wsl --shutdown 然后重跑本脚本"
    Write-Host "  手动看状态：wsl -d $distro -u root -- bash $wslScript status" -ForegroundColor DarkGray
}

# ---------- 3. 检查 JDK / Maven ----------
Write-Step "3/4 检查 JDK 17 / Maven"
$jdkHome = $null
foreach ($cand in @("C:\Users\Administrator\.jdks\ms-17.0.17", $env:JAVA_HOME)) {
    if ($cand -and (Test-Path "$cand\bin\java.exe")) { $jdkHome = $cand; break }
}
if ($jdkHome) { Write-Ok "JDK: $jdkHome"; $env:JAVA_HOME = $jdkHome }
elseif (Get-Command java -ErrorAction SilentlyContinue) { Write-Ok ("JDK: " + ((& java -version 2>&1)[0])) }
else { Write-Bad "没找到 JDK 17：https://adoptium.net/temurin/releases/?version=17" }

$mvn = "C:\Program Files\JetBrains\IntelliJ IDEA 2024.3.7\plugins\maven\lib\maven3\bin\mvn.cmd"
if (Get-Command mvn -ErrorAction SilentlyContinue) { Write-Ok "Maven: 系统 PATH 里的" }
elseif (Test-Path $mvn) { Write-Ok "Maven: IDEA 自带的" }
else { Write-Bad "没找到 Maven：IDEA 的 Settings > Build Tools > Maven 自带即可" }

# ---------- 4. 下一步 ----------
Write-Step "4/4 下一步"
Write-Host "  A. 在 IDEA 里 Run SeckillApplication（推荐，能断点）" -ForegroundColor White
Write-Host "  B. 或者命令行：" -ForegroundColor White
Write-Host "     `$env:JAVA_HOME='$jdkHome'; & `"$mvn`" spring-boot:run" -ForegroundColor DarkGray
Write-Host "`n  起来以后自检（全绿再叫验收）：" -ForegroundColor White
Write-Host "     python tools/verify.py --day 1" -ForegroundColor DarkGray
Write-Host "`n  提醒：中间件在 WSL 里，电脑重启后要先跑本脚本再启动应用。" -ForegroundColor Yellow
