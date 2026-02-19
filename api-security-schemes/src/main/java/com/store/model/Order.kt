package com.store.model

import java.util.concurrent.atomic.AtomicInteger
import jakarta.validation.constraints.NotNull
import jakarta.validation.constraints.Positive

class Order(@field:Positive val productid: Int = 0, @field:Positive val count: Int = 0, @field:NotNull var status: OrderStatus = OrderStatus.pending, val id: Int = idGenerator.getAndIncrement()) {
    companion object {
        val idGenerator: AtomicInteger = AtomicInteger()
    }
}

enum class OrderStatus {
    pending,
    fulfilled,
    cancelled
}