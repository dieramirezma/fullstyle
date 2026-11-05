package services

import (
	"errors"
	"fmt"
	"time"

	"fullstyle-backend-go/internal/models"

	"gorm.io/gorm"
)

func RegisterManager(db *gorm.DB, id uint, bankaccount int, accounttype, bankentity string, subscriptionactive bool, subscriptiontype, subscriptionstartdate, subscriptionfinishdate string) (*models.Manager, error) {

	//Validations:
	// Check if the user exists
	var user models.User
	if err := db.First(&user, id).Error; err != nil {
		return nil, fmt.Errorf("user with ID %d not found", id)
	}
	// Check if the bank account number is valid
	if bankaccount <= 0 {
		return nil, errors.New("invalid bank account number")
	}
	// Check if the account type is valid
	if accounttype == "" || bankentity == "" {
		return nil, errors.New("account type and bank entity are required")
	}

	// Dates validations
	//Start date must be in ISO 8601 format
	startDate, err := time.Parse(time.RFC3339, subscriptionstartdate)
	if err != nil {
		return nil, errors.New("invalid subscription start date format (use ISO 8601)")
	}
	//End date must be in ISO 8601 format
	endDate, err := time.Parse(time.RFC3339, subscriptionfinishdate)
	if err != nil {
		return nil, errors.New("invalid subscription finish date format (use ISO 8601)")
	}
	// Check if the end date is after the start date
	if endDate.Before(startDate) {
		return nil, errors.New("subscription end date must be after start date")
	}

	manager := &models.Manager{
		ID:                     id,
		Bankaccount:            bankaccount,
		Accounttype:            accounttype,
		Bankentity:             bankentity,
		Subscriptionactive:     false, // Legacy inputs never grant a paid entitlement.
		Subscriptiontype:       "",
		Subscriptionstartdate:  time.Time{},
		Subscriptionfinishdate: time.Time{},
	}

	if err := db.Create(manager).Error; err != nil {
		return nil, err
	}

	return manager, nil
}
