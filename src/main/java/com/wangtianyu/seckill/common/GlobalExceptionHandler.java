package com.wangtianyu.seckill.common;

import lombok.extern.slf4j.Slf4j;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.web.HttpRequestMethodNotSupportedException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.servlet.resource.NoResourceFoundException;

@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

    /** 业务异常：按约定码返回，演示时能直接看到 1001 已售罄、1003 一人一单 */
    @ExceptionHandler(BizException.class)
    public Result<Void> handleBiz(BizException e) {
        return Result.fail(e.getCode(), e.getMessage());
    }

    /** 唯一索引冲突：最常见就是 seckill_order 的 UK(user_id, sku_id)——重复下单 */
    @ExceptionHandler(DuplicateKeyException.class)
    public Result<Void> handleDuplicateKey(DuplicateKeyException e) {
        log.warn("唯一索引冲突（大概率是重复下单）: {}", e.getMostSpecificCause().getMessage());
        return Result.fail(1003, "你已经抢到过了，一人一单");
    }

    /** 404 不要伪装成 500 系统繁忙，否则排错能查一晚上 */
    @ExceptionHandler(NoResourceFoundException.class)
    public Result<Void> handleNotFound(NoResourceFoundException e) {
        return Result.fail(404, "接口不存在：" + e.getResourcePath());
    }

    /** 路径对但方法不对（比如该 POST 的地方发了 GET） */
    @ExceptionHandler(HttpRequestMethodNotSupportedException.class)
    public Result<Void> handleMethod(HttpRequestMethodNotSupportedException e) {
        return Result.fail(405, "这个接口只支持 " + e.getSupportedHttpMethods() + "，你用的是 " + e.getMethod());
    }

    @ExceptionHandler(Exception.class)
    public Result<Void> handleOther(Exception e) {
        log.error("unexpected error", e);
        return Result.fail(500, "系统繁忙");
    }
}
