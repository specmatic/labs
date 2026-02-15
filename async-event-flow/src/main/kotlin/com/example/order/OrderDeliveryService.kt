package com.example.order

import com.fasterxml.jackson.core.JsonProcessingException
import com.fasterxml.jackson.databind.DeserializationFeature
import com.fasterxml.jackson.module.kotlin.jacksonObjectMapper
import org.apache.kafka.clients.consumer.ConsumerRecord
import org.springframework.kafka.annotation.KafkaListener
import org.springframework.kafka.support.Acknowledgment
import org.springframework.stereotype.Service

private const val SERVICE_NAME = "OrderDeliveryService"
private const val ORDER_OUT_FOR_DELIVERY_TOPIC = "out-for-delivery-orders"

@Service
class OrderDeliveryService(
    private val orderRepository: OrderRepository,
    private val taxServiceClient: TaxServiceClient
) {
    private val mapper = jacksonObjectMapper().apply {
        configure(DeserializationFeature.FAIL_ON_NULL_FOR_PRIMITIVES, true)
    }

    init {
        println("$SERVICE_NAME started running..")
    }

    @KafkaListener(topics = [ORDER_OUT_FOR_DELIVERY_TOPIC])
    fun orderDeliveryUpdates(record: ConsumerRecord<String, String>, ack: Acknowledgment) {
        when(record.topic()) {
            ORDER_OUT_FOR_DELIVERY_TOPIC -> initiateOrderDelivery(record, ack)
        }
    }

    private fun initiateOrderDelivery(record: ConsumerRecord<String, String>, ack: Acknowledgment) {
        val orderDeliveryRequest = record.value()
        println("[$SERVICE_NAME] Received message on topic $ORDER_OUT_FOR_DELIVERY_TOPIC - $orderDeliveryRequest")

        try {
            val request = mapper.readValue(orderDeliveryRequest, OrderDeliveryRequest::class.java)

            // Check if order already processed (idempotency)
            try {
                orderRepository.findById(request.orderId, OrderStatus.SHIPPED)
                println("[$SERVICE_NAME] Order ${request.orderId} already processed with status SHIPPED, skipping")
                ack.acknowledge()
                return
            } catch (_: OrderNotFoundException) {
                // Order not found, proceed with processing
            }

            val currentStatus = OrderStatus.SHIPPED

            val invoice = taxServiceClient.raiseInvoice(
                orderId = request.orderId,
                invoiceDate = request.deliveryDate
            )
            println(
                "[$SERVICE_NAME] Tax invoice '${invoice.invoiceId}' raised with status '${invoice.status}' for orderId '${request.orderId}'"
            )

            // Save order with status maintained by this service
            orderRepository.save(
                Order(
                    id = request.orderId,
                    lastUpdatedDate = request.deliveryDate,
                    status = currentStatus
                )
            )
            println("[$SERVICE_NAME] Order with orderId '${request.orderId}' is $currentStatus")

            // Only acknowledge after successful processing
            ack.acknowledge()
        } catch (e: JsonProcessingException) {
            // Malformed message: log and acknowledge to skip it (could send to DLQ in production)
            println("[$SERVICE_NAME] Failed to parse message, acknowledging to skip: $orderDeliveryRequest")
            e.printStackTrace()
            ack.acknowledge()
        } catch (e: Exception) {
            // Transient errors: don't acknowledge so Kafka can retry or move to DLQ based on config
            println("[$SERVICE_NAME] Error processing message, will retry: $orderDeliveryRequest")
            e.printStackTrace()
            throw e
        }
    }

    fun findById(orderId: Int, status: OrderStatus): Order? {
        return orderRepository.findById(orderId, status)
    }
}

data class OrderDeliveryRequest(
    val orderId: Int,
    val deliveryAddress: String,
    val deliveryDate: String
)
