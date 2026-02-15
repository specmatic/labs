package com.example.order

import org.springframework.beans.factory.annotation.Value
import org.springframework.stereotype.Component
import org.springframework.web.reactive.function.client.WebClient
import org.springframework.web.reactive.function.client.bodyToMono
import java.time.Duration

@Component
class TaxServiceClient(
    private val webClient: WebClient,
    @param:Value($$"${tax-service.base-url}") private val baseUrl: String,
    @param:Value($$"${tax-service.timeout-seconds:3}") private val timeoutSeconds: Long,
    @param:Value($$"${tax-service.retry-attempts:1}") private val retryAttempts: Long
) {
    fun raiseInvoice(orderId: Int, invoiceDate: String): TaxInvoiceResponse {
        val path = "$baseUrl/tax/invoices"
        val request = TaxInvoiceRequest(orderId = orderId, invoiceDate = invoiceDate)
        println("[TaxServiceClient] Raising tax invoice for orderId: $orderId at $path")

        return try {
            webClient.post()
                .uri(path)
                .bodyValue(request)
                .retrieve()
                .bodyToMono<TaxInvoiceResponse>()
                .timeout(Duration.ofSeconds(timeoutSeconds))
                .retry(retryAttempts)
                .block() ?: throw IllegalStateException("Empty invoice response for order $orderId")
        } catch (e: Exception) {
            println("[TaxServiceClient] Failed to raise tax invoice for order $orderId")
            e.printStackTrace()
            throw e
        }
    }
}

data class TaxInvoiceRequest(
    val orderId: Int,
    val invoiceDate: String
)

data class TaxInvoiceResponse(
    val invoiceId: String,
    val status: String,
    val orderId: Int
)
