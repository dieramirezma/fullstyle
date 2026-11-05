package main

import (
	"fmt"
	"log"
	"net/http"
	"os"
	"strconv"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/joho/godotenv"
	swaggerFiles "github.com/swaggo/files"
	ginSwagger "github.com/swaggo/gin-swagger"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"

	_ "fullstyle-backend-go/docs"
	"fullstyle-backend-go/internal/routes"
)

// @title FullStyle Backend API
// @version 1.0
// @description API de autenticación para la aplicación FullStyle
// @host localhost:5000
// @BasePath /
// @schemes http https
func main() {
	if len(os.Args) == 2 && os.Args[1] == "--healthcheck" {
		client := http.Client{Timeout: 3 * time.Second}
		response, err := client.Get("http://127.0.0.1:5001/ready")
		if err != nil {
			os.Exit(1)
		}
		defer response.Body.Close()
		if response.StatusCode != 200 {
			os.Exit(1)
		}
		return
	}

	// Cargar variables del .env
	_ = godotenv.Load()

	dsn := os.Getenv("DATABASE_URL")

	if dsn == "" {
		log.Fatal("DATABASE_URL is required")
	}
	// Conectar a PostgreSQL
	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{})
	if err != nil {
		log.Fatal("Error conectando a la base de datos:", err)
	}
	fmt.Println("✅ Conexión exitosa a PostgreSQL")

	// Iniciar servidor
	r := gin.Default()
	r.Use(func(c *gin.Context) {
		for _, h := range []string{"X-Correlation-ID", "X-Operation-ID"} {
			id := c.GetHeader(h)
			if len(id) < 1 || len(id) > 80 {
				id = strconv.FormatInt(time.Now().UnixNano(), 36)
			}
			c.Header(h, id)
		}
		c.Next()
	})
	r.GET("/health", func(c *gin.Context) { c.JSON(200, gin.H{"status": "ok"}) })
	r.GET("/ready", func(c *gin.Context) {
		sqlDB, e := db.DB()
		if e != nil || sqlDB.Ping() != nil {
			c.JSON(503, gin.H{"status": "unavailable"})
			return
		}
		c.JSON(200, gin.H{"status": "ready"})
	})
	// Configuración de Swagger
	config := &ginSwagger.Config{
		URL: "doc.json",
	}
	r.GET("/swagger/*any", ginSwagger.CustomWrapHandler(config, swaggerFiles.Handler))

	// Registrar rutas
	// routes.SimpleRoutes(r)
	routes.AuthRoutes(r, db)

	port := os.Getenv("PORT")
	if port == "" {
		port = "80"
	}

	r.Run("0.0.0.0:" + port)
}
