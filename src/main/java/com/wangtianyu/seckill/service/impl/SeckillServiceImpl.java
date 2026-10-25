package com.wangtianyu.seckill.service.impl;

import com.wangtianyu.seckill.common.BizException;
import com.wangtianyu.seckill.common.Result;
import com.wangtianyu.seckill.mapper.SkuStockMapper;
import com.wangtianyu.seckill.service.SeckillService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

@Slf4j
@Service
@RequiredArgsConstructor
public class SeckillServiceImpl implements SeckillService {

    private final SkuStockMapper skuStockMapper;

    @Override
    public Result<String> detail(Long skuId) {
        // TODO D2：查库返回 商品名 + 剩余库存
        throw new BizException(501, "TODO D2: 实现商品详情");
    }

    @Override
    public Result<String> seckill(Long skuId, Long userId) {
        // TODO D2：调 skuStockMapper.deductStock(skuId, 1)，成功则写 seckill_order
        throw new BizException(501, "TODO D2: 实现 DB 扣减版秒杀");
    }

    @Override
    public Result<String> result(Long skuId, Long userId) {
        // TODO D2：查订单表返回结果
        throw new BizException(501, "TODO D2: 实现结果查询");
    }
}
