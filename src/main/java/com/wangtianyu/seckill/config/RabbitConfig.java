package com.wangtianyu.seckill.config;

import org.springframework.amqp.core.Binding;
import org.springframework.amqp.core.BindingBuilder;
import org.springframework.amqp.core.DirectExchange;
import org.springframework.amqp.core.Queue;
import org.springframework.amqp.core.QueueBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class RabbitConfig {

    public static final String EXCHANGE = "seckill.exchange";
    public static final String ORDER_QUEUE = "seckill.order.queue";
    public static final String ORDER_ROUTING_KEY = "seckill.order.create";

    @Bean
    public DirectExchange seckillExchange() {
        return new DirectExchange(EXCHANGE, true, false);
    }

    @Bean
    public Queue orderQueue() {
        return QueueBuilder.durable(ORDER_QUEUE).build();
    }

    @Bean
    public Binding orderBinding(Queue orderQueue, DirectExchange seckillExchange) {
        return BindingBuilder.bind(orderQueue).to(seckillExchange).with(ORDER_ROUTING_KEY);
    }
}
