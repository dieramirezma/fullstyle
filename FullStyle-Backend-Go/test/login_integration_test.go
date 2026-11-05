package tests

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestLoginSuccess(t *testing.T) {
	router, _ := setupTestApp(t)

	regPayload := map[string]string{
		"name":     "Carlos",
		"email":    "carlos@test.com",
		"password": "secure1234",
	}
	regBody, _ := json.Marshal(regPayload)
	req, _ := http.NewRequest("POST", "/api/register", bytes.NewBuffer(regBody))
	req.Header.Set("Content-Type", "application/json")
	resp := httptest.NewRecorder()
	router.ServeHTTP(resp, req)
	assert.Equal(t, http.StatusOK, resp.Code)

	loginPayload := map[string]string{
		"email":    "carlos@test.com",
		"password": "secure1234",
	}
	body, _ := json.Marshal(loginPayload)
	req, _ = http.NewRequest("POST", "/api/login", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	resp = httptest.NewRecorder()
	router.ServeHTTP(resp, req)

	assert.Equal(t, http.StatusOK, resp.Code)

	var result map[string]interface{}
	err := json.Unmarshal(resp.Body.Bytes(), &result)
	assert.NoError(t, err)

	assert.Equal(t, "Login successful", result["message"], "Expected success message, got: %v", result["message"])
	assert.NotEmpty(t, result["token"], "Token should not be empty")

	user, ok := result["user"].(map[string]interface{})
	assert.True(t, ok, "User field must be present and a map")

	assert.Equal(t, "Carlos", user["name"], "Expected user name to be 'Carlos', got: %v", user["name"])
	assert.Equal(t, "carlos@test.com", user["email"], "Expected user email to be 'carlos@test.com', got: %v", user["email"])
	assert.NotEmpty(t, user["id"], "User ID should not be empty")
}

func TestLoginFailures(t *testing.T) {
	router, _ := setupTestApp(t)

	validUser := map[string]string{
		"name":     "Lucia",
		"email":    "lucia@test.com",
		"password": "mypassword",
	}
	body, _ := json.Marshal(validUser)
	req, _ := http.NewRequest("POST", "/api/register", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	resp := httptest.NewRecorder()
	router.ServeHTTP(resp, req)

	tests := []struct {
		name       string
		input      map[string]string
		wantStatus int
		wantError  string
	}{
		{
			name: "No email provided ",
			input: map[string]string{
				"email":    "",
				"password": "mypassword",
			},
			wantStatus: http.StatusUnauthorized,
			wantError:  "email is required",
		},
		{
			name: "No password provided",
			input: map[string]string{
				"email":    "lucia@test.com",
				"password": "",
			},
			wantStatus: http.StatusUnauthorized,
			wantError:  "password is required",
		},
		{
			name: "Email does not exist",
			input: map[string]string{
				"email":    "no@existe.com",
				"password": "mypassword",
			},
			wantStatus: http.StatusUnauthorized,
			wantError:  "email not found",
		},
		{
			name: "Incorrect password",
			input: map[string]string{
				"email":    "lucia@test.com",
				"password": "wrongpass",
			},
			wantStatus: http.StatusUnauthorized,
			wantError:  "invalid password",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			b, _ := json.Marshal(tt.input)
			req, _ := http.NewRequest("POST", "/api/login", bytes.NewBuffer(b))
			req.Header.Set("Content-Type", "application/json")

			resp := httptest.NewRecorder()
			router.ServeHTTP(resp, req)

			assert.Equal(t, tt.wantStatus, resp.Code, "Expected status %d, got %d", tt.wantStatus, resp.Code)

			var body map[string]interface{}
			_ = json.Unmarshal(resp.Body.Bytes(), &body)
			msg, ok := body["error"]
			assert.True(t, ok, "Expected 'error' field to be present in response")
			assert.Equal(t, tt.wantError, msg, "Expected error: %q, got: %v", tt.wantError, msg)

		})
	}
}
