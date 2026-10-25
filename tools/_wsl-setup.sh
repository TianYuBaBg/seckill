#!/bin/bash
set -e
echo "===== MySQL ====="
systemctl start mysql
sleep 2
mysql -uroot -e "ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'root'; FLUSH PRIVILEGES;" || echo "(密码可能已是 root)"
mysql -uroot -proot -e "CREATE DATABASE IF NOT EXISTS seckill DEFAULT CHARACTER SET utf8mb4;" 2>/dev/null
mysql -uroot -proot -e "SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='seckill';" 2>/dev/null

sed -i "s/^bind-address.*/bind-address = 0.0.0.0/" /etc/mysql/mysql.conf.d/mysqld.cnf
grep -q "^mysqlx-bind-address" /etc/mysql/mysql.conf.d/mysqld.cnf && sed -i "s/^mysqlx-bind-address.*/mysqlx-bind-address = 0.0.0.0/" /etc/mysql/mysql.conf.d/mysqld.cnf
systemctl restart mysql
sleep 3
echo -n "mysql 状态: "; systemctl is-active mysql

echo "===== Redis ====="
sed -i "s/^bind 127.0.0.1.*/bind 0.0.0.0/" /etc/redis/redis.conf
sed -i "s/^protected-mode yes/protected-mode no/" /etc/redis/redis.conf
systemctl restart redis-server
sleep 1
echo -n "redis 状态: "; systemctl is-active redis-server
echo -n "redis ping : "; redis-cli ping

echo "===== 监听端口 ====="
ss -lntp 2>/dev/null | grep -E ':(3306|6379)' | head -4
