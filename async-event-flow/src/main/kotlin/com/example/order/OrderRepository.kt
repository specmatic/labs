package com.example.order

import org.springframework.stereotype.Repository

@Repository
class OrderRepository {
    private val orders = mutableListOf(
        Order(123, status = OrderStatus.SHIPPED)
    )

    fun save(order: Order) {
        orders.add(order)
    }

    fun findById(id: Int, status: OrderStatus): Order {
        return orders.find {
            it.id == id && it.status == status
        } ?: throw OrderNotFoundException("Cannot find order with Id: '$id' and status: '$status'")
    }
}

class OrderNotFoundException(
    override val message: String
) : Exception(message)