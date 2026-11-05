package tests

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"fullstyle-backend-go/internal/models"

	"github.com/stretchr/testify/assert"
)

func TestRegisterManagerSuccess(t *testing.T) {
	router, database := setupTestApp(t)

	payload := map[string]interface{}{
		"name":                   "Juan",
		"email":                  "juan.manager@test.com",
		"password":               "12345678",
		"bankaccount":            123456,
		"accounttype":            "corriente",
		"bankentity":             "NeonBank",
		"subscriptionactive":     true,
		"subscriptiontype":       "Premium",
		"subscriptionstartdate":  "2025-06-20T00:00:00Z",
		"subscriptionfinishdate": "2025-12-31T00:00:00Z",
	}

	body, _ := json.Marshal(payload)
	req, _ := http.NewRequest("POST", "/api/manager_register", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	resp := httptest.NewRecorder()

	router.ServeHTTP(resp, req)

	assert.Equal(t, http.StatusOK, resp.Code, "Expected status 200 OK, got %d", resp.Code)

	var response map[string]interface{}
	if err := json.Unmarshal(resp.Body.Bytes(), &response); err != nil {
		t.Fatalf("Error parsing JSON response: %v", err)
	}

	assert.Equal(t, "Manager registered successfully", response["message"], "Expected success message, got: %v", response["message"])

	user, ok := response["user"].(map[string]interface{})
	assert.True(t, ok, "Expected 'user' field to be present on the response")

	assert.Equal(t, "Juan", user["name"], "Expected user name to be 'Juan', got: %v", user["name"])

	assert.Equal(t, "juan.manager@test.com", user["email"], "Expected email to be 'juan.manager@test.com', got: %v", user["email"])

	assert.NotEmpty(t, user["id"], "User ID should not be empty")
	var persisted models.Manager
	assert.NoError(t, database.First(&persisted, uint(user["id"].(float64))).Error)
	assert.False(t, persisted.Subscriptionactive, "client registration must not grant a subscription")
	assert.Empty(t, persisted.Subscriptiontype)
	assert.True(t, persisted.Subscriptionstartdate.IsZero())
	assert.True(t, persisted.Subscriptionfinishdate.IsZero())

}

func TestRegisterManagerFailures(t *testing.T) {
	router, _ := setupTestApp(t)

	initialPayload := map[string]interface{}{
		"name":                   "Repetido",
		"email":                  "duplicate@test.com",
		"password":               "12345678",
		"bankaccount":            10001,
		"accounttype":            "ahorros",
		"bankentity":             "BancoA",
		"subscriptionactive":     true,
		"subscriptiontype":       "Basic",
		"subscriptionstartdate":  "2025-06-20T00:00:00Z",
		"subscriptionfinishdate": "2025-12-20T00:00:00Z",
	}
	body, _ := json.Marshal(initialPayload)
	req, _ := http.NewRequest("POST", "/api/manager_register", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	resp := httptest.NewRecorder()
	router.ServeHTTP(resp, req)
	if resp.Code != http.StatusOK {
		t.Fatalf("Setup failed: could not create initial user for duplicate email test")
	}

	tests := []struct {
		name       string
		input      map[string]interface{}
		wantStatus int
		wantError  string
	}{
		{
			name: "Invalid bank account number",
			input: map[string]interface{}{
				"name":                   "Test",
				"email":                  "badbank@test.com",
				"password":               "12345678",
				"bankaccount":            0,
				"accounttype":            "ahorros",
				"bankentity":             "BancoX",
				"subscriptionactive":     true,
				"subscriptiontype":       "Premium",
				"subscriptionstartdate":  "2025-06-20T00:00:00Z",
				"subscriptionfinishdate": "2025-12-20T00:00:00Z",
			},
			wantStatus: http.StatusBadRequest,
			wantError:  "invalid bank account number",
		},
		{
			name: "Missing account type and bank entity",
			input: map[string]interface{}{
				"name":                   "Test2",
				"email":                  "missing@test.com",
				"password":               "12345678",
				"bankaccount":            12345,
				"accounttype":            "",
				"bankentity":             "",
				"subscriptionactive":     true,
				"subscriptiontype":       "Premium",
				"subscriptionstartdate":  "2025-06-20T00:00:00Z",
				"subscriptionfinishdate": "2025-12-20T00:00:00Z",
			},
			wantStatus: http.StatusBadRequest,
			wantError:  "account type and bank entity are required",
		},
		{
			name: "Malformed start date",
			input: map[string]interface{}{
				"name":                   "Test3",
				"email":                  "badstart@test.com",
				"password":               "12345678",
				"bankaccount":            12345,
				"accounttype":            "ahorros",
				"bankentity":             "BancoZ",
				"subscriptionactive":     true,
				"subscriptiontype":       "Premium",
				"subscriptionstartdate":  "not-a-date",
				"subscriptionfinishdate": "2025-12-20T00:00:00Z",
			},
			wantStatus: http.StatusBadRequest,
			wantError:  "invalid subscription start date format (use ISO 8601)",
		},
		{
			name: "End date before start date",
			input: map[string]interface{}{
				"name":                   "Test4",
				"email":                  "badrange@test.com",
				"password":               "12345678",
				"bankaccount":            12345,
				"accounttype":            "ahorros",
				"bankentity":             "BancoY",
				"subscriptionactive":     true,
				"subscriptiontype":       "Premium",
				"subscriptionstartdate":  "2025-12-20T00:00:00Z",
				"subscriptionfinishdate": "2025-06-20T00:00:00Z",
			},
			wantStatus: http.StatusBadRequest,
			wantError:  "subscription end date must be after start date",
		},
		{
			name: "Email already used",
			input: map[string]interface{}{
				"name":                   "Test5",
				"email":                  "duplicate@test.com",
				"password":               "12345678",
				"bankaccount":            99999,
				"accounttype":            "corriente",
				"bankentity":             "Neon",
				"subscriptionactive":     false,
				"subscriptiontype":       "Basic",
				"subscriptionstartdate":  "2025-06-20T00:00:00Z",
				"subscriptionfinishdate": "2025-12-20T00:00:00Z",
			},
			wantStatus: http.StatusBadRequest,
			wantError:  "user already exists",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			b, _ := json.Marshal(tt.input)
			req, _ := http.NewRequest("POST", "/api/manager_register", bytes.NewBuffer(b))
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
