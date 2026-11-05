package routes

import (
	"errors"
	"net/http"

	"fullstyle-backend-go/internal/models"
	"fullstyle-backend-go/internal/services"

	"github.com/gin-gonic/gin"

	"gorm.io/gorm"
)

func AuthRoutes(r *gin.Engine, db *gorm.DB) {
	// RegisterUser godoc
	// @Summary Registrar un nuevo usuario
	// @Description Registra un nuevo usuario en el sistema
	// @Tags Autenticación
	// @Accept json
	// @Produce json
	// @Param user body models.RegisterUserRequest true "Información del usuario"
	// @Success 200 {object} models.RegisterUserResponse
	// @Failure 400 {object} models.ErrorResponse
	// @Router /api/register [post]
	r.POST("/api/register", func(c *gin.Context) {
		var req struct {
			Name     string `json:"name"`
			Email    string `json:"email"`
			Password string `json:"password"`
		}

		if err := c.ShouldBindJSON(&req); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request"})
			return
		}

		user, accessToken, refreshToken, err := services.RegisterUserWithTokens(db, req.Name, req.Email, req.Password)
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}

		c.JSON(http.StatusOK, gin.H{
			"message": "User registered successfully",
			"user": gin.H{
				"id":            user.ID,
				"email":         user.Email,
				"name":          user.Name,
				"active":        user.Active,
				"auth_provider": user.AuthProvider,
				"google_id":     user.GoogleID,
			},
			"access_token":  accessToken,
			"refresh_token": refreshToken,
		})
	})

	// RegisterManager godoc
	// @Summary Registrar un nuevo manager
	// @Description Registra un nuevo manager en el sistema
	// @Tags Autenticación
	// @Accept json
	// @Produce json
	// @Param manager body models.RegisterManagerRequest true "Información del manager"
	// @Success 200 {object} models.RegisterUserResponse
	// @Failure 400 {object} models.ErrorResponse
	// @Router /api/manager_register [post]
	r.POST("/api/manager_register", func(c *gin.Context) {
		var req struct {
			Name                   string `json:"name"`
			Email                  string `json:"email"`
			Password               string `json:"password"`
			Bankaccount            int    `json:"bankaccount"`
			Accounttype            string `json:"accounttype"`
			Bankentity             string `json:"bankentity"`
			Subscriptionactive     bool   `json:"subscriptionactive"`
			Subscriptiontype       string `json:"subscriptiontype"`
			Subscriptionstartdate  string `json:"subscriptionstartdate"`
			Subscriptionfinishdate string `json:"subscriptionfinishdate"`
		}

		if err := c.ShouldBindJSON(&req); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request"})
			return
		}

		var user *models.User
		var manager *models.Manager

		err := db.Transaction(func(tx *gorm.DB) error {
			// Registrar el usuario
			newUser, err := services.RegisterUser(tx, req.Name, req.Email, req.Password)
			if err != nil {
				return err // aborta transacción
			}
			user = newUser

			// Registrar el manager
			newManager, err := services.RegisterManager(tx, user.ID, req.Bankaccount, req.Accounttype, req.Bankentity, req.Subscriptionactive, req.Subscriptiontype, req.Subscriptionstartdate, req.Subscriptionfinishdate)
			if err != nil {
				return err // aborta transacción
			}
			manager = newManager

			return nil // commit
		})

		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}

		c.JSON(http.StatusOK, gin.H{
			"message": "Manager registered successfully",
			"user": gin.H{
				"id":     manager.ID,
				"name":   user.Name,
				"active": user.Active,
				"email":  user.Email,
			},
		})
	})

	// LoginUser godoc
	// @Summary Iniciar sesión
	// @Description Autentica un usuario y retorna un token JWT
	// @Tags Autenticación
	// @Accept json
	// @Produce json
	// @Param credentials body models.LoginRequest true "Credenciales de acceso"
	// @Success 200 {object} models.LoginResponse
	// @Failure 401 {object} models.ErrorResponse
	// @Router /api/login [post]
	r.POST("/api/login", func(c *gin.Context) {
		var req struct {
			Email    string `json:"email"`
			Password string `json:"password"`
			OTP      string `json:"otp"`
		}

		if err := c.ShouldBindJSON(&req); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request"})
			return
		}

		token, refreshToken, user, err := services.LoginUserWithTokens(db, req.Email, req.Password)
		if errors.Is(err, services.ErrMFARequired) {
			mfaLogin(c, req.Email, req.Password, req.OTP)
			return
		}
		if err != nil {
			c.JSON(http.StatusUnauthorized, gin.H{"error": err.Error()})
			return
		}

		c.JSON(http.StatusOK, gin.H{
			"refresh_token": refreshToken,
			"message":       "Login successful",
			"token":         token,
			"user": gin.H{
				"id":     user.ID,
				"name":   user.Name,
				"active": user.Active,
				"email":  user.Email,
			},
		})
	})
}
