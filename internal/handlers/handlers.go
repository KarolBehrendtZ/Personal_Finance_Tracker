package handlers

import (
	"database/sql"
	"fmt"
	"log"
	"net/http"
	"strconv"
	"strings"
	"time"

	"personal-finance-tracker/internal/auth"
	"personal-finance-tracker/internal/models"

	"github.com/gin-gonic/gin"
)

type Handler struct {
	db *sql.DB
}

func NewHandler(db *sql.DB) *Handler {
	return &Handler{db: db}
}

func (h *Handler) HealthCheck(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"status": "healthy"})
}

func (h *Handler) RootHandler(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"message": "Personal Finance Tracker API",
		"version": "1.0.0",
		"endpoints": gin.H{
			"health":       "/health or /api/v1/health",
			"auth":         "/api/v1/auth/{register,login}",
			"accounts":     "/api/v1/accounts",
			"categories":   "/api/v1/categories",
			"transactions": "/api/v1/transactions",
			"analytics":    "/api/v1/analytics/{summary,spending}",
		},
		"documentation": "https://github.com/your-repo/personal-finance-tracker",
	})
}

func (h *Handler) AuthMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		authHeader := c.GetHeader("Authorization")
		if authHeader == "" {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Authorization header required"})
			c.Abort()
			return
		}

		tokenString := strings.TrimPrefix(authHeader, "Bearer ")
		claims, err := auth.ValidateJWT(tokenString)
		if err != nil {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid token"})
			c.Abort()
			return
		}

		c.Set("user_id", claims.UserID)
		c.Set("email", claims.Email)
		c.Next()
	}
}

func (h *Handler) Register(c *gin.Context) {
	var req models.RegisterRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Add logging for debugging
	log.Printf("Register request: %+v", req)

	hashedPassword, err := auth.HashPassword(req.Password)
	if err != nil {
		log.Printf("Failed to hash password: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to hash password"})
		return
	}

	var userID int
	query := `INSERT INTO users (email, password_hash, first_name, last_name, created_at, updated_at) 
			  VALUES ($1, $2, $3, $4, NOW(), NOW()) RETURNING id`

	err = h.db.QueryRow(query, req.Email, hashedPassword, req.FirstName, req.LastName).Scan(&userID)
	if err != nil {
		log.Printf("Failed to create user in database: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create user"})
		return
	}

	token, err := auth.GenerateJWT(userID, req.Email)
	if err != nil {
		log.Printf("Failed to generate JWT: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to generate token"})
		return
	}

	user := models.User{
		ID:        userID,
		Email:     req.Email,
		FirstName: req.FirstName,
		LastName:  req.LastName,
	}

	c.JSON(http.StatusCreated, models.AuthResponse{
		Token: token,
		User:  user,
	})
}

func (h *Handler) Login(c *gin.Context) {
	var req models.LoginRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	var user models.User
	query := `SELECT id, email, password_hash, first_name, last_name FROM users WHERE email = $1`

	err := h.db.QueryRow(query, req.Email).Scan(&user.ID, &user.Email, &user.Password, &user.FirstName, &user.LastName)
	if err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid credentials"})
		return
	}

	if !auth.CheckPasswordHash(req.Password, user.Password) {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid credentials"})
		return
	}

	token, err := auth.GenerateJWT(user.ID, user.Email)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to generate token"})
		return
	}

	c.JSON(http.StatusOK, models.AuthResponse{
		Token: token,
		User:  user,
	})
}

func (h *Handler) GetProfile(c *gin.Context) {
	userID := c.GetInt("user_id")

	var user models.User
	query := `SELECT id, email, first_name, last_name, created_at, updated_at FROM users WHERE id = $1`

	err := h.db.QueryRow(query, userID).Scan(&user.ID, &user.Email, &user.FirstName, &user.LastName, &user.CreatedAt, &user.UpdatedAt)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "User not found"})
		return
	}

	c.JSON(http.StatusOK, user)
}

func (h *Handler) UpdateProfile(c *gin.Context) {
	// Implementation for updating user profile
	c.JSON(http.StatusOK, gin.H{"message": "Profile updated"})
}

func (h *Handler) GetAccounts(c *gin.Context) {
	userID := c.GetInt("user_id")

	query := `SELECT id, user_id, name, type, balance, currency, description, created_at, updated_at 
			  FROM accounts WHERE user_id = $1 ORDER BY created_at DESC`

	rows, err := h.db.Query(query, userID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch accounts"})
		return
	}
	defer rows.Close()

	var accounts []models.Account
	for rows.Next() {
		var account models.Account
		err := rows.Scan(&account.ID, &account.UserID, &account.Name, &account.Type,
			&account.Balance, &account.Currency, &account.Description,
			&account.CreatedAt, &account.UpdatedAt)
		if err != nil {
			continue
		}
		accounts = append(accounts, account)
	}

	c.JSON(http.StatusOK, accounts)
}

func (h *Handler) CreateAccount(c *gin.Context) {
	userID := c.GetInt("user_id")

	var account models.Account
	if err := c.ShouldBindJSON(&account); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	account.UserID = userID

	query := `INSERT INTO accounts (user_id, name, type, balance, currency, description, created_at, updated_at) 
			  VALUES ($1, $2, $3, $4, $5, $6, NOW(), NOW()) RETURNING id, created_at, updated_at`

	err := h.db.QueryRow(query, account.UserID, account.Name, account.Type,
		account.Balance, account.Currency, account.Description).
		Scan(&account.ID, &account.CreatedAt, &account.UpdatedAt)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create account"})
		return
	}

	c.JSON(http.StatusCreated, account)
}

func (h *Handler) UpdateAccount(c *gin.Context) {
	// Implementation for updating account
	c.JSON(http.StatusOK, gin.H{"message": "Account updated"})
}

func (h *Handler) DeleteAccount(c *gin.Context) {
	// Implementation for deleting account
	c.JSON(http.StatusOK, gin.H{"message": "Account deleted"})
}

func (h *Handler) GetCategories(c *gin.Context) {
	// Implementation for getting categories
	c.JSON(http.StatusOK, []models.Category{})
}

func (h *Handler) CreateCategory(c *gin.Context) {
	// Implementation for creating category
	c.JSON(http.StatusCreated, gin.H{"message": "Category created"})
}

func (h *Handler) UpdateCategory(c *gin.Context) {
	// Implementation for updating category
	c.JSON(http.StatusOK, gin.H{"message": "Category updated"})
}

func (h *Handler) DeleteCategory(c *gin.Context) {
	// Implementation for deleting category
	c.JSON(http.StatusOK, gin.H{"message": "Category deleted"})
}

func (h *Handler) GetTransactions(c *gin.Context) {
	userID := c.GetInt("user_id")

	// Parse query parameters for filtering
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "20"))
	offset, _ := strconv.Atoi(c.DefaultQuery("offset", "0"))

	query := `SELECT t.id, t.user_id, t.account_id, t.category_id, t.amount, t.type, 
			  t.description, t.date, t.created_at, t.updated_at
			  FROM transactions t 
			  WHERE t.user_id = $1 
			  ORDER BY t.date DESC, t.created_at DESC 
			  LIMIT $2 OFFSET $3`

	rows, err := h.db.Query(query, userID, limit, offset)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch transactions"})
		return
	}
	defer rows.Close()

	var transactions []models.Transaction
	for rows.Next() {
		var transaction models.Transaction
		err := rows.Scan(&transaction.ID, &transaction.UserID, &transaction.AccountID,
			&transaction.CategoryID, &transaction.Amount, &transaction.Type,
			&transaction.Description, &transaction.Date,
			&transaction.CreatedAt, &transaction.UpdatedAt)
		if err != nil {
			continue
		}
		transactions = append(transactions, transaction)
	}

	c.JSON(http.StatusOK, transactions)
}

func (h *Handler) CreateTransaction(c *gin.Context) {
	// Implementation for creating transaction
	c.JSON(http.StatusCreated, gin.H{"message": "Transaction created"})
}

func (h *Handler) UpdateTransaction(c *gin.Context) {
	// Implementation for updating transaction
	c.JSON(http.StatusOK, gin.H{"message": "Transaction updated"})
}

func (h *Handler) DeleteTransaction(c *gin.Context) {
	// Implementation for deleting transaction
	c.JSON(http.StatusOK, gin.H{"message": "Transaction deleted"})
}

func (h *Handler) BulkCreateTransactions(c *gin.Context) {
	// Implementation for bulk creating transactions
	c.JSON(http.StatusCreated, gin.H{"message": "Transactions created"})
}

func (h *Handler) GetAnalyticsSummary(c *gin.Context) {
	userID := c.GetInt("user_id")

	// Get query parameters for date range
	startDate := c.DefaultQuery("start_date", "")
	endDate := c.DefaultQuery("end_date", "")

	var summary models.AnalyticsSummary

	query := `
		SELECT 
			COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0) as total_income,
			COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) as total_expenses,
			COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE -amount END), 0) as net_income
		FROM transactions 
		WHERE user_id = $1`

	params := []interface{}{userID}
	paramCount := 1

	if startDate != "" {
		paramCount++
		query += fmt.Sprintf(" AND date >= $%d", paramCount)
		params = append(params, startDate)
	}

	if endDate != "" {
		paramCount++
		query += fmt.Sprintf(" AND date <= $%d", paramCount)
		params = append(params, endDate)
	}

	err := h.db.QueryRow(query, params...).Scan(&summary.TotalIncome, &summary.TotalExpenses, &summary.NetIncome)
	if err != nil {
		log.Printf("Error getting analytics summary: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to get analytics summary"})
		return
	}

	// Get account balance
	balanceQuery := `SELECT COALESCE(SUM(balance), 0) FROM accounts WHERE user_id = $1`
	err = h.db.QueryRow(balanceQuery, userID).Scan(&summary.AccountBalance)
	if err != nil {
		log.Printf("Error getting account balance: %v", err)
		summary.AccountBalance = 0
	}

	summary.Period = "custom"
	if startDate == "" && endDate == "" {
		summary.Period = "all_time"
	}

	c.JSON(http.StatusOK, summary)
}

func (h *Handler) GetSpendingAnalytics(c *gin.Context) {
	userID := c.GetInt("user_id")

	// Get query parameters for date range
	startDate := c.DefaultQuery("start_date", "")
	endDate := c.DefaultQuery("end_date", "")

	query := `
		SELECT 
			c.id,
			c.name,
			COALESCE(SUM(t.amount), 0) as total_amount
		FROM categories c
		LEFT JOIN transactions t ON c.id = t.category_id AND t.type = 'expense'
		WHERE c.user_id = $1 AND c.type = 'expense'`

	params := []interface{}{userID}
	paramCount := 1

	if startDate != "" {
		paramCount++
		query += fmt.Sprintf(" AND t.date >= $%d", paramCount)
		params = append(params, startDate)
	}

	if endDate != "" {
		paramCount++
		query += fmt.Sprintf(" AND t.date <= $%d", paramCount)
		params = append(params, endDate)
	}

	query += `
		GROUP BY c.id, c.name
		ORDER BY total_amount DESC`

	rows, err := h.db.Query(query, params...)
	if err != nil {
		log.Printf("Error getting spending analytics: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to get spending analytics"})
		return
	}
	defer rows.Close()

	var analytics []models.SpendingByCategory
	var totalSpending float64

	for rows.Next() {
		var spending models.SpendingByCategory
		err := rows.Scan(&spending.CategoryID, &spending.CategoryName, &spending.Amount)
		if err != nil {
			log.Printf("Error scanning spending row: %v", err)
			continue
		}
		analytics = append(analytics, spending)
		totalSpending += spending.Amount
	}

	// Calculate percentages
	for i := range analytics {
		if totalSpending > 0 {
			analytics[i].Percentage = (analytics[i].Amount / totalSpending) * 100
		} else {
			analytics[i].Percentage = 0
		}
	}

	c.JSON(http.StatusOK, analytics)
}

// GetSpendingTrends returns spending trends with predictions
func (h *Handler) GetSpendingTrends(c *gin.Context) {
	userID := c.GetInt("user_id")

	var req models.SpendingTrendsRequest
	if err := c.ShouldBindQuery(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Default to current date if not provided
	if req.Date == "" {
		req.Date = time.Now().Format("2006-01-02")
	}

	trends, err := h.calculateSpendingTrends(userID, req.Period, req.Date)
	if err != nil {
		log.Printf("Error calculating spending trends: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to calculate spending trends"})
		return
	}

	response := models.SpendingTrendsResponse{
		Period: req.Period,
		Date:   req.Date,
		Trends: trends,
	}

	c.JSON(http.StatusOK, response)
}

