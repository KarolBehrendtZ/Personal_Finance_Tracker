"""
Constants for the Personal Finance Tracker Dashboard.

IMPORTANT: These constants must match the Go backend constants defined in:
internal/models/trend_direction.go (formerly constants.go)

Backend constants:
- TrendDirections.Up = "up"
- TrendDirections.Down = "down" 
- TrendDirections.Stable = "stable"
- TrendDirections.New = "new"

Any changes to these values must be synchronized between both files.
"""

class TrendDirections:
    """
    Constants for trend direction values used across the application.
    
    These values MUST match the Go backend TrendDirections constants
    defined in internal/models/trend_direction.go
    """
    
    UP = "up"          # Spending is trending up (increase > threshold)
    DOWN = "down"      # Spending is trending down (decrease < negative threshold)
    STABLE = "stable"  # Spending is stable (change within threshold range)
    NEW = "new"        # New category or no previous data


def validate_trend_constants():
    """
    Validation function to ensure trend direction constants are properly defined.
    This should be called during application startup to catch any issues early.
    
    Raises:
        ValueError: If any required constant is missing or invalid
    """
    required_trends = ['UP', 'DOWN', 'STABLE', 'NEW']
    
    for trend in required_trends:
        if not hasattr(TrendDirections, trend):
            raise ValueError(f"Missing required trend direction constant: {trend}")
        
        value = getattr(TrendDirections, trend)
        if not isinstance(value, str) or not value:
            raise ValueError(f"Invalid trend direction value for {trend}: {value}")
    
    # Ensure all values are unique
    values = [TrendDirections.UP, TrendDirections.DOWN, TrendDirections.STABLE, TrendDirections.NEW]
    if len(values) != len(set(values)):
        raise ValueError("Trend direction constants must have unique values")
    
    print("✓ Trend direction constants validation passed")


# Validate constants on import
validate_trend_constants()

# Mapping for trend direction indicators in the UI
TREND_INDICATORS = {
    TrendDirections.UP: '📈 ↗️',
    TrendDirections.DOWN: '📉 ↘️', 
    TrendDirections.STABLE: '➡️',
    TrendDirections.NEW: '🆕'
}
