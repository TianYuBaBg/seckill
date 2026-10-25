#!/bin/bash
# 中间件一键开关（在你机器上，MySQL/Redis/RabbitMQ 装在 WSL Ubuntu 22.04 里）
#
# 用法（在 Windows 的 PowerShell/CMD 里）：
#   wsl -d Ubuntu-22.04 -u root -- bash /mnt/d/me/seckill/tools/wsl-mw.sh start
#   wsl -d Ubuntu-22.04 -u root -- bash /mnt/d/me/seckill/tools/wsl-mw.sh stop
#   wsl -d Ubuntu-22.04 -u root -- bash /mnt/d/me/seckill/tools/wsl-mw.sh status
#   wsl -d Ubuntu-22.04 -u root -- bash /mnt/d/me/seckill/tools/wsl-mw.sh reset-stock
SERVICES="mysql redis-server rabbitmq-server"

show_status() {
  for s in $SERVICES; do
    printf '  %-18s %s\n' "$s" "$(systemctl is-active "$s" 2>/dev/null || echo unknown)"
  done
  echo "  --- 监听端口 ---"
  ss -lnt 2>/dev/null | grep -E ':(3306|6379|5672|15672)\b' | awk '{print "  " $4}'
}

case "$1" in
  start)
    for s in $SERVICES; do systemctl start "$s"; done
    sleep 2
    echo "已启动："; show_status
    ;;
  stop)
    for s in $SERVICES; do systemctl stop "$s"; done
    echo "已停止。"
    ;;
  status|"")
    echo "当前状态："; show_status
    ;;
  reset-stock)
    mysql -uroot -proot seckill -e "TRUNCATE TABLE seckill_order; UPDATE sku_stock SET stock=1000, sold=0, version=0 WHERE sku_id=1001;" 2>/dev/null
    echo "已重置：seckill_order 清空，sku_stock 库存回到 1000"
    mysql -uroot -proot seckill -e "SELECT sku_id, sku_name, stock, sold FROM sku_stock;" 2>/dev/null
    ;;
  *)
    echo "用法: $0 {start|stop|status|reset-stock}"
    exit 1
    ;;
esac
