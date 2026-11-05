package models

// RegisterUserRequest representa la solicitud para registrar un nuevo usuario
type RegisterUserRequest struct {
	Name     string `json:"name" example:"John Doe"`
	Email    string `json:"email" example:"john.doe@example.com"`
	Password string `json:"password" example:"securePassword123"`
}

// LoginRequest representa la solicitud para iniciar sesión
type LoginRequest struct {
	Email    string `json:"email" example:"john.doe@example.com"`
	Password string `json:"password" example:"securePassword123"`
}

// RegisterManagerRequest representa la solicitud para registrar un nuevo manager
type RegisterManagerRequest struct {
	Name                   string `json:"name" example:"Jane Smith"`
	Email                  string `json:"email" example:"jane.smith@example.com"`
	Password               string `json:"password" example:"securePassword123"`
	Bankaccount            int    `json:"bankaccount" example:"123456789"`
	Accounttype            string `json:"accounttype" example:"Checking"`
	Bankentity             string `json:"bankentity" example:"BankName"`
	Subscriptionactive     bool   `json:"subscriptionactive" example:"true"`
	Subscriptiontype       string `json:"subscriptiontype" example:"Premium"`
	Subscriptionstartdate  string `json:"subscriptionstartdate" example:"2025-06-03"`
	Subscriptionfinishdate string `json:"subscriptionfinishdate" example:"2026-06-03"`
}

// UserResponse representa la respuesta con información básica del usuario
type UserResponse struct {
	ID    uint   `json:"id" example:"1"`
	Name  string `json:"name" example:"John Doe"`
	Email string `json:"email" example:"john.doe@example.com"`
}

// RegisterUserResponse representa la respuesta al registrar un usuario
type RegisterUserResponse struct {
	Message string       `json:"message" example:"User registered successfully"`
	User    UserResponse `json:"user"`
}

// LoginResponse representa la respuesta al iniciar sesión
type LoginResponse struct {
	Message string       `json:"message" example:"Login successful"`
	Token   string       `json:"token" example:"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."`
	User    UserResponse `json:"user"`
}

// ErrorResponse representa una respuesta de error
type ErrorResponse struct {
	Error string `json:"error" example:"Invalid credentials"`
}
