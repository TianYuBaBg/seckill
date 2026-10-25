package com.wangtianyu.seckill.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

@Data
@TableName("sku_stock")
public class SkuStock {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long skuId;
    private String skuName;
    /** 剩余库存 */
    private Integer stock;
    /** 已售 */
    private Integer sold;
    /** 乐观锁版本号（D2 用） */
    private Integer version;
}
