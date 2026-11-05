package tests

import (
	"errors"
	"sync"
	"testing"
	"time"

	"fullstyle-backend-go/internal/services"

	"github.com/golang-jwt/jwt/v5"
	"golang.org/x/crypto/bcrypt"
	"gorm.io/gorm"
)

func TestLoginUsesAccountPolicyAndCannotIssueMFABypass(t *testing.T) {
	_, db := setupTestApp(t)
	user, err := services.RegisterUser(db, "Policy", "policy@synthetic.invalid", "Password123")
	if err != nil {
		t.Fatal(err)
	}
	policy := services.AccountSecurity{UserID: user.ID, Epoch: 7, Enabled: false}
	if err := db.Create(&policy).Error; err != nil {
		t.Fatal(err)
	}
	token, _, err := services.LoginUser(db, user.Email, "Password123")
	if err != nil {
		t.Fatal(err)
	}
	parser := jwt.NewParser()
	parsed, _, err := parser.ParseUnverified(token, jwt.MapClaims{})
	if err != nil || parsed.Claims.(jwt.MapClaims)["session_epoch"] != float64(7) {
		t.Fatal("Login ignored persisted account epoch")
	}
	if err := db.Model(&policy).Update("enabled", true).Error; err != nil {
		t.Fatal(err)
	}
	token, _, err = services.LoginUser(db, user.Email, "Password123")
	if token != "" || !errors.Is(err, services.ErrMFARequired) {
		t.Fatal("Go issued a password-only session for MFA account")
	}
	if err := db.Exec("DROP TABLE account_security").Error; err != nil {
		t.Fatal(err)
	}
	token, _, err = services.LoginUser(db, user.Email, "Password123")
	if token != "" || err == nil {
		t.Fatal("Missing account policy must fail closed")
	}
}

func TestPasswordResetBetweenHashCheckAndIssuanceCannotCreateNewEpochSession(t *testing.T) {
	_, db := setupTestApp(t)
	user, err := services.RegisterUser(db, "Race", "race@synthetic.invalid", "Password123")
	if err != nil {
		t.Fatal(err)
	}
	if err := db.Create(&services.AccountSecurity{UserID: user.ID}).Error; err != nil {
		t.Fatal(err)
	}
	reached, resume := make(chan struct{}), make(chan struct{})
	var first sync.Once
	var unblock sync.Once
	t.Cleanup(func() { unblock.Do(func() { close(resume) }) })
	hook := func(tx *gorm.DB) {
		if tx.Statement.Table == "account_security" {
			first.Do(func() { close(reached); <-resume })
		}
	}
	if err := db.Callback().Create().Before("gorm:create").Register("test:policy-race", hook); err != nil {
		t.Fatal(err)
	}
	if err := db.Callback().Query().Before("gorm:query").Register("test:policy-race", hook); err != nil {
		t.Fatal(err)
	}
	type result struct {
		access, refresh string
		err             error
	}
	done := make(chan result, 1)
	go func() {
		a, r, _, e := services.LoginUserWithTokens(db, user.Email, "Password123")
		done <- result{a, r, e}
	}()
	select {
	case <-reached:
	case <-time.After(10 * time.Second):
		t.Fatal("Login never reached SQL policy boundary")
	}
	encoded, err := bcrypt.GenerateFromPassword([]byte("Changed123"), bcrypt.DefaultCost)
	if err != nil {
		t.Fatal(err)
	}
	if err := db.Transaction(func(tx *gorm.DB) error {
		if err := tx.Exec("UPDATE userr SET password=? WHERE id=?", string(encoded), user.ID).Error; err != nil {
			return err
		}
		return tx.Exec("UPDATE account_security SET epoch=1 WHERE user_id=?", user.ID).Error
	}); err != nil {
		t.Fatal(err)
	}
	unblock.Do(func() { close(resume) })
	select {
	case value := <-done:
		if value.access != "" || value.refresh != "" || value.err == nil {
			t.Fatal("Old password issued a new-epoch session after reset")
		}
	case <-time.After(10 * time.Second):
		t.Fatal("Login did not release its policy transaction")
	}
}
