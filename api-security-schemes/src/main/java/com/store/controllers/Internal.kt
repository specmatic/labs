package com.store.controllers

import com.store.services.MetricService
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.RestController

@RestController
class Internal {
    @Autowired
    lateinit var metricService: MetricService
    @GetMapping("/internal/metrics")
    fun metrics(): Int {
        return metricService.activeUsers()
    }
}