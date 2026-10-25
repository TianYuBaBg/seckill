# 一条命令把 D1 走完（Windows PowerShell）
# 用法：在 D:\me\seckill 目录下执行
#   .\tools\start.ps1
# 它做三件事：① 检查 JDK/Maven/Docker ② 起中间件并等健康 ③ 告诉你下一步敲什么

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root

function Write-Step($msg) { Write-Host "`n== $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "  [OK]   $msg" -ForegroundColor Green }
function Write-Bad($msg)  { Write-Host "  [缺]   $msg" -ForegroundColor Red }

$missing = @()

Write-Step "1/3 检查工具"

# JDK 17
$javaOk = $false
if (Get-Command java -ErrorAction SilentlyContinue) {
    $v = (& java -version 2>&1 | Select-Object -First 1) -join ""
    if ($v -match '"(1\.)?(?<maj>\d+)') {
        $maj = [int]$Matches['maj']
        if ($maj -ge 17) { $javaOk = $true; Write-Ok "JDK $maj" }
        else { Write-Bad "JDK 是 $maj，需要 17+（pom.xml 里定的是 17）"; $missing += "jdk" }
    }
} else { Write-Bad "没装 JDK"; $missing += "jdk" }

# Maven
if (Get-Command mvn -ErrorAction SilentlyContinue) {
    $mv = (& mvn -v 2>&1 | Select-Object -First 1) -join ""
    Write-Ok "Maven $mv"
} else { Write-Bad "没装 Maven"; $missing += "maven" }

# Docker
$dockerOk = $false
if (Get-Command docker -ErrorAction SilentlyContinue) {
    $null = & docker info 2>&1
    if ($LASTEXITCODE -eq 0) { $dockerOk = $true; Write-Ok "Docker 引擎在运行" }
    else { Write-Bad "Docker 装了但引擎没起（打开 Docker Desktop 等它变成 Running）"; $missing += "docker-run" }
} else { Write-Bad "没装 Docker Desktop"; $missing += "docker" }

if ($missing.Count -gt 0) {
    Write-Step "先补这些（装完重新跑本脚本）"
    if ($missing -contains "jdk")    { Write-Host "  JDK 17   : https://adoptium.net/temurin/releases/?version=17" }
    if ($missing -contains "maven")  { Write-Host "  Maven    : https://maven.apache.org/download.cgi （解压后把 bin 加进 PATH）" }
    if ($missing -contains "docker") { Write-Host "  Docker   : https://www.docker.com/products/docker-desktop/ （装时勾 WSL2 backend，装完可能要重启）" }
    if ($missing -contains "docker-run") { Write-Host "  打开开始菜单里的 Docker Desktop，等右下角鲸鱼图标不动了再跑本脚本" }
    Write-Host "`n装完请重开一个 PowerShell 窗口，让新的 PATH 生效。" -ForegroundColor Yellow
    exit 1
}

Write-Step "2/3 起中间件（MySQL / Redis / RabbitMQ）"
& docker compose up -d
if ($LASTEXITCODE -ne 0) { Write-Host "  docker compose 失败，把上面的报错发我" -ForegroundColor Red; exit 1 }

Write-Host "  等 mysql 健康（最多 90 秒）..."
$ready = $false
for ($i = 1; $i -le 45; $i++) {
    $status = (& docker inspect --format "{{.State.Health.Status}}" seckill-mysql 2>$null)
    if ($status -eq "healthy") { $ready = $true; break }
    Start-Sleep -Seconds 2
}
if ($ready) { Write-Ok "三个容器就绪（mysql 健康）" } else { Write-Host "  mysql 还没 healthy，用 docker logs seckill-mysql 看原因" -ForegroundColor Yellow }

Write-Step "3/3 下一步（复制这两行到新窗口）"
Write-Host "  mvn spring-boot:run" -ForegroundColor White
Write-Host "  python tools/verify.py --day 1" -ForegroundColor White
Write-Host "`n看到 verify.py 全 [PASS]，就在 PROGRESS.md 记一行，然后跟我说「Day 1 完成」。" -ForegroundColor Green
