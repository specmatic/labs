package com.example.order

import org.springframework.boot.SpringApplication
import org.springframework.boot.autoconfigure.SpringBootApplication
import org.springframework.kafka.annotation.EnableKafka

@SpringBootApplication
@EnableKafka
class OrderServiceApplication

fun main() {
    SpringApplication.run(OrderServiceApplication::class.java)
}

