package com.example.order

import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.*

private const val NAME = "OrderController"

@RestController
@RequestMapping("/orders")
class OrderController(
    private val orderDeliveryService: OrderDeliveryService,
    private val orderAcceptanceService: OrderAcceptanceService
) {

    @GetMapping("/{id}")
    fun getOrderWith(
        @PathVariable id: Int,
        @RequestParam status: String
    ): ResponseEntity<Order> {
        println("[$NAME] Received request to find Order with id '$id' and status '$status'")
        return ResponseEntity.ok(orderDeliveryService.findById(id, OrderStatus.valueOf(status)))
    }

    @PutMapping
    fun updateOrder(@RequestBody request: OrderUpdateRequest): ResponseEntity<String> {
        println("[$NAME] Received update request: $request")
        orderAcceptanceService.notify(request)
        return ResponseEntity.ok("Notification triggered.")
    }
}
data class OrderUpdateRequest(
    val id: Int,
    val status: OrderStatus,
    val timestamp: String
)