package com.example.order

import io.specmatic.enterprise.SpecmaticContractTest
import org.junit.jupiter.api.TestInstance
import org.springframework.boot.test.context.SpringBootTest
import org.springframework.kafka.test.context.EmbeddedKafka
import org.springframework.test.annotation.DirtiesContext

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.DEFINED_PORT)
@EmbeddedKafka(
    ports = [9092],
    topics = [
        "new-orders",
        "wip-orders",
        "to-be-cancelled-orders",
        "cancelled-orders",
        "accepted-orders",
        "out-for-delivery-orders"
    ],
    brokerProperties = [
        "listeners=PLAINTEXT://0.0.0.0:9092",
        "advertised.listeners=PLAINTEXT://localhost:9092"
    ],
    bootstrapServersProperty = "spring.kafka.bootstrap-servers"
)
@TestInstance(TestInstance.Lifecycle.PER_CLASS)
@DirtiesContext(classMode = DirtiesContext.ClassMode.AFTER_CLASS)
class ContractTest : SpecmaticContractTest
