package com.store.config

import com.store.security.ApiKeyAuthenticationFilter
import com.store.security.JwtAuthenticationFilter
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.context.annotation.Profile
import org.springframework.http.HttpMethod
import org.springframework.security.config.annotation.web.builders.HttpSecurity
import org.springframework.security.config.annotation.web.configurers.ExpressionUrlAuthorizationConfigurer
import org.springframework.security.config.annotation.web.configurers.oauth2.server.resource.OAuth2ResourceServerConfigurer
import org.springframework.security.core.userdetails.User
import org.springframework.security.core.userdetails.UserDetailsService
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder
import org.springframework.security.crypto.password.PasswordEncoder
import org.springframework.security.oauth2.server.resource.web.BearerTokenAuthenticationFilter
import org.springframework.security.provisioning.InMemoryUserDetailsManager
import org.springframework.security.web.SecurityFilterChain
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter

@Configuration
@Profile("prod")
open class SecurityConfig {
    @Bean
    open fun filterChain(http: HttpSecurity): SecurityFilterChain? {
        http
            .csrf().disable()  // Disable CSRF for API key and token-based authentication
            .authorizeRequests { auth ->
                // POST endpoints require OAuth2
                auth.requestMatchers(HttpMethod.POST, "/products/**").authenticated()
                auth.requestMatchers(HttpMethod.POST, "/orders/**").authenticated()

                // GET endpoints require Basic Auth
                auth.requestMatchers(HttpMethod.GET, "/products/**").authenticated()
                auth.requestMatchers(HttpMethod.GET, "/orders/**").authenticated()

                // DELETE endpoints require API Key
                auth.requestMatchers(HttpMethod.DELETE, "/products/**").authenticated()
                auth.requestMatchers(HttpMethod.DELETE, "/orders/**").authenticated()

                verifyAuthority(auth.anyRequest())
            }
            .httpBasic()  // Enable Basic Authentication for GET endpoints
        configureFilterChain(http)
        return http.build()
    }

    protected open fun configureFilterChain(http: HttpSecurity) {
        // Add API Key filter for DELETE endpoints - must run before authentication checks
        http.addFilterBefore(ApiKeyAuthenticationFilter(), UsernamePasswordAuthenticationFilter::class.java)

        // Add JWT filter for OAuth2 (POST endpoints)
        http.addFilterAfter(JwtAuthenticationFilter(), BearerTokenAuthenticationFilter::class.java)


        http.oauth2ResourceServer { obj: OAuth2ResourceServerConfigurer<HttpSecurity?> -> obj.jwt() }
    }

    protected open fun verifyAuthority(authorizedUrl: ExpressionUrlAuthorizationConfigurer<HttpSecurity>.AuthorizedUrl) {
        authorizedUrl.permitAll()
    }

    @Bean
    open fun userDetailsService(): UserDetailsService {
        val user = User.builder()
            .username("user")
            .password(passwordEncoder().encode("password"))
            .roles("USER")
            .build()
        return InMemoryUserDetailsManager(user)
    }

    @Bean
    open fun passwordEncoder(): PasswordEncoder {
        return BCryptPasswordEncoder()
    }
}