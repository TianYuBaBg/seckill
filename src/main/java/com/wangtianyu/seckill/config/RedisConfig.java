package com.wangtianyu.seckill.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.io.ClassPathResource;
import org.springframework.data.redis.connection.RedisConnectionFactory;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.core.script.DefaultRedisScript;
import org.springframework.data.redis.serializer.StringRedisSerializer;
import org.springframework.util.StreamUtils;

import java.io.IOException;
import java.nio.charset.StandardCharsets;

@Configuration
public class RedisConfig {

    @Bean
    public RedisTemplate<String, String> redisTemplate(RedisConnectionFactory factory) {
        RedisTemplate<String, String> t = new RedisTemplate<>();
        t.setConnectionFactory(factory);
        t.setKeySerializer(new StringRedisSerializer());
        t.setValueSerializer(new StringRedisSerializer());
        t.setHashKeySerializer(new StringRedisSerializer());
        t.setHashValueSerializer(new StringRedisSerializer());
        t.afterPropertiesSet();
        return t;
    }

    /**
     * 秒杀扣减脚本 —— D4 由你补全 src/main/resources/lua/seckill.lua
     * 约定：KEYS[1] = 库存 key，ARGV[1] = 购买数量
     * 返回：>=0 扣减成功后的剩余库存；-1 库存不足；-2 key 不存在
     */
    @Bean
    public DefaultRedisScript<Long> seckillScript() throws IOException {
        String lua = StreamUtils.copyToString(
                new ClassPathResource("lua/seckill.lua").getInputStream(), StandardCharsets.UTF_8);
        DefaultRedisScript<Long> script = new DefaultRedisScript<>();
        script.setScriptText(lua);
        script.setResultType(Long.class);
        return script;
    }
}
