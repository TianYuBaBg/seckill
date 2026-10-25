# 中间件环境（你机器上的真实情况）

> 结论先说：**你不用装 Docker，也不用再找 MySQL 安装包了。** 三件中间件已经装好并跑在
> WSL Ubuntu 22.04 里，Windows 上的 Java 应用通过 `127.0.0.1` 直接连。

## 当前装了什么

| 组件 | 版本 | 位置 | 端口 |
|---|---|---|---|
| MySQL | 8.0.46 | WSL `Ubuntu-22.04` | 3306 |
| Redis | 6.0.16 | 同上 | 6379 |
| RabbitMQ | 3.9.27 | 同上 | 5672（管理台 15672） |
| JDK | 17.0.17 | `C:\Users\Administrator\.jdks\ms-17.0.17` | — |
| Maven | 3.9（IDEA 自带） | `C:\Program Files\JetBrains\IntelliJ IDEA 2024.3.7\plugins\maven\lib\maven3` | — |

数据库账号 `root / root`，库名 `seckill`，表已按 `sql/init.sql` 建好（`sku_stock` 库存 1000，`sku_id=1001`）。
RabbitMQ 管理台：<http://127.0.0.1:15672>（guest / guest）。

## 一天开关一次

**最省事的做法：直接跑这个，它会把中间件拉起、等端口通、顺便检查 JDK/Maven。**

```powershell
powershell -ExecutionPolicy Bypass -File tools\start.ps1
```

手动版：

```powershell
# 看状态
wsl -d Ubuntu-22.04 -u root -- bash /mnt/d/me/seckill/tools/wsl-mw.sh status
# 启动（每天开机后跑一次）
wsl -d Ubuntu-22.04 -u root -- bash /mnt/d/me/seckill/tools/wsl-mw.sh start
# 重置库存（每次压测后都要跑，回到 1000）
wsl -d Ubuntu-22.04 -u root -- bash /mnt/d/me/seckill/tools/wsl-mw.sh reset-stock
```

## 坑二：WSL 自己会停，一停就"中间件全挂了"

WSL 在一段时间没人用、或者你重启电脑后会**自己关闭**（`wsl -l -v` 显示 `Stopped`）。
这时 Windows 上的应用连 3306/6379/5672 全是 `Connection refused`，`/actuator/health` 里
`db/redis/rabbit` 全 DOWN —— 看起来像"没装中间件"，其实只是 WSL 睡了。

两个已经做好的兜底：

1. `/etc/wsl.conf` 里加了 `[boot] command=...`，**WSL 一启动就自动把三个服务拉起来**；
2. `tools/start.ps1` 会先唤起 WSL、再等端口真正可连，最后才提示你启动应用。

规矩记一条：**先 `start.ps1`，再起应用。**

> 这也是一条面试可讲的排查故事：「本地中间件在 WSL 里，WSL 是懒启动的，
> 应用先起来时 Redis/MySQL 还没就绪；后来我把启动顺序改成先探端口再起应用，
> 并在 WSL 的 boot 里加了自启脚本。」

## 一个必须记住的坑：localhost ≠ 127.0.0.1

一开始应用起来后 `/actuator/health` 里 `db`、`redis`、`rabbit` 全是 DOWN，但端口用工具测是通的。原因：

- Windows 上 `localhost` 会**优先解析成 IPv6 的 `::1`**；
- WSL 里的 MySQL/Redis 只监听 IPv4；
- 于是 Java 连 `::1:3306` → 直接 Connection refused。

修法：`application.yml` 里所有地址写死 `127.0.0.1`（已改，并支持 `DB_HOST` / `REDIS_HOST` / `MQ_HOST` 环境变量覆盖）。

> 这条**面试能直接讲**：「线上排查过一个连接超时，最后发现是 `localhost` 优先走 IPv6、而中间件只监听 IPv4，把连接串改成 127.0.0.1 就好了」—— 真事，比背八股强。

## 想换成 Docker 怎么办（可选，不是必须）

如果你以后装了 Docker Desktop，`docker compose up -d` 仍然可用（`docker-compose.yml` 一直留着）。
`tools/verify.py` 会自动判断：有 Docker 就走 `docker exec`，没有就走 `wsl`。

## 和 `docs/D1-环境.md` 的关系

那份文档写的是「用 Docker 起中间件」的路线，**你现在这条路线不需要它**，留着当备选方案看。
