package com.store.security

import com.store.model.User
import org.springframework.security.core.context.SecurityContextHolder
import org.springframework.security.oauth2.server.resource.authentication.JwtAuthenticationToken
import org.springframework.security.web.authentication.preauth.PreAuthenticatedAuthenticationToken
import org.springframework.web.filter.OncePerRequestFilter
import jakarta.servlet.FilterChain
import jakarta.servlet.http.HttpServletRequest
import jakarta.servlet.http.HttpServletResponse

class JwtAuthenticationFilter : OncePerRequestFilter() {

    override fun doFilterInternal(
        request: HttpServletRequest,
        response: HttpServletResponse,
        filterChain: FilterChain
    ) {
        val authentication = SecurityContextHolder.getContext().authentication
        if (authentication is JwtAuthenticationToken) {
            logger.info("Request: ${request.method} ${request.requestURI} received with a JWT token with scopes: ${authentication.authorities.joinToString(", ")}")
            SecurityContextHolder.getContext().authentication =
                PreAuthenticatedAuthenticationToken(User("authenticated_user"), null, authentication.authorities)
        }
        filterChain.doFilter(request, response)
    }

}