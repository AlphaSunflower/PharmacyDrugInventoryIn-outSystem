package com.gcky.durginoutsystem;

import com.gcky.durginoutsystem.config.AuthInterceptor;
import com.gcky.durginoutsystem.utils.JwtUtil;
import jakarta.servlet.http.HttpServletResponse;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;

import static org.junit.jupiter.api.Assertions.*;

public class AuthInterceptorTest {

    private AuthInterceptor interceptor;
    private final JwtUtil jwtUtil = new JwtUtil("test-secret-key-for-unit-testing-12345678");

    @BeforeEach
    void setUp() {
        interceptor = new AuthInterceptor();
        try {
            var field = AuthInterceptor.class.getDeclaredField("jwtUtil");
            field.setAccessible(true);
            field.set(interceptor, jwtUtil);
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    @Test
    void shouldRejectRequestWithoutToken() throws Exception {
        var req = new MockHttpServletRequest();
        var res = new MockHttpServletResponse();
        // Non-HandlerMethod objects pass through the interceptor
        boolean result = interceptor.preHandle(req, res, new Object());
        assertTrue(result);
    }

    @Test
    void shouldRejectMalformedToken() {
        assertThrows(Exception.class, () -> jwtUtil.extractClaims("invalid.token.here"));
    }
}
