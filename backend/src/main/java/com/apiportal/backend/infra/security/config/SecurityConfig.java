package com.apiportal.backend.infra.security.config;

import com.apiportal.backend.infra.security.JwtTokenValidator;
import com.auth0.jwk.JwkProvider;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.context.annotation.Bean;
import org.springframework.core.annotation.Order;
import org.springframework.http.HttpMethod;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.AuthenticationProvider;
import org.springframework.security.config.annotation.authentication.builders.AuthenticationManagerBuilder;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.builders.WebSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.web.access.AccessDeniedHandler;
import org.springframework.security.web.authentication.AuthenticationFailureHandler;
import org.springframework.security.web.authentication.www.BasicAuthenticationFilter;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

import java.util.Arrays;

@Order(1)
@EnableWebSecurity
@RequiredArgsConstructor
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    @Value("${spring.security.ignored}")
    private String nonSecureUrl;

    @Value("${keycloak.jwk}")
    private String jwkProviderUrl;

    @Override
    protected void configure(HttpSecurity http) throws Exception {
        http
                .sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS)
                .and()
                .csrf().disable()
                .cors().configurationSource(corsConfigurationSource())
                .and()
                .exceptionHandling()
                .accessDeniedHandler(accessDeniedHandler())
                .and()
                .addFilterBefore(
                        new AccessTokenFilter(
                                jwtTokenValidator(keycloakJwkProvider()),
                                authenticationManagerBean(),
                                authenticationFailureHandler()),
                        BasicAuthenticationFilter.class);
    }

    @Bean
    CorsConfigurationSource corsConfigurationSource() {

        final UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        CorsConfiguration config = new CorsConfiguration();
        source.registerCorsConfiguration("/**", config.applyPermitDefaultValues());
        //allow Authorization to be exposed
        config.setExposedHeaders(Arrays.asList("Authorization"));
        config.addAllowedMethod(HttpMethod.OPTIONS);
        config.addAllowedMethod(HttpMethod.PUT);

        return source;
    }

    @Override
    public void configure(WebSecurity web) {
        web.ignoring().antMatchers(nonSecureUrl);
    }

    @SuppressWarnings("EmptyMethod")
    @ConditionalOnMissingBean
    @Bean
    @Override
    public AuthenticationManager authenticationManagerBean() throws Exception {
        return super.authenticationManagerBean();
    }

    @Override
    public void configure(AuthenticationManagerBuilder auth) {
        auth.authenticationProvider(authenticationProvider());
    }

    @Bean
    public AuthenticationProvider authenticationProvider() {
        return new KeycloakAuthenticationProvider();
    }

    @Bean
    public AuthenticationFailureHandler authenticationFailureHandler() {
        return new AccessTokenAuthenticationFailureHandler();
    }

    @Bean
    public JwtTokenValidator jwtTokenValidator(JwkProvider jwkProvider) {
        return new JwtTokenValidator(jwkProvider);
    }

    @Bean
    public JwkProvider keycloakJwkProvider() {
        return new KeycloakJwkProvider(jwkProviderUrl);
    }

    @Bean
    public AccessDeniedHandler accessDeniedHandler() {
        return new AuthorizationAccessDeniedHandler();
    }
}
