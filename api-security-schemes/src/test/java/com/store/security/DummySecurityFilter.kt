package com.store.security

import com.store.model.User
import org.springframework.http.HttpMethod
import org.springframework.security.core.context.SecurityContextHolder
import org.springframework.security.web.authentication.preauth.PreAuthenticatedAuthenticationToken
import org.springframework.web.filter.OncePerRequestFilter
import jakarta.servlet.FilterChain
import jakarta.servlet.http.HttpServletRequest
import jakarta.servlet.http.HttpServletResponse
import java.util.Base64

class DummySecurityFilter : OncePerRequestFilter() {
    override fun doFilterInternal(
        request: HttpServletRequest,
        response: HttpServletResponse,
        filterChain: FilterChain
    ) {
        val authenticated = when (request.method) {
            HttpMethod.POST.name() -> authenticateOAuth2(request)
            HttpMethod.GET.name() -> authenticateBasic(request)
            HttpMethod.DELETE.name() -> authenticateApiKey(request)
            else -> false
        }

        if (!authenticated) {
            response.sendError(HttpServletResponse.SC_UNAUTHORIZED, "Authentication failed")
            return
        }

        SecurityContextHolder.getContext().authentication = PreAuthenticatedAuthenticationToken(
            User("Authenticated User"),
            null,
            emptyList()
        ).apply { isAuthenticated = true }

        filterChain.doFilter(request, response)
    }

    private fun authenticateOAuth2(request: HttpServletRequest): Boolean {
        val authHeader = request.getHeader("Authorization")
        return authHeader != null && authHeader.startsWith("Bearer ")
    }

    private fun authenticateBasic(request: HttpServletRequest): Boolean {
        val authHeader = request.getHeader("Authorization")
        if (authHeader != null && authHeader.startsWith("Basic ")) {
            try {
                val base64Credentials = authHeader.substring("Basic ".length)
                val credentials = String(Base64.getDecoder().decode(base64Credentials))
                // Just verify format username:password exists, don't validate actual credentials in test mode
                return credentials.contains(":")
            } catch (e: Exception) {
                return false
            }
        }
        return false
    }

    private fun authenticateApiKey(request: HttpServletRequest): Boolean {
        val apiKey = request.getHeader("X-API-Key")
        return apiKey != null && apiKey.isNotEmpty()
    }
}