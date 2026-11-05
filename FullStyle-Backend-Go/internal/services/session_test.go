package services

import (
	"github.com/golang-jwt/jwt/v5"
	"testing"
)

func TestSessionsAreIndependentlyRevocable(t *testing.T) {
	t.Setenv("JWT_SECRET_KEY", "synthetic-test-secret-with-thirty-two-characters")
	a, r, err := GenerateTokens(17)
	if err != nil {
		t.Fatal(err)
	}
	b, _, err := GenerateTokens(17)
	if err != nil {
		t.Fatal(err)
	}
	ids := map[string]bool{}
	for _, sample := range []struct{ raw, kind string }{{a, "access"}, {b, "access"}, {r, "refresh"}} {
		parsed, e := jwt.Parse(sample.raw, func(*jwt.Token) (interface{}, error) {
			return []byte("synthetic-test-secret-with-thirty-two-characters"), nil
		}, jwt.WithValidMethods([]string{"HS256"}), jwt.WithExpirationRequired())
		if e != nil || !parsed.Valid {
			t.Fatalf("Invalid session: %v", e)
		}
		claims := parsed.Claims.(jwt.MapClaims)
		if claims["sub"] != "17" || claims["type"] != sample.kind {
			t.Fatal("Identity or token purpose changed")
		}
		id := claims["jti"].(string)
		if len(id) < 32 || ids[id] {
			t.Fatal("Two sessions share a revocation identifier")
		}
		ids[id] = true
	}
}

func TestMalformedHashesAndWrongPasswordsAreRejected(t *testing.T) {
	for _, encoded := range []string{"", "plaintext", "pbkdf2:sha256:-1$s$ab", "scrypt:999999999:8:1$s$ab", "$2b$invalid"} {
		if validPassword(encoded, "anything") {
			t.Fatalf("Accepted malformed password hash %q", encoded)
		}
	}
}