// calculateSpendingTrends calculates current spending and predictions
func (h *Handler) calculateSpendingTrends(userID int, period, dateStr string) ([]models.SpendingTrend, error) {
	date, err := time.Parse("2006-01-02", dateStr)
	if err != nil {
		return nil, err
	}

	var startDate, endDate time.Time
	var prevStartDate, prevEndDate time.Time

	// Calculate date ranges based on period
	switch period {
	case "day":
		startDate = time.Date(date.Year(), date.Month(), date.Day(), 0, 0, 0, 0, date.Location())
		endDate = startDate.AddDate(0, 0, 1)
		prevStartDate = startDate.AddDate(0, 0, -1)
		prevEndDate = startDate
	case "week":
		// Start of week (Monday)
		weekday := int(date.Weekday())
		if weekday == 0 {
			weekday = 7
		} // Sunday = 7
		startDate = date.AddDate(0, 0, -(weekday - 1))
		startDate = time.Date(startDate.Year(), startDate.Month(), startDate.Day(), 0, 0, 0, 0, startDate.Location())
		endDate = startDate.AddDate(0, 0, 7)
		prevStartDate = startDate.AddDate(0, 0, -7)
		prevEndDate = startDate
	case "month":
		startDate = time.Date(date.Year(), date.Month(), 1, 0, 0, 0, 0, date.Location())
		endDate = startDate.AddDate(0, 1, 0)
		prevStartDate = startDate.AddDate(0, -1, 0)
		prevEndDate = startDate
	default:
		return nil, fmt.Errorf("invalid period: %s", period)
	}

	// Get current period spending by category
	currentQuery := `
		SELECT c.id, c.name, COALESCE(SUM(t.amount), 0) as amount
		FROM categories c
		LEFT JOIN transactions t ON c.id = t.category_id 
			AND t.user_id = $1 
			AND t.type = 'expense'
			AND t.date >= $2 
			AND t.date < $3
		WHERE c.user_id = $1 AND c.type = 'expense'
		GROUP BY c.id, c.name
		ORDER BY amount DESC
	`

	currentRows, err := h.db.Query(currentQuery, userID, startDate, endDate)
	if err != nil {
		return nil, err
	}
	defer currentRows.Close()

	// Get previous period spending for comparison
	prevQuery := `
		SELECT c.id, COALESCE(SUM(t.amount), 0) as amount
		FROM categories c
		LEFT JOIN transactions t ON c.id = t.category_id 
			AND t.user_id = $1 
			AND t.type = 'expense'
			AND t.date >= $2 
			AND t.date < $3
		WHERE c.user_id = $1 AND c.type = 'expense'
		GROUP BY c.id
	`

	prevRows, err := h.db.Query(prevQuery, userID, prevStartDate, prevEndDate)
	if err != nil {
		return nil, err
	}
	defer prevRows.Close()

	// Store previous period data
	prevSpending := make(map[int]float64)
	for prevRows.Next() {
		var categoryID int
		var amount float64
		if err := prevRows.Scan(&categoryID, &amount); err != nil {
			continue
		}
		prevSpending[categoryID] = amount
	}

	// Calculate trends and predictions
	var trends []models.SpendingTrend
	for currentRows.Next() {
		var trend models.SpendingTrend
		if err := currentRows.Scan(&trend.CategoryID, &trend.CategoryName, &trend.CurrentSpend); err != nil {
			continue
		}

		// Get historical average for prediction
		historicalAvg, err := h.getHistoricalAverage(userID, trend.CategoryID, period)
		if err != nil {
			historicalAvg = trend.CurrentSpend // fallback
		}

		// Calculate prediction based on trend
		prevAmount := prevSpending[trend.CategoryID]
		prediction := h.calculatePrediction(trend.CurrentSpend, prevAmount, historicalAvg, period)

		trend.PredictedSpend = prediction

		// Calculate trend direction and change
		if prevAmount > 0 {
			change := ((trend.CurrentSpend - prevAmount) / prevAmount) * 100
			trend.ChangePercent = change

			if change > 10 {
				trend.TrendDirection = "up"
			} else if change < -10 {
				trend.TrendDirection = "down"
			} else {
				trend.TrendDirection = "stable"
			}
		} else {
			trend.TrendDirection = "new"
			trend.ChangePercent = 0
		}

		trends = append(trends, trend)
	}

	return trends, nil
}

// getHistoricalAverage calculates average spending for a category over last periods
func (h *Handler) getHistoricalAverage(userID, categoryID int, period string) (float64, error) {
	var days int
	switch period {
	case "day":
		days = 30 // last 30 days
	case "week":
		days = 84 // last 12 weeks
	case "month":
		days = 365 // last 12 months
	}

	query := `
		SELECT COALESCE(AVG(amount), 0)
		FROM transactions 
		WHERE user_id = $1 
			AND category_id = $2 
			AND type = 'expense'
			AND date >= NOW() - INTERVAL '%d days'
	`

	var avg float64
	err := h.db.QueryRow(fmt.Sprintf(query, days), userID, categoryID).Scan(&avg)
	return avg, err
}

// calculatePrediction uses simple trending algorithm
func (h *Handler) calculatePrediction(current, previous, historical float64, period string) float64 {
	// Weight factors
	const (
		currentWeight    = 0.4
		trendWeight      = 0.4
		historicalWeight = 0.2
	)

	// Calculate trend factor
	var trendFactor float64
	if previous > 0 {
		trendFactor = current - previous
	} else {
		trendFactor = 0
	}

	// Simple prediction: weighted average with trend
	prediction := (current * currentWeight) +
		(trendFactor * trendWeight) +
		(historical * historicalWeight)

	// Ensure prediction is not negative
	if prediction < 0 {
		prediction = current * 0.8 // conservative estimate
	}

	return prediction
}
