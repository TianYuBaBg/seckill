CREATE DATABASE IF NOT EXISTS seckill DEFAULT CHARSET utf8mb4;
USE seckill;

DROP TABLE IF EXISTS sku_stock;
CREATE TABLE sku_stock (
  id       BIGINT PRIMARY KEY AUTO_INCREMENT,
  sku_id   BIGINT       NOT NULL COMMENT '商品ID',
  sku_name VARCHAR(128) NOT NULL COMMENT '商品名',
  stock    INT          NOT NULL DEFAULT 0 COMMENT '剩余库存',
  sold     INT          NOT NULL DEFAULT 0 COMMENT '已售',
  version  INT          NOT NULL DEFAULT 0 COMMENT '乐观锁版本',
  UNIQUE KEY uk_sku (sku_id)
) ENGINE = InnoDB COMMENT '商品库存';

DROP TABLE IF EXISTS seckill_order;
CREATE TABLE seckill_order (
  id          BIGINT PRIMARY KEY AUTO_INCREMENT,
  order_no    VARCHAR(64) NOT NULL COMMENT '订单号',
  user_id     BIGINT      NOT NULL COMMENT '用户ID',
  sku_id      BIGINT      NOT NULL COMMENT '商品ID',
  quantity    INT         NOT NULL DEFAULT 1,
  status      TINYINT     NOT NULL DEFAULT 0 COMMENT '0待支付 1已支付 2已取消',
  create_time DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  pay_time    DATETIME    NULL,
  UNIQUE KEY uk_order_no (order_no),
  UNIQUE KEY uk_user_sku (user_id, sku_id) COMMENT '一人一单（幂等兜底）',
  KEY idx_sku (sku_id)
) ENGINE = InnoDB COMMENT '秒杀订单';

INSERT INTO sku_stock (sku_id, sku_name, stock, sold, version)
VALUES (1001, 'iPhone 16 Pro 256G（秒杀）', 1000, 0, 0);
