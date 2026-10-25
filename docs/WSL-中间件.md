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

## 坑二：WSL 空闲约 40 秒就自动关闭（"中间件凭空消失"的真凶）

实测：`wsl --shutdown` 后手动起好三个服务，**只要 40 秒没有任何 wsl 命令在跑，WSL 虚拟机就自己关掉**，
3306/6379/5672 立刻全部 `Connection refused`，应用 `/actuator/health` 里 `db/redis/rabbit` 全 DOWN。
看起来就像"根本没装 MySQL 和 Redis"——其实就是 WSL 睡了。

三条兜底（都已装好）：

1. **保活进程**：`tools/wsl-keepalive.ps1` 会起一个隐藏的 `wsl ... sleep infinity`，
   只要它活着，WSL 就不会休眠。`start.ps1` 第一步就会自动调用它。
2. **WSL 启动即拉起服务**：`/etc/wsl.conf` 里配了 `[boot] command=... systemctl start ...`。
3. **等端口再起应用**：`start.ps1` 会一直等到 3306/6379/5672 真正可连才提示下一步。

> 也试过 `.wslconfig` 的 `vmIdleTimeout=-1`，在 WSL 2.6.3 + 镜像网络下**不生效**，所以走保活进程这条路。

规矩记一条：**先 `start.ps1`，再起应用。**

> 面试可讲的排查故事：「本地中间件跑在 WSL 里，WSL 是懒启动+会自己休眠的，
> 应用先起来时 Redis/MySQL 还没就绪，健康检查全 DOWN。后来我加了保活进程 + 启动前探端口，
> 才把这类'时好时坏'的连不上问题彻底按死。」

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
