package com.store.model

import com.store.exceptions.UnrecognizedTypeException
import jakarta.validation.ValidationException

object DB {
    private var PRODUCTS: MutableMap<Int, Product> =
        mutableMapOf(10 to Product("XYZ Phone", "gadget", 10, 10), 20 to Product("Gemini", "dog", 10, 20))
    private var ORDERS: MutableMap<Int, Order> =
        mutableMapOf(10 to Order(10, 2, OrderStatus.pending, 10), 20 to Order(10, 1, OrderStatus.pending, 20))
    private val USERS: Map<String, User> = mapOf("API-TOKEN-SPEC" to User("Hari"))

    fun userCount(): Int {
        return USERS.values.count()
    }

    fun resetDB() {
        PRODUCTS = mutableMapOf(10 to Product("XYZ Phone", "gadget", 10, 10), 20 to Product("Gemini", "dog", 10, 20))
        ORDERS = mutableMapOf(10 to Order(10, 2, OrderStatus.pending, 10), 20 to Order(10, 1, OrderStatus.pending, 20))
    }

    fun addProduct(product: Product) {
        PRODUCTS[product.id] = product
    }

    fun findProduct(id: Int): Product = PRODUCTS.getValue(id)

    fun updateProduct(update: Product) {
        PRODUCTS[update.id] = run {
            PRODUCTS.getValue(update.id)
            Product(update.name, update.type, update.inventory)
        }
    }

    fun deleteProduct(id: Int) {
        PRODUCTS.remove(id)
    }

    fun findProducts(name: String?, type: String?, status: String?): List<Product> {
        if (type != null && type !in listOf("book", "food", "gadget", "other"))
            throw UnrecognizedTypeException(type)

        return PRODUCTS.filter { (id, product) ->
            product.name == name || product.type == type || inventoryStatus(id) == status
        }.values.toList()
    }

    private fun inventoryStatus(productid: Int): String {
        return when (PRODUCTS.getValue(productid).inventory) {
            0 -> "sold"
            else -> "available"
        }
    }

    fun addOrder(order: Order) {
        ORDERS[order.id] = order
    }

    fun getOrder(id: Int): Order = ORDERS.getValue(id)

    fun deleteOrder(id: Int) {
        ORDERS.remove(id)
    }

    fun findOrders(status: OrderStatus?, productId: Int?): List<Order> {
        return ORDERS.filter { (_, order) ->
            order.status == status || order.productid == productId
        }.values.toList()
    }

    fun cleanSlate() {
        PRODUCTS.clear()
        ORDERS.clear()
    }

    fun updateOrder(updatedOrder: Order) {
        ORDERS[updatedOrder.id] = updatedOrder
    }

    fun reserveProductInventory(productId: Int, count: Int) {
        if (productId !in PRODUCTS)
            throw ValidationException("Product Id $productId does not exist")
        val updatedProduct = PRODUCTS.getValue(productId).let {
            it.copy(inventory = it.inventory - count)
        }

        PRODUCTS[productId] = updatedProduct
    }

    fun getUserForToken(token: String) = USERS[token]
}
