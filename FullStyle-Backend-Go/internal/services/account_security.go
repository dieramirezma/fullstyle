package services

import (
	"errors"
)

var ErrMFARequired = errors.New("MFA requires the shared password and OTP verifier")

type AccountSecurity struct {
	UserID  uint `gorm:"primaryKey"`
	Epoch   int
	Enabled bool
}

func (AccountSecurity) TableName() string { return "account_security" }
