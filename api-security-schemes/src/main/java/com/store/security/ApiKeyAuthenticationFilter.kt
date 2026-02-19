package com.store.security

import com.store.model.User
import org.springframework.http.HttpMethod
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken
import org.springframework.security.core.authority.SimpleGrantedAuthority
import org.springframework.security.core.context.SecurityContextHolder
import org.springframework.web.filter.OncePerRequestFilter
import jakarta.servlet.FilterChain
import jakarta.servlet.http.HttpServletRequest
import jakarta.servlet.http.HttpServletResponse

class ApiKeyAuthenticationFilter : OncePerRequestFilter() {

    companion object {
        private const val API_KEY_HEADER = "X-API-Key"
        private const val VALID_API_KEY = "APIKEY1234"  // In production, this should come from configuration
    }

    override fun doFilterInternal(
        request: HttpServletRequest,
        response: HttpServletResponse,
        filterChain: FilterChain
    ) {
        // Only process DELETE requests
        if (request.method == HttpMethod.DELETE.name()) {
            val apiKey = request.getHeader(API_KEY_HEADER)

            if (apiKey != null && apiKey == VALID_API_KEY) {
                logger.info("Request: ${request.method} ${request.requestURI} authenticated with valid API Key")
                val authorities = listOf(SimpleGrantedAuthority("ROLE_API_KEY_USER"))
                val authentication = UsernamePasswordAuthenticationToken(
                    User("api_key_user"),
                    null,
                    authorities
                )
                SecurityContextHolder.getContext().authentication = authentication
            } else {
                logger.warn("Request: ${request.method} ${request.requestURI} has invalid or missing API Key")
            }
        }

        filterChain.doFilter(request, response)
    }
}

