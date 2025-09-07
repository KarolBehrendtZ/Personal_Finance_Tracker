package models

import (
	"time"
)

type User struct {
	ID        int       `json:"id" db:"id"`
	Email     string    `json:"email" db:"email"`
	Password  string    `json:"-" db:"password_hash"`
	FirstName string    `json:"first_name" db:"first_name"`
	LastName  string    `json:"last_name" db:"last_name"`
	CreatedAt time.Time `json:"created_at" db:"created_at"`
	UpdatedAt time.Time `json:"updated_at" db:"updated_at"`
}

type Account struct {
	ID          int       `json:"id" db:"id"`
	UserID      int       `json:"user_id" db:"user_id"`
	Name        string    `json:"name" db:"name"`
	Type        string    `json:"type" db:"type"`
	Balance     float64   `json:"balance" db:"balance"`
	Currency    string    `json:"currency" db:"currency"`
	Description string    `json:"description" db:"description"`
	CreatedAt   time.Time `json:"created_at" db:"created_at"`
	UpdatedAt   time.Time `json:"updated_at" db:"updated_at"`
}

type Category struct {
	ID        int       `json:"id" db:"id"`
	UserID    int       `json:"user_id" db:"user_id"`
	Name      string    `json:"name" db:"name"`
	Type      string    `json:"type" db:"type"`
	Color     string    `json:"color" db:"color"`
	Icon      string    `json:"icon" db:"icon"`
	ParentID  *int      `json:"parent_id" db:"parent_id"`
	CreatedAt time.Time `json:"created_at" db:"created_at"`
	UpdatedAt time.Time `json:"updated_at" db:"updated_at"`
}

type Transaction struct {
	ID          int       `json:"id" db:"id"`
	UserID      int       `json:"user_id" db:"user_id"`
	AccountID   int       `json:"account_id" db:"account_id"`
	CategoryID  int       `json:"category_id" db:"category_id"`
	Amount      float64   `json:"amount" db:"amount"`
	Type        string    `json:"type" db:"type"`
	Description string    `json:"description" db:"description"`
	Date        time.Time `json:"date" db:"date"`
	Tags        []string  `json:"tags" db:"tags"`
	CreatedAt   time.Time `json:"created_at" db:"created_at"`
	UpdatedAt   time.Time `json:"updated_at" db:"updated_at"`
}

type BudgetRule struct {
	ID         int        `json:"id" db:"id"`
	UserID     int        `json:"user_id" db:"user_id"`
	CategoryID int        `json:"category_id" db:"category_id"`
	Amount     float64    `json:"amount" db:"amount"`
	Period     string     `json:"period" db:"period"`
	StartDate  time.Time  `json:"start_date" db:"start_date"`
	EndDate    *time.Time `json:"end_date" db:"end_date"`
	CreatedAt  time.Time  `json:"created_at" db:"created_at"`
	UpdatedAt  time.Time  `json:"updated_at" db:"updated_at"`
}

type RegisterRequest struct {
	Email     string `json:"email" binding:"required,email"`
	Password  string `json:"password" binding:"required,min=6"`
	FirstName string `json:"first_name" binding:"required"`
	LastName  string `json:"last_name" binding:"required"`
}

type LoginRequest struct {
	Email    string `json:"email" binding:"required,email"`
	Password string `json:"password" binding:"required"`
}

type AuthResponse struct {
	Token string `json:"token"`
	User  User   `json:"user"`
}

type TransactionFilter struct {
	AccountID  *int       `form:"account_id"`
	CategoryID *int       `form:"category_id"`
	Type       *string    `form:"type"`
	StartDate  *time.Time `form:"start_date"`
	EndDate    *time.Time `form:"end_date"`
	Limit      int        `form:"limit"`
	Offset     int        `form:"offset"`
}

type AnalyticsSummary struct {
	TotalIncome    float64 `json:"total_income"`
	TotalExpenses  float64 `json:"total_expenses"`
	NetIncome      float64 `json:"net_income"`
	AccountBalance float64 `json:"account_balance"`
	Period         string  `json:"period"`
}

type SpendingByCategory struct {
	CategoryID   int     `json:"category_id"`
	CategoryName string  `json:"category_name"`
	Amount       float64 `json:"amount"`
	Percentage   float64 `json:"percentage"`
}

type SpendingTrend struct {
	CategoryID     int     `json:"category_id"`
	CategoryName   string  `json:"category_name"`
	CurrentSpend   float64 `json:"current_spend"`
	PredictedSpend float64 `json:"predicted_spend"`
	TrendDirection string  `json:"trend_direction"`
	ChangePercent  float64 `json:"change_percent"`
}

type SpendingTrendsRequest struct {
	Period string `form:"period" binding:"required"`
	Date   string `form:"date"`
}

type SpendingTrendsResponse struct {
	Period string          `json:"period"`
	Date   string          `json:"date"`
	Trends []SpendingTrend `json:"trends"`
}

type PredictionData struct {
	CategoryID    int     `json:"category_id"`
	HistoricalAvg float64 `json:"historical_avg"`
	RecentTrend   float64 `json:"recent_trend"`
	Seasonality   float64 `json:"seasonality"`
}
