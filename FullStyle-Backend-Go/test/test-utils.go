package tests

import (
	"bytes"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"fullstyle-backend-go/internal/models"
	"fullstyle-backend-go/internal/routes"
	"fullstyle-backend-go/internal/services"
	"net/http"
	"net/http/httptest"
	"os"
	"testing"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

func setupTestApp(t *testing.T) (*gin.Engine, *gorm.DB) {
	t.Helper()
	dsn := os.Getenv("DATABASE_URL_TEST")
	if dsn == "" {
		t.Skip("Local PostgreSQL integration tests require explicit synthetic DSN")
	}
	if dsn != "postgresql://synthetic:local-synthetic-only@postgres/fullstyle_synthetic" {
		t.Fatal("Integration tests accept only the isolated synthetic database")
	}
	t.Setenv("JWT_SECRET_KEY", "synthetic-go-test-signing-secret-32characters")
	admin, err := gorm.Open(postgres.Open(dsn), &gorm.Config{})
	if err != nil {
		t.Fatal(err)
	}
	random := make([]byte, 16)
	if _, err := rand.Read(random); err != nil {
		t.Fatal(err)
	}
	schema := "go_test_" + hex.EncodeToString(random)
	if err := admin.Exec("CREATE SCHEMA " + schema).Error; err != nil {
		t.Fatal(err)
	}
	testDB, err := gorm.Open(postgres.Open(dsn+"?search_path="+schema), &gorm.Config{})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() {
		sqlDB, _ := testDB.DB()
		sqlDB.Close()
		admin.Exec("DROP SCHEMA " + schema + " CASCADE")
		sqlAdmin, _ := admin.DB()
		sqlAdmin.Close()
	})
	if err := testDB.AutoMigrate(&models.User{}, &models.Manager{}, &models.Client{}, &services.AccountSecurity{}); err != nil {
		t.Fatal(err)
	}
	router := gin.New()
	routes.AuthRoutes(router, testDB)
	return router, testDB
}

type TestCase struct {
	Name       string
	Input      map[string]string
	WantStatus int
	WantError  string
}

func RunErrorSubtests(t *testing.T, router *gin.Engine, path string, tests []TestCase) {
	for _, tt := range tests {
		t.Run(tt.Name, func(t *testing.T) {
			b, _ := json.Marshal(tt.Input)
			req, _ := http.NewRequest("POST", path, bytes.NewBuffer(b))
			req.Header.Set("Content-Type", "application/json")

			resp := httptest.NewRecorder()
			router.ServeHTTP(resp, req)

			assert.Equal(t, tt.WantStatus, resp.Code, "Expected status %d, got %d", tt.WantStatus, resp.Code)

			var body map[string]interface{}
			_ = json.Unmarshal(resp.Body.Bytes(), &body)

			msg, ok := body["error"]
			assert.True(t, ok, "Expected 'error' field in response")
			assert.Equal(t, tt.WantError, msg, "Expected error: %q, got: %v", tt.WantError, msg)
		})
	}
}
