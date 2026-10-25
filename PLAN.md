# 14 天计划 · 每天 ≤1 小时

> 目标：把这个仓库从"脚手架"变成"能演示、能压测、能讲"的项目。
> 规则：**每天只做一天的量**。跳过的天不用补，往后顺延即可。

## 打卡与验收规则（我来监督的部分）

1. **每天做完 3 件事**：改代码 → `git commit` → `git push` → 在 `PROGRESS.md` 加一行（见文件模板）。
2. **然后跟我说一句「Day N 完成」**，我会拉你的代码，按下面的验收标准逐条核，给你「通过 / 打回 + 要改的 1~3 条」，再给下一天的任务。
3. **卡住超过 15 分钟就贴报错给我**，不要自己耗半小时。报错 = 学习效率最高的时刻，但要让我帮你判断是"环境坑"还是"知识点没懂"。
4. 卡住时优先贴三样：完整报错、你执行的命令、你期望的结果。
5. 周末不排任务：D1~D14 是**工作日**计数，实际跨度约 3 周。

## D1 · 环境跑通（60min）

- 装：JDK 17、Maven（IDEA 自带的也行）、Docker Desktop。
- `docker compose up -d` 起 MySQL/Redis/RabbitMQ；`mvn spring-boot:run` 起应用。
- **验收**
  - `curl http://localhost:8080/actuator/health` → `"status":"UP"`
  - `docker ps` 三个容器都是 `healthy`
  - 数据库里 `seckill.sku_stock` 有 1 条记录，stock=1000
  - 浏览器能打开 http://localhost:15672

## D2 · DB 版秒杀（最笨但能跑的版本）（60min）

- 补全 `SeckillServiceImpl` 的 `detail / seckill / result`：`deductStock` 扣减成功就插一条订单。
- **验收**
  - `curl -X POST "http://localhost:8080/api/seckill/1001?userId=1"` 返回成功
  - 数据库 `sku_stock.stock=999, sold=1`，`seckill_order` 有 1 条
  - `curl http://localhost:8080/api/seckill/detail/1001` 能看到库存 999

## D3 · 压测「裸奔版」，拿到第一组数字（60min）

- 跑：`python loadtest/bench.py --total 5000 --concurrency 200 --out loadtest/d3-db.json`
- 压完对账：`select stock, sold from sku_stock;` `select count(*) from seckill_order;`
- **验收**：把 qps / p95 / p99 / 成功率 / **超卖了几件** 填进 README 的压测表第一行
- 提示：这一版大概率会超卖或大量失败 —— 这正好是 D4 的动机，记下来。

## D4 · Redis 预热 + Lua 原子扣减（60min）

- 应用启动时把 `seckill:stock:1001` 写进 Redis；补全 `lua/seckill.lua`；Java 里用 `redisTemplate.execute(seckillScript, keys, qty)`。
- **验收**
  - 并发 200 跑 2000 次后，Redis 里库存剩多少、DB 里订单多了多少，两者对得上
  - **不超卖**（`stock >= 0` 且订单数 ≤ 1000）
  - 日志里能看到脚本返回值

## D5 · MQ 异步下单 + 幂等（60min）

- 扣减成功 → `rabbitTemplate.convertAndSend`；`OrderConsumer` 消费落库；重复消息靠 `uk_user_sku` 兜底。
- **验收**
  - 秒杀接口立即返回"排队中"，不再等 DB
  - RabbitMQ 面板能看到消息进队/出队
  - 同一 userId 重复投递 5 次，订单表只有 1 条

## D6 · 一人一单 + 结果轮询（60min）

- Redis `Set` 记录已下单用户（`sadd` 返回 0 即重复）；`result` 接口查结果。
- **验收**：同一 userId 并发 10 次，只有 1 次成功；`result` 接口能查到"成功/排队中/失败"

## D7 · 中期验收 + 限流（60min）

- 加限流（令牌桶，Redis 实现或 Guava RateLimiter），超限返回业务码。
- **验收**
  - 并发 500 时，超出部分被限流而不是把 DB 打挂
  - 输出一张"限流开/关 的 QPS + 成功率"对比
  - 我会在这里做一次**中期验收**：接口能跑通 + 不超卖 + 有第一轮数据

## D8 · 缓存优化（60min）

- 商品详情加缓存 + 空值缓存（防穿透）+ 简单热点保护。
- **验收**：`detail` 接口 P95 下降；日志/统计里能看到缓存命中率

## D9 · 压测第二轮，出对比表（60min）

- 同样参数重跑，填 README 压测表第二行。
- **验收**：README 有完整的"优化前 vs 优化后"对比（QPS / P95 / P99 / 成功率 / 超卖）

## D10 · 超时未支付回补库存（60min）

- 延迟队列（RabbitMQ TTL+DLX 或 Redis ZSet + 定时任务）。
- **验收**：造 3 单不支付，5 分钟后库存自动 +3，订单状态变"已取消"

## D11 · 故障演练（面试最加分的一环）（60min）

- 停 RabbitMQ 看表现；停 Redis 看报错是否可控；记录现象。
- 写 `docs/fault-drill.md`：现象 / 影响范围 / 你的处理 / 改进项。
- **验收**：文档里有 3 个真实演练记录（不是编的）

## D12 · Docker 化 + 一键启动（60min）

- 写 `Dockerfile`（多阶段构建），compose 里加 `app` 服务。
- **验收**：`docker compose up -d` 一条命令全起；`curl` 接口可用

## D13 · CI + 单元测试（60min）

- 写 3 个测试：Lua 扣减不超卖、订单幂等、限流生效；CI 里跑 `mvn verify`。
- **验收**：GitHub Actions 绿；README badge 绿

## D14 · 收尾 + 面试话术（60min）

- README 补架构图说明、压测结论、取舍说明；写 3 段"我被问到能怎么答"。
- **验收（终验）**
  - 仓库 public，CI 绿，`docker compose up -d` 能一键起
  - README 里数字齐全
  - 你能对着 README 讲 5 分钟不卡壳（我会抽查 3 个问题）

## 做完之后，简历里怎么写（示例，按真实数据改）

> **秒杀/抢购系统（个人项目 · 2026）** 技术栈：Spring Boot 3 + MySQL + Redis + RabbitMQ + Docker
> - 设计 Redis + Lua 原子扣减方案替代 DB 行锁，压测 200 并发下 **零超卖**，QPS 从 X 提升至 Y
> - 引入 RabbitMQ 削峰 + 唯一索引幂等，下单接口 P99 从 A ms 降到 B ms
> - 实现令牌桶限流、一人一单、未支付延迟回补库存；Docker Compose 一键部署，GitHub Actions 持续集成
