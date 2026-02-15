package com.example.order

import com.fasterxml.jackson.databind.ObjectMapper
import org.springframework.kafka.core.KafkaTemplate
import org.springframework.stereotype.Service

private const val SERVICE_NAME = "OrderAcceptanceService"
private const val TOPIC_NAME = "accepted-orders"

@Service
class OrderAcceptanceService(
    private val kafkaTemplate: KafkaTemplate<String, String>
) {

    fun notify(request: OrderUpdateRequest) {
        println("[$SERVICE_NAME] Publishing the acceptance message on topic '$TOPIC_NAME'..")
        kafkaTemplate.send(
            TOPIC_NAME,
           ObjectMapper().writeValueAsString(request)
        ).get()
    }
}