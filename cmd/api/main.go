package main

import (
	"log"
	"os"

	"personal-finance-tracker/internal/database"
	"personal-finance-tracker/internal/handlers"

	"github.com/gin-gonic/gin"
	"github.com/joho/godotenv"
)

func main() {
	if err := godotenv.Load(); err != nil {
		log.Println("No .env file found")
	}

	db, err := database.Initialize()
	if err != nil {
		log.Fatal("Failed to connect to database:", err)
	}
	defer db.Close()

	router := gin.Default()

	h := handlers.NewHandler(db)

	setupRoutes(router, h)

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	log.Printf("Starting server on port %s", port)
	log.Fatal(router.Run(":" + port))
}

func setupRoutes(router *gin.Engine, h *handlers.Handler) {
	router.GET("/", h.RootHandler)
	router.GET("/health", h.HealthCheck)

	api := router.Group("/api/v1")

	api.GET("/health", h.HealthCheck)
	auth := api.Group("/auth")
	{
		auth.POST("/register", h.Register)
		auth.POST("/login", h.Login)
	}

	protected := api.Group("/")
	protected.Use(h.AuthMiddleware())
	{
		protected.GET("/profile", h.GetProfile)
		protected.PUT("/profile", h.UpdateProfile)

		protected.GET("/accounts", h.GetAccounts)
		protected.POST("/accounts", h.CreateAccount)
		protected.PUT("/accounts/:id", h.UpdateAccount)
		protected.DELETE("/accounts/:id", h.DeleteAccount)

		protected.GET("/categories", h.GetCategories)
		protected.POST("/categories", h.CreateCategory)
		protected.PUT("/categories/:id", h.UpdateCategory)
		protected.DELETE("/categories/:id", h.DeleteCategory)

		protected.GET("/transactions", h.GetTransactions)
		protected.POST("/transactions", h.CreateTransaction)
		protected.PUT("/transactions/:id", h.UpdateTransaction)
		protected.DELETE("/transactions/:id", h.DeleteTransaction)
		protected.POST("/transactions/bulk", h.BulkCreateTransactions)

		protected.GET("/analytics/summary", h.GetAnalyticsSummary)
		protected.GET("/analytics/spending", h.GetSpendingAnalytics)
		protected.GET("/analytics/trends", h.GetSpendingTrends)
	}
}
