package services

import (
	"crypto/sha256"
	"crypto/sha512"
	"crypto/subtle"
	"encoding/hex"
	"hash"
	"strconv"
	"strings"

	"golang.org/x/crypto/bcrypt"
	"golang.org/x/crypto/pbkdf2"
	"golang.org/x/crypto/scrypt"
)

// Verify legacy Werkzeug and Go hashes without rewriting stored passwords.
func validPassword(encoded, password string) bool {
	if strings.HasPrefix(encoded, "$2") {
		return bcrypt.CompareHashAndPassword([]byte(encoded), []byte(password)) == nil
	}
	parts := strings.Split(encoded, "$")
	if len(parts) != 3 {
		return false
	}
	method := strings.Split(parts[0], ":")
	want, err := hex.DecodeString(parts[2])
	if err != nil {
		return false
	}
	var actual []byte
	switch method[0] {
	case "pbkdf2":
		if len(method) != 3 {
			return false
		}
		iterations, e := strconv.Atoi(method[2])
		if e != nil || iterations < 1 || iterations > 10000000 {
			return false
		}
		var digest func() hash.Hash
		switch method[1] {
		case "sha256":
			digest = sha256.New
		case "sha512":
			digest = sha512.New
		default:
			return false
		}
		actual = pbkdf2.Key([]byte(password), []byte(parts[1]), iterations, digest().Size(), digest)
	case "scrypt":
		if len(method) != 4 {
			return false
		}
		n, e1 := strconv.Atoi(method[1])
		r, e2 := strconv.Atoi(method[2])
		p, e3 := strconv.Atoi(method[3])
		if e1 != nil || e2 != nil || e3 != nil || n < 2 || n > 65536 || r < 1 || r > 16 || p < 1 || p > 4 {
			return false
		}
		actual, err = scrypt.Key([]byte(password), []byte(parts[1]), n, r, p, 64)
		if err != nil {
			return false
		}
	default:
		return false
	}
	return subtle.ConstantTimeCompare(actual, want) == 1
}
