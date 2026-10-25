# 一键启动秒杀服务：中间件 + 应用
# 由 run.cmd 调用；也可以直接右键「使用 PowerShell 运行」
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$javaHome = "C:\Users\Administrator\.jdks\ms-17.0.17"
$mvn = "C:\Program Files\JetBrains\IntelliJ IDEA 2024.3.7\plugins\maven\lib\maven3\bin\mvn.cmd"
$env:JAVA_HOME = $javaHome

if (-not (Test-Path "$javaHome\bin\java.exe")) {
    Write-Host "[错误] 找不到 JDK 17：$javaHome" -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $mvn)) {
    Write-Host "[错误] 找不到 Maven：$mvn" -ForegroundColor Red
    exit 1
}

Write-Host "[1/2] 检查中间件（MySQL / Redis / RabbitMQ）..." -ForegroundColor Cyan
& powershell -NoProfile -ExecutionPolicy Bypass -File "$root\tools\start.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[错误] 中间件没起来，看上面的输出" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[2/2] 启动应用 http://127.0.0.1:8080" -ForegroundColor Cyan
Write-Host "      看到 Started SeckillApplication 就成功了；Ctrl+C 停止" -ForegroundColor DarkGray
Write-Host ""
& $mvn -f "$root\pom.xml" -q spring-boot:run
