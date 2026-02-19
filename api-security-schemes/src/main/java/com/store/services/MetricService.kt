package com.store.services

import com.store.model.DB
import org.springframework.stereotype.Service

@Service
class MetricService {
    fun activeUsers(): Int {
        return DB.userCount()
    }
}
