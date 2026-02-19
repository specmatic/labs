package com.store.config

import com.store.security.DummySecurityFilter
import org.springframework.context.annotation.Configuration
import org.springframework.context.annotation.Profile
import org.springframework.security.config.annotation.web.builders.HttpSecurity
import org.springframework.security.config.annotation.web.configurers.ExpressionUrlAuthorizationConfigurer
import org.springframework.security.web.authentication.preauth.AbstractPreAuthenticatedProcessingFilter

@Configuration
@Profile("test")
open class DummySecurityConfig: SecurityConfig() {
    override fun configureFilterChain(http: HttpSecurity) {
        http.addFilterBefore(DummySecurityFilter(), AbstractPreAuthenticatedProcessingFilter::class.java)
        http.csrf().disable()
    }

    override fun verifyAuthority(authorizedUrl: ExpressionUrlAuthorizationConfigurer<HttpSecurity>.AuthorizedUrl) {
        authorizedUrl.permitAll()
    }
}