class TrendDirections:
    """Constants for trend direction values used across the application."""
    
    UP = "up"          # Spending is trending up (increase > 10%)
    DOWN = "down"      # Spending is trending down (decrease < -10%)
    STABLE = "stable"  # Spending is stable (change between -10% and 10%)
    NEW = "new"        # New category or no previous data

# Mapping for trend direction indicators in the UI
TREND_INDICATORS = {
    TrendDirections.UP: '📈 ↗️',
    TrendDirections.DOWN: '📉 ↘️', 
    TrendDirections.STABLE: '➡️',
    TrendDirections.NEW: '🆕'
}
