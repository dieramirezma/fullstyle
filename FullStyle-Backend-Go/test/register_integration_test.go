package tests

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestRegisterUserSuccess(t *testing.T) {
	router, _ := setupTestApp(t)

	input := map[string]string{
		"name":     "dbtest02",
		"email":    "dbtest02@gmail.com",
		"password": "12345678",
	}
	body, _ := json.Marshal(input)

	req, _ := http.NewRequest("POST", "/api/register", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	resp := httptest.NewRecorder()

	router.ServeHTTP(resp, req)

	if resp.Code != http.StatusOK {
		t.Fatalf("Expected 200 OK, got %d", resp.Code)
	}

	var response map[string]interface{}
	err := json.Unmarshal(resp.Body.Bytes(), &response)
	if err != nil {
		t.Fatalf("Error parsing response JSON: %v", err)
	}

	assert.Equal(t, "User registered successfully", response["message"], "Expected success message, got: %v", response["message"])

	user, ok := response["user"].(map[string]interface{})
	assert.True(t, ok, "Expected 'user' field to be present on the response")
	assert.Equal(t, input["name"], user["name"], "Expected name to be '%s', got '%v'", input["name"], user["name"])

	assert.Equal(t, input["email"], user["email"], "Expected email to be '%s', got '%v'", input["email"], user["email"])

	assert.NotEmpty(t, user["id"], "User ID should not be empty")
}

func TestRegisterUserFailures(t *testing.T) {
	router, _ := setupTestApp(t)

	payload := map[string]string{
		"name":     "Juan",
		"email":    "juan@test.com",
		"password": "12345678",
	}
	body, _ := json.Marshal(payload)

	req, _ := http.NewRequest("POST", "/api/register", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	resp := httptest.NewRecorder()
	router.ServeHTTP(resp, req)

	if resp.Code != http.StatusOK {
		t.Fatalf("Error en setup: usuario válido no se registró correctamente")
	}

	tests := []struct {
		name       string
		input      map[string]string
		wantStatus int
		wantError  string
	}{
		{
			name: "No name provided",
			input: map[string]string{
				"name":     "",
				"email":    "test1@test.com",
				"password": "12345678",
			},
			wantStatus: http.StatusBadRequest,
			wantError:  "name is required",
		},
		{
			name: "Invalid email",
			input: map[string]string{
				"name":     "Carlos",
				"email":    "no-es-email",
				"password": "12345678",
			},
			wantStatus: http.StatusBadRequest,
			wantError:  "invalid email format",
		},
		{
			name: "Short password",
			input: map[string]string{
				"name":     "Laura",
				"email":    "laura@test.com",
				"password": "1234",
			},
			wantStatus: http.StatusBadRequest,
			wantError:  "password must be at least 8 characters",
		},
		{
			name: "Email already registered",
			input: map[string]string{
				"name":     "Repetido",
				"email":    "juan@test.com",
				"password": "12345678",
			},
			wantStatus: http.StatusBadRequest,
			wantError:  "user already exists",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			b, _ := json.Marshal(tt.input)
			req, _ := http.NewRequest("POST", "/api/register", bytes.NewBuffer(b))
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
