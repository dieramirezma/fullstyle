package services

import (
	"crypto/rand"
	"encoding/hex"
	"errors"
	"os"
	"strconv"
	"strings"
	"time"

	"fullstyle-backend-go/internal/models"
	"fullstyle-backend-go/internal/utils"

	"github.com/golang-jwt/jwt/v5"

	"golang.org/x/crypto/bcrypt"
	"gorm.io/gorm"
	"gorm.io/gorm/clause"
)

func RegisterUser(db *gorm.DB, name, email, password string) (*models.User, error) {
	email = strings.ToLower(email)

	// Check if the account type is valid
	if name == "" {
		return nil, errors.New("name is required")
	}
	// Email format validation
	if !utils.IsValidEmail(email) {
		return nil, errors.New("invalid email format")
	}
	// Password length validation
	if len(password) < 8 {
		return nil, errors.New("password must be at least 8 characters")
	}

	// Existent user validation
	var existing models.User
	if err := db.Where("email = ?", email).First(&existing).Error; err == nil {
		return nil, errors.New("user already exists")
	}

	// Encriptar la contraseña
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	if err != nil {
		return nil, err
	}

	user := &models.User{
		Name:         name,
		Email:        email,
		Password:     string(hashedPassword),
		Active:       true,
		AuthProvider: "credentials",
		GoogleID:     nil,
	}

	if err := db.Create(user).Error; err != nil {
		return nil, err
	}

	return user, nil
}

func LoginUser(db *gorm.DB, email, password string) (string, *models.User, error) {
	access, _, user, err := LoginUserWithTokens(db, email, password)
	return access, user, err
}

func LoginUserWithTokens(db *gorm.DB, email, password string) (string, string, *models.User, error) {
	var user models.User
	email = strings.ToLower(email)

	if email == "" {
		return "", "", nil, errors.New("email is required")
	}

	if password == "" {
		return "", "", nil, errors.New("password is required")
	}

	// Search for the user by email
	if err := db.Where("email = ?", email).First(&user).Error; err != nil {
		return "", "", nil, errors.New("email not found")
	}

	// Password validation
	if !user.Active || !validPassword(user.Password, password) {
		return "", "", nil, errors.New("invalid password")
	}

	var accessToken, refreshToken string
	err := db.Transaction(func(tx *gorm.DB) error {
		policy := AccountSecurity{UserID: user.ID}
		if err := tx.Clauses(clause.OnConflict{DoNothing: true}).Create(&policy).Error; err != nil {
			return errors.New("session policy unavailable")
		}
		if err := tx.Clauses(clause.Locking{Strength: "UPDATE"}).Where("user_id = ?", user.ID).Take(&policy).Error; err != nil {
			return errors.New("session policy unavailable")
		}
		// Password reset/deletion may have committed after the initial hash check.
		if err := tx.First(&user, user.ID).Error; err != nil || !user.Active || !validPassword(user.Password, password) {
			return errors.New("invalid password")
		}
		if policy.Enabled {
			return ErrMFARequired
		}
		var err error
		accessToken, refreshToken, err = GenerateTokensWithEpoch(user.ID, policy.Epoch)
		return err
	})
	if err != nil {
		return "", "", nil, err
	}
	return accessToken, refreshToken, &user, nil
}

// generateTokens genera tokens de acceso y refresh para un usuario
func GenerateTokens(userID uint) (string, string, error) {
	return GenerateTokensWithEpoch(userID, 0)
}

func GenerateTokensWithEpoch(userID uint, epoch int) (string, string, error) {
	secret := os.Getenv("JWT_SECRET_KEY")
	if secret == "" {
		return "", "", errors.New("missing JWT secret")
	}

	// Access token (1 hora)
	family := randomTokenID()
	accessToken := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
		"session_family": family,
		"sub":            strconv.Itoa(int(userID)),
		"session_epoch":  epoch,
		"exp":            time.Now().Add(time.Hour * 1).Unix(),
		"type":           "access",
		"csrf":           randomTokenID(),
		"fresh":          false,
		"iat":            time.Now().Unix(),
		"jti":            randomTokenID(),
		"nbf":            time.Now().Unix(),
	})

	accessTokenString, err := accessToken.SignedString([]byte(secret))
	if err != nil {
		return "", "", errors.New("could not generate access token")
	}

	// Refresh lifetime matches the Flask issuer.
	refreshToken := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
		"session_family": family,
		"sub":            strconv.Itoa(int(userID)),
		"session_epoch":  epoch,
		"exp":            time.Now().Add(time.Hour * 24 * 15).Unix(),
		"type":           "refresh",
		"csrf":           randomTokenID(),
		"fresh":          false,
		"iat":            time.Now().Unix(),
		"jti":            randomTokenID(),
		"nbf":            time.Now().Unix(),
	})

	refreshTokenString, err := refreshToken.SignedString([]byte(secret))
	if err != nil {
		return "", "", errors.New("could not generate refresh token")
	}

	return accessTokenString, refreshTokenString, nil
}

// RegisterUserWithTokens registra un usuario y devuelve los tokens
func RegisterUserWithTokens(db *gorm.DB, name, email, password string) (*models.User, string, string, error) {
	// Begin transaction
	tx := db.Begin()
	if tx.Error != nil {
		return nil, "", "", tx.Error
	}

	// Create user
	user, err := RegisterUser(tx, name, email, password)
	if err != nil {
		tx.Rollback()
		return nil, "", "", err
	}

	// Create client entry
	client := models.Client{
		ID:       user.ID,
		Calendar: nil,
	}

	if err := tx.Create(&client).Error; err != nil {
		tx.Rollback()
		return nil, "", "", err
	}

	// Commit transaction
	if err := tx.Commit().Error; err != nil {
		return nil, "", "", err
	}

	accessToken, refreshToken, err := GenerateTokens(user.ID)
	if err != nil {
		return nil, "", "", err
	}

	return user, accessToken, refreshToken, nil
}

func randomTokenID() string {
	b := make([]byte, 32)
	if _, err := rand.Read(b); err != nil {
		panic("secure random unavailable")
	}
	return hex.EncodeToString(b)
}
