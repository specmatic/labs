package com.store.services

import com.store.exceptions.ValidationException
import com.store.model.DB
import com.store.model.Id
import com.store.model.Order
import com.store.model.OrderStatus
import org.springframework.stereotype.Service

@Service
class OrderService {
    fun createOrder(order: Order): Id {
        DB.reserveProductInventory(order.productid, order.count)
        DB.addOrder(order)
        return Id(order.id)
    }

    fun getOrder(id: Int): Order {
        return DB.getOrder(id)
    }

    fun deleteOrder(id: Int) {
        DB.deleteOrder(id)
    }

    fun updateOrder(order: Order) {
        if (order.id == 0)
            throw ValidationException("Product id cannot be null")
        DB.updateOrder(order)
    }

    fun findOrders(status: OrderStatus?, productid: Int?): List<Order> {
        return DB.findOrders(status, productid)
    }
}