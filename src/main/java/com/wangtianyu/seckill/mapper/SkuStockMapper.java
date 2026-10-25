package com.wangtianyu.seckill.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.wangtianyu.seckill.entity.SkuStock;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Update;

@Mapper
public interface SkuStockMapper extends BaseMapper<SkuStock> {

    /** D2：DB 层扣减（先用乐观锁，后面再上 Redis） */
    @Update("update sku_stock set stock = stock - #{qty}, sold = sold + #{qty}, version = version + 1 "
            + "where sku_id = #{skuId} and stock >= #{qty}")
    int deductStock(@Param("skuId") Long skuId, @Param("qty") int qty);
}
