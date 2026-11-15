from typing import Dict, Any, Optional
import os
import json

INVENTORY_FILE = os.path.join(os.path.dirname(__file__), "inventory.json")

DEFAULT_STOCK = {
    "Food Kits": 400,
    "Water Packs": 600,
    "Medical Kits": 150,
    "Blankets": 250
}

def load_inventory() -> Dict[str, int]:
    """Load inventory from JSON file or return default stock."""
    if os.path.exists(INVENTORY_FILE):
        try:
            with open(INVENTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and data:
                    return {str(k): int(v) for k, v in data.items()}
        except Exception:
            pass
    return dict(DEFAULT_STOCK)

def save_inventory(stock: Dict[str, int]) -> None:
    """Persist inventory to JSON file."""
    try:
        with open(INVENTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(stock, f, indent=2)
    except Exception as e:
        print(f"Warning: Failed to save inventory to file: {e}")

SOP_DATABASE = [
    {
        "tier": "Tier 1 (Critical Need)",
        "score_range": (8.0, 10.0),
        "keywords": ["critical", "casualties", "collapse", "severe", "trapped", "drowning", "burst", "urgent", "life-threatening"],
        "rule": "Active casualties, structural collapse, or water contamination. Must receive top priority and at least 40% of critical supplies. Zero allocation is strictly prohibited."
    },
    {
        "tier": "Tier 2 (Moderate Need)",
        "score_range": (5.0, 7.9),
        "keywords": ["moderate", "shortage", "displaced", "flooded", "shelter", "submerged", "stranded"],
        "rule": "Displaced population and basic supply shortages. Allocated proportional share after Tier 1 baseline is reserved."
    },
    {
        "tier": "Tier 3 (Low Need)",
        "score_range": (1.0, 4.9),
        "keywords": ["low", "stable", "minor", "monitoring", "self-sufficient", "contained", "normal"],
        "rule": "Minor localized damage. Self-sufficient for 48 hours. Receive baseline maintenance kits once higher tiers are fulfilled."
    }
]

def rag_retrieve_sop(situation_report: str) -> Dict[str, Any]:
    text = situation_report.lower()
    has_active_casualties = "casualties" in text and "no casualties" not in text
    if has_active_casualties or any(k in text for k in ["burst", "severe", "critical", "collapse", "drowning", "trapped", "life-threatening"]):
        return SOP_DATABASE[0]
    elif any(k in text for k in ["moderate", "displaced", "shortage", "shelter", "submerged", "stranded"]):
        return SOP_DATABASE[1]
    return SOP_DATABASE[2]

class InventoryTool:
    def __init__(self, stock: Optional[Dict[str, int]] = None):
        if stock is None:
            self.stock = load_inventory()
        else:
            self.stock = dict(stock)

    def get_stock(self) -> Dict[str, int]:
        return dict(self.stock)

    def update_stock(self, new_stock: Dict[str, int]) -> Dict[str, int]:
        self.stock = {str(k): max(0, int(v)) for k, v in new_stock.items()}
        save_inventory(self.stock)
        return self.get_stock()

    def set_item_qty(self, item: str, qty: int) -> Dict[str, int]:
        self.stock[item] = max(0, int(qty))
        save_inventory(self.stock)
        return self.get_stock()

class LogisticsTool:
    DISTANCES_KM = {
        "Zone North": 45,
        "Zone South": 120,
        "Zone East": 75,
        "Zone West": 30,
        "Zone Central": 15
    }

    def calculate_route(self, zone: str, custom_dist: Optional[int] = None) -> Dict[str, Any]:
        if custom_dist is not None and custom_dist > 0:
            dist = int(custom_dist)
        else:
            dist = self.DISTANCES_KM.get(zone, 50)
        transit_hrs = round(dist / 40.0, 1)
        return {
            "distance_km": dist,
            "transit_hours": transit_hrs,
            "mode": "Express Dispatch" if dist <= 50 else "Heavy Convoy"
        }
