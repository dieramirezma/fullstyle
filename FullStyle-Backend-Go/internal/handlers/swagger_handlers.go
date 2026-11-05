package handlers

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"gorm.io/gorm"
)

// AuthHandler maneja las operaciones de autenticación
type AuthHandler struct {
	DB *gorm.DB
}

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
func (h *AuthHandler) RegisterUser(c *gin.Context) {
	// Este es solo un esqueleto para la documentación
	c.JSON(http.StatusOK, gin.H{})
}

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
func (h *AuthHandler) RegisterManager(c *gin.Context) {
	// Este es solo un esqueleto para la documentación
	c.JSON(http.StatusOK, gin.H{})
}

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
func (h *AuthHandler) LoginUser(c *gin.Context) {
	// Este es solo un esqueleto para la documentación
	c.JSON(http.StatusOK, gin.H{})
}
