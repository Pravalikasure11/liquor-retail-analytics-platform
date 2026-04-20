"""
Pricing Intelligence Service
Predicts optimal sell price based on:
- Cost price + target margin
- Category benchmarks
- Historical sales velocity
- Competitor price ranges (configurable)
- Seasonal demand factors
"""
from typing import Optional
from app.core.config import get_settings

settings = get_settings()

# Category-specific target margins (liquor store industry benchmarks)
CATEGORY_MARGINS = {
    "Beer":           {"target": 0.30, "min": 0.20, "max": 0.45},
    "Hard Liquor":    {"target": 0.35, "min": 0.25, "max": 0.55},
    "Wine":           {"target": 0.40, "min": 0.30, "max": 0.60},
    "Hard Cider":     {"target": 0.35, "min": 0.25, "max": 0.50},
    "Cocktails":      {"target": 0.40, "min": 0.30, "max": 0.55},
    "Cool Drinks":    {"target": 0.35, "min": 0.25, "max": 0.50},
    "Cigarettes":     {"target": 0.20, "min": 0.10, "max": 0.30},
    "E-Cigarettes":   {"target": 0.35, "min": 0.25, "max": 0.55},
    "Snacks & Chips": {"target": 0.45, "min": 0.35, "max": 0.60},
    "Accessories":    {"target": 0.50, "min": 0.40, "max": 0.70},
}

# Seasonal demand multipliers
SEASONAL_FACTORS = {
    "christmas":     1.15,
    "new_year":      1.20,
    "st_patricks":   1.10,
    "super_bowl":    1.12,
    "july_4th":      1.10,
    "labor_day":     1.08,
    "thanksgiving":  1.10,
    "memorial_day":  1.08,
    "summer":        1.05,
    "default":       1.00,
}


def predict_price(
    cost_price: float,
    category: str,
    current_sell_price: Optional[float] = None,
    sales_velocity: Optional[float] = None,   # units/week
    season: Optional[str] = None,
) -> dict:
    """
    Returns predicted price with full reasoning.
    """
    if cost_price <= 0:
        return {"predicted_price": 0, "reasoning": "Invalid cost price", "margin_pct": 0}

    margins = CATEGORY_MARGINS.get(category, {"target": 0.35, "min": 0.25, "max": 0.55})
    target_margin = margins["target"]
    min_margin = margins["min"]

    # Base price at target margin: price = cost / (1 - margin)
    base_price = cost_price / (1 - target_margin)

    # Apply seasonal factor
    season_factor = SEASONAL_FACTORS.get(season or "default", 1.0)
    adjusted_price = base_price * season_factor

    # Velocity adjustment: fast movers can carry slightly higher price
    velocity_adj = 1.0
    if sales_velocity is not None:
        if sales_velocity > 20:   # high velocity
            velocity_adj = 1.05
        elif sales_velocity < 2:  # slow mover
            velocity_adj = 0.95

    final_price = adjusted_price * velocity_adj

    # Ensure min margin
    min_price = cost_price / (1 - min_margin)
    final_price = max(final_price, min_price)

    # Round to clean retail price (e.g. x.99)
    final_price = round(final_price - 0.01, 2) + 0.00  # e.g. 32.00 → keep as is
    if final_price > 5:
        # Apply psychological pricing (.99)
        import math
        final_price = math.floor(final_price) + 0.99 if final_price % 1 < 0.5 else math.floor(final_price) + 0.99

    actual_margin = round((final_price - cost_price) / final_price * 100, 1)

    # Build reasoning
    reasoning_parts = [
        f"Target margin for {category}: {int(target_margin*100)}%",
        f"Base price at target margin: ${base_price:.2f}",
    ]
    if season and season != "default":
        reasoning_parts.append(f"Seasonal uplift ({season}): {int((season_factor-1)*100)}%")
    if velocity_adj != 1.0:
        direction = "high" if velocity_adj > 1 else "low"
        reasoning_parts.append(f"Velocity adjustment ({direction} demand): {int((velocity_adj-1)*100):+}%")
    if current_sell_price:
        diff = round(final_price - current_sell_price, 2)
        reasoning_parts.append(f"Current price: ${current_sell_price:.2f} (suggested change: ${diff:+.2f})")

    return {
        "predicted_price": round(final_price, 2),
        "min_price": round(min_price, 2),
        "target_margin_pct": int(target_margin * 100),
        "actual_margin_pct": actual_margin,
        "reasoning": " | ".join(reasoning_parts),
        "season_applied": season,
        "velocity_factor": velocity_adj,
    }


def bulk_predict(products: list) -> list:
    """Run pricing prediction on a list of product dicts."""
    results = []
    for p in products:
        prediction = predict_price(
            cost_price=p.get("cost_price", 0),
            category=p.get("category", "Hard Liquor"),
            current_sell_price=p.get("sell_price"),
        )
        results.append({"product_id": p["id"], "product_name": p["name"], **prediction})
    return results
