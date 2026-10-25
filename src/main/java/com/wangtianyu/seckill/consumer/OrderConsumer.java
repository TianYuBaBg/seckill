package com.wangtianyu.seckill.consumer;

import com.wangtianyu.seckill.config.RabbitConfig;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.stereotype.Component;

@Slf4j
@Component
@RequiredArgsConstructor
public class OrderConsumer {

    /**
     * TODO D6：消费秒杀消息，落库创建订单
     * 要求：① 幂等（唯一索引 uk_user_sku + 重复消息直接丢弃）② 失败重试 ③ 记录消费耗时
     */
    @RabbitListener(queues = RabbitConfig.ORDER_QUEUE)
    public void onMessage(String payload) {
        log.info("TODO D6: 收到秒杀消息 {}", payload);
    }
}
