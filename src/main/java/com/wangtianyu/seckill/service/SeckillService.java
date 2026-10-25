package com.wangtianyu.seckill.service;

import com.wangtianyu.seckill.common.Result;

public interface SeckillService {

    /** 商品详情：D4 加缓存 */
    Result<String> detail(Long skuId);

    /**
     * 秒杀下单
     * D2 版本：直接 DB 扣减
     * D3 版本：Redis + Lua 预扣（不落库），成功后投递 MQ
     * D5 版本：加一人一单
     * D8 版本：加限流
     */
    Result<String> seckill(Long skuId, Long userId);

    /** 查询秒杀结果（前端轮询用） */
    Result<String> result(Long skuId, Long userId);
}
