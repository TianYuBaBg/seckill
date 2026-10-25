package com.wangtianyu.seckill.controller;

import com.wangtianyu.seckill.common.Result;
import com.wangtianyu.seckill.service.SeckillService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/seckill")
@RequiredArgsConstructor
public class SeckillController {

    private final SeckillService seckillService;

    @GetMapping("/detail/{skuId}")
    public Result<String> detail(@PathVariable Long skuId) {
        return seckillService.detail(skuId);
    }

    @PostMapping("/{skuId}")
    public Result<String> seckill(@PathVariable Long skuId, @RequestParam Long userId) {
        return seckillService.seckill(skuId, userId);
    }

    @GetMapping("/result/{skuId}/{userId}")
    public Result<String> result(@PathVariable Long skuId, @PathVariable Long userId) {
        return seckillService.result(skuId, userId);
    }
}
