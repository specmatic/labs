package com.example.order

import com.example.order.OrderStatus.*
import com.fasterxml.jackson.databind.DeserializationFeature
import com.fasterxml.jackson.module.kotlin.jacksonObjectMapper
import org.apache.kafka.clients.consumer.ConsumerRecord
import org.apache.kafka.clients.producer.ProducerRecord
import org.apache.kafka.common.header.internals.RecordHeader
import org.apache.kafka.common.header.internals.RecordHeaders
import org.springframework.kafka.annotation.KafkaListener
import org.springframework.kafka.core.KafkaTemplate
import org.springframework.kafka.support.Acknowledgment
import org.springframework.stereotype.Service

private const val SERVICE_NAME = "OrderService"
private const val NEW_ORDERS_TOPIC = "new-orders"
private const val WIP_ORDERS_TOPIC = "wip-orders"
private const val TO_BE_CANCELLED_ORDERS_TOPIC = "to-be-cancelled-orders"
private const val CANCELLED_ORDERS_TOPIC = "cancelled-orders"

@Service
class OrderService(
    private val kafkaTemplate: KafkaTemplate<String, String>,
    private val orderRepository: OrderRepository
) {
    init {
        println("$SERVICE_NAME started running..")
    }

    @KafkaListener(topics = [NEW_ORDERS_TOPIC, TO_BE_CANCELLED_ORDERS_TOPIC])
    fun orderUpdates(record: ConsumerRecord<String, String>, ack: Acknowledgment) {
        val topic = record.topic()

        when (topic) {
            NEW_ORDERS_TOPIC -> {
                val orderRequest = record.value()
                val headers = record.headers()

                println("[$SERVICE_NAME] Received message on topic $NEW_ORDERS_TOPIC - $orderRequest")
                println("[$SERVICE_NAME] Headers: ${headers.joinToString { "${it.key()}: ${String(it.value())}" }}")

                val placeOrderRequestJson = try {
                    jacksonObjectMapper().apply {
                        configure(DeserializationFeature.FAIL_ON_NULL_FOR_PRIMITIVES, true)
                    }.readValue(orderRequest, PlaceOrderRequest::class.java)
                } catch (e: Exception) {
                    throw e
                }

                processPlaceOrderMessage(placeOrderRequestJson)
            }

            TO_BE_CANCELLED_ORDERS_TOPIC -> {
                val cancellationRequest = record.value()

                println("[$SERVICE_NAME] Received message on topic $TO_BE_CANCELLED_ORDERS_TOPIC - $cancellationRequest")

                val orderIdObject = try {
                    jacksonObjectMapper().apply {
                        configure(DeserializationFeature.FAIL_ON_NULL_FOR_PRIMITIVES, true)
                    }.readValue(cancellationRequest, OrderId::class.java)
                } catch (e: Exception) {
                    throw e
                }

                processCancellation(orderIdObject)
            }
        }

        ack.acknowledge()
    }

    private fun processPlaceOrderMessage(placeOrderRequest: PlaceOrderRequest) {
        val order = Order(
            id = placeOrderRequest.id,
            orderItems = placeOrderRequest.orderItems,
            status = INITIATED
        )
        sendMessageOnProcessOrderTopic(order)
        orderRepository.save(order)
    }

    private fun processCancellation(id: OrderId) {
        val order = Order(
            id = id.id,
            status = CANCELLED
        )
        sendMessageOnProcessCancellationTopic(order)
        orderRepository.save(order)
    }

    private fun sendMessageOnProcessCancellationTopic(order: Order) {
        val headers = RecordHeaders().apply {
            add(RecordHeader("orderCorrelationId", "12345".toByteArray(Charsets.UTF_8)))
        }
        val cancellationMessage = """{"reference": ${order.id}, "status": "${order.status}"}"""
        val record = ProducerRecord<String, String>(CANCELLED_ORDERS_TOPIC, null, null, null, cancellationMessage, headers)

        println("[$SERVICE_NAME] Publishing a message on $CANCELLED_ORDERS_TOPIC topic: $cancellationMessage")
        kafkaTemplate.send(record)
    }

    private fun sendMessageOnProcessOrderTopic(order: Order) {
        val headers = RecordHeaders().apply {
            add(RecordHeader("orderCorrelationId", "12345".toByteArray(Charsets.UTF_8)))
        }
        val taskMessage =
            """{"id": ${order.id}, "totalAmount": ${order.totalAmount()}, "status": "${order.status}"}"""

        val record = ProducerRecord<String, String>(WIP_ORDERS_TOPIC, null, null, null, taskMessage, headers)
        kafkaTemplate.send(record)
    }
}

data class PlaceOrderRequest(
    val id: Int,
    val orderItems: List<OrderItem>
)