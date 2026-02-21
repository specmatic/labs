package com.example.order

import order.OrderRequest
import order.OrderStatus
import order.OrderToProcess
import org.apache.kafka.clients.consumer.ConsumerRecord
import org.springframework.kafka.annotation.KafkaListener
import org.springframework.kafka.core.KafkaTemplate
import org.springframework.stereotype.Service

@Service
class OrderService(
    private val kafkaTemplate: KafkaTemplate<String, OrderToProcess>,
) {
    companion object {
        private const val NEW_ORDERS_TOPIC = "new-orders"
        private const val WIP_ORDERS_TOPIC = "wip-orders"
    }

    private val serviceName = this::class.simpleName

    init {
        println("$serviceName started running..")
    }

    @KafkaListener(topics = [NEW_ORDERS_TOPIC])
    fun placeOrder(record: ConsumerRecord<String, OrderRequest>) {
        val orderRequest = record.value()
        println("[$serviceName] Received message on topic $NEW_ORDERS_TOPIC - $orderRequest")

        val orderToProcess = OrderToProcess.newBuilder()
            .setId(orderRequest.id)
            .setStatus(OrderStatus.PROCESSING)
            .build()
        kafkaTemplate.send(WIP_ORDERS_TOPIC, orderToProcess)
        println("[$serviceName] Sent message to topic $WIP_ORDERS_TOPIC - $orderToProcess")
    }
}