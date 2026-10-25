# Seckill · 高并发秒杀/抢购服务

[![ci](https://github.com/TianYuBaBg/seckill/actions/workflows/ci.yml/badge.svg)](https://github.com/TianYuBaBg/seckill/actions/workflows/ci.yml)

一个用 Java 17 + Spring Boot 3 写的秒杀系统，目标不是"功能多"，而是**把高并发这一条链路做透**：
库存不超卖、下单不重复、削峰不丢消息、压得住流量、扛得住故障、能一键起来。

技术栈：Spring Boot 3.2 · MySQL 8 · Redis 7 · RabbitMQ 3.13 · MyBatis-Plus · Docker · GitHub Actions

## 架构

```
                 ┌────────────────────────────────────────────────┐
   JMeter/bench  │  POST /api/seckill/{skuId}?userId=N            │
   ────────────► │  ① 限流（令牌桶，Redis）                       │
                 │  ② 一人一单校验（Redis Set / DB 唯一索引）      │
                 │  ③ Redis + Lua 原子预扣库存                    │
                 │  ④ 扣减成功 → 发 MQ，立即返回"排队中"           │
                 └───────────────┬────────────────────────────────┘
                                 │  seckill.order.create
                                 ▼
                 ┌────────────────────────────────────────────────┐
                 │  ⑤ OrderConsumer 消费 → 落库（幂等）           │
                 │  ⑥ 未支付超时 → 延迟队列 → 回补库存            │
                 └────────────────────────────────────────────────┘
```

## 快速开始

```bash
# 1. 起中间件（MySQL + Redis + RabbitMQ）
docker compose up -d

# 2. 起应用（本机需 JDK 17 + Maven）
mvn spring-boot:run

# 3. 冒烟
curl http://localhost:8080/api/seckill/detail/1001
curl -X POST "http://localhost:8080/api/seckill/1001?userId=1"

# 4. 压测（零依赖，用 Python 标准库）
python loadtest/bench.py --total 5000 --concurrency 200
```

- RabbitMQ 管理台：http://localhost:15672 （guest/guest）
- 健康检查：http://localhost:8080/actuator/health

## 压测报告

> D3 跑"裸奔版"拿基线，D9 跑"优化版"对比。数字按实际填，别编。

| 版本 | 并发 | 总量 | QPS | P50 | P95 | P99 | 成功率 | 超卖 |
|---|---|---|---|---|---|---|---|---|
| D3 裸奔（DB 直扣） | 200 | 5000 | | | | | | |
| D9 优化（Redis+Lua+MQ） | 200 | 5000 | | | | | | |

## 目录结构

```
src/main/java/com/wangtianyu/seckill
├── controller/   接口层（已搭好）
├── service/      业务层（核心逻辑由你在 D2~D8 补全）
├── consumer/     MQ 消费者（D5 补全）
├── mapper/       MyBatis-Plus（D2 直接用）
├── entity/       实体
├── config/       Redis / RabbitMQ 配置（已搭好）
└── common/       统一返回 + 异常处理
sql/init.sql      建表 + 初始库存 1000（sku_id=1001）
loadtest/bench.py 压测脚本（零依赖）
tools/verify.py   每日自检（跑完当天任务先自检，绿了再验收）
PLAN.md           14 天计划 + 每日验收标准
PROGRESS.md       每日打卡表
docs/D1-环境.md            JDK/Maven/Docker 装法与 8 个常见坑
docs/压测报告模板.md        D3/D9/D11 往里填数字
docs/面试话术提纲.md        10 题骨架句式（照着练，别背稿）
```

## 面试可讲的 8 个点（做完自然会有答案）

1. 为什么用 Redis+Lua 而不是 DB 行锁扣库存？超卖是怎么被杜绝的？
2. 消息发出去但消费失败了怎么办？幂等怎么做的（唯一索引 vs Redis 标记）？
3. 削峰后"排队中"的用户怎么知道结果？轮询 vs 推送。
4. 一人一单在高并发下怎么保证（先查后写为什么会挂）？
5. 限流放网关还是应用层？令牌桶参数怎么定？
6. 压测从 X 提到 Y 的过程中，瓶颈到底在哪（看什么指标定位）？
7. 未支付订单怎么回补库存？延迟队列 vs 定时扫表。
8. 如果把 Redis 打挂，系统表现如何？降级方案是什么？

## License

MIT
