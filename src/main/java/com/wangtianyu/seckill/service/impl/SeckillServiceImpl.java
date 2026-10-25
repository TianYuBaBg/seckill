package com.wangtianyu.seckill.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.wangtianyu.seckill.common.BizException;
import com.wangtianyu.seckill.common.Result;
import com.wangtianyu.seckill.entity.SeckillOrder;
import com.wangtianyu.seckill.entity.SkuStock;
import com.wangtianyu.seckill.mapper.SeckillOrderMapper;
import com.wangtianyu.seckill.mapper.SkuStockMapper;
import com.wangtianyu.seckill.service.SeckillService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * D2 参考实现（分支 ref/d2，仅用于对照，别直接抄进 main）。
 * 三个方法对应 docs/D2-照着做.md 里的三段。
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class SeckillServiceImpl implements SeckillService {

    private final SkuStockMapper skuStockMapper;
    private final SeckillOrderMapper seckillOrderMapper;

    @Override
    public Result<String> detail(Long skuId) {
        SkuStock stock = skuStockMapper.selectOne(
                new LambdaQueryWrapper<SkuStock>().eq(SkuStock::getSkuId, skuId));
        if (stock == null) {
            throw new BizException(404, "商品不存在");
        }
        return Result.ok(stock.getSkuName() + " 剩余 " + stock.getStock());
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public Result<String> seckill(Long skuId, Long userId) {
        // ① 原子扣库存：靠 where stock >= qty 保证不超卖
        int rows = skuStockMapper.deductStock(skuId, 1);
        if (rows == 0) {
            return Result.fail(1001, "已售罄");
        }
        // ② 落订单：重复下单会撞 UK(user_id, sku_id) → 异常 → 事务回滚
        SeckillOrder order = new SeckillOrder();
        order.setOrderNo(System.currentTimeMillis() + "" + userId);
        order.setUserId(userId);
        order.setSkuId(skuId);
        order.setQuantity(1);
        order.setStatus(0);
        seckillOrderMapper.insert(order);
        log.info("秒杀成功 skuId={} userId={} orderNo={}", skuId, userId, order.getOrderNo());
        return Result.ok(order.getOrderNo());
    }

    @Override
    public Result<String> result(Long skuId, Long userId) {
        SeckillOrder o = seckillOrderMapper.selectOne(new LambdaQueryWrapper<SeckillOrder>()
                .eq(SeckillOrder::getUserId, userId)
                .eq(SeckillOrder::getSkuId, skuId));
        return o == null
                ? Result.fail(1002, "没有下单记录")
                : Result.ok("订单号 " + o.getOrderNo() + "，状态 " + o.getStatus());
    }
}
