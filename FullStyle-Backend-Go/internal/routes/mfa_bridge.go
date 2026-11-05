package routes

import (
	"bytes"
	"encoding/json"
	"io"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
)

// Only the SQL password verifier handles MFA issuance. No mutation retry or redirects.
func mfaLogin(c *gin.Context, email, password, otp string) {
	body, err := json.Marshal(map[string]string{"email": email, "password": password, "otp": otp})
	if err != nil {
		c.JSON(400, gin.H{"error": "Invalid credentials"})
		return
	}
	req, err := http.NewRequestWithContext(c.Request.Context(), "POST", "http://backend:5000/api/login", bytes.NewReader(body))
	if err != nil {
		c.JSON(503, gin.H{"error": "Session unavailable"})
		return
	}
	req.Header.Set("Content-Type", "application/json")
	client := &http.Client{Timeout: 6 * time.Second, CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }}
	response, err := client.Do(req)
	if err != nil {
		c.JSON(503, gin.H{"error": "Session unavailable"})
		return
	}
	defer response.Body.Close()
	var result map[string]interface{}
	if json.NewDecoder(io.LimitReader(response.Body, 65536)).Decode(&result) != nil {
		c.JSON(503, gin.H{"error": "Session unavailable"})
		return
	}
	if response.StatusCode != 200 {
		c.JSON(response.StatusCode, gin.H{"error": "MFA required or invalid OTP", "mfa_required": true})
		return
	}
	result["token"] = result["access_token"]
	c.JSON(200, result)
}
