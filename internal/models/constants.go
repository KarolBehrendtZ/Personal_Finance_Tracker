package models

type TrendDirectionTypes struct {
	Up     string
	Down   string
	Stable string
	New    string
}

var TrendDirections = TrendDirectionTypes{
	Up:     "up",
	Down:   "down",
	Stable: "stable",
	New:    "new",
}

type PredictionWeights struct {
	Current    float64
	Trend      float64
	Historical float64
}

var PredictionConfig = PredictionWeights{
	Current:    0.4,
	Trend:      0.4,
	Historical: 0.2,
}

type TrendThresholds struct {
	UpThreshold   float64
	DownThreshold float64
}

var TrendLimits = TrendThresholds{
	UpThreshold:   10.0,
	DownThreshold: -10.0,
}

type HistoricalPeriods struct {
	DayLookback   int
	WeekLookback  int
	MonthLookback int
}

var HistoricalDays = HistoricalPeriods{
	DayLookback:   30,
	WeekLookback:  84,
	MonthLookback: 365,
}

type PaginationDefaults struct {
	DefaultLimit  string
	DefaultOffset string
}

var Pagination = PaginationDefaults{
	DefaultLimit:  "20",
	DefaultOffset: "0",
}

type PredictionFactors struct {
	ConservativeEstimate float64
}

var PredictionSettings = PredictionFactors{
	ConservativeEstimate: 0.8,
}
