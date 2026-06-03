package com.gcky.durginoutsystem;

import com.gcky.durginoutsystem.utils.JwtUtil;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.ExpiredJwtException;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

public class JwtUtilTest {

    private static final String SECRET = "test-secret-key-for-unit-testing-12345678";
    private final JwtUtil jwtUtil = new JwtUtil(SECRET);

    @Test
    void shouldGenerateAndExtractToken() {
        String token = jwtUtil.generateToken("testuser", "DOCTOR", 1L);
        assertNotNull(token);

        Claims claims = jwtUtil.extractClaims(token);
        assertEquals("testuser", claims.getSubject());
        assertEquals("DOCTOR", claims.get("role"));
        assertEquals(1L, claims.get("userId", Long.class));
    }

    @Test
    void shouldValidateTokenCorrectly() {
        String token = jwtUtil.generateToken("testuser", "DOCTOR", 1L);
        assertTrue(jwtUtil.validateToken(token, "testuser"));
    }

    @Test
    void shouldRejectTokenWithWrongUsername() {
        String token = jwtUtil.generateToken("testuser", "DOCTOR", 1L);
        assertFalse(jwtUtil.validateToken(token, "otheruser"));
    }

    @Test
    void shouldRejectTokenWithBlankSecret() {
        assertThrows(IllegalStateException.class, () -> new JwtUtil(""));
    }

    @Test
    void shouldRejectTokenWithNullSecret() {
        assertThrows(IllegalStateException.class, () -> new JwtUtil(null));
    }
}