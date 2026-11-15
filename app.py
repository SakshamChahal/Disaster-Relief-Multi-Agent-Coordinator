import os
import json
from flask import Flask, render_template, request, jsonify
from tools import InventoryTool, LogisticsTool, load_inventory, save_inventory
from agents import NeedsAssessmentAgent, InventoryAgent, LogisticsAgent, FairnessAuditorAgent, ReliefCoordinator

app = Flask(__name__)

# Initialize singletons
inv_tool = InventoryTool()
log_tool = LogisticsTool()

needs_agent = NeedsAssessmentAgent()
inv_agent = InventoryAgent(inv_tool)
log_agent = LogisticsAgent(log_tool)
fairness_agent = FairnessAuditorAgent()
coordinator = ReliefCoordinator(needs_agent, inv_agent, log_agent, fairness_agent)

PRESET_SCENARIOS = {
    "flood": {
        "title": "Coastal Flood Crisis",
        "description": "Severe monsoon flooding, coastal surge, contaminated water supply.",
        "zones": [
            {
                "name": "Zone South",
                "distance_km": 120,
                "report": "CRITICAL: Flooding, 90 casualties, trapped families, drinking water contaminated, hospitals overwhelmed.",
                "requirements": "Urgent Medical Kits, 300 Water Packs, Life Rafts",
                "casualties": 90,
                "displaced": 350,
                "urgency": "critical"
            },
            {
                "name": "Zone East",
                "distance_km": 75,
                "report": "MODERATE: 200 displaced people sheltered in school buildings, localized food shortage, roads partially submerged.",
                "requirements": "Food Kits, Blankets, Clean Water",
                "casualties": 0,
                "displaced": 200,
                "urgency": "moderate"
            },
            {
                "name": "Zone North",
                "distance_km": 45,
                "report": "LOW: Minor damage, monitoring river embankment, electricity intact, no casualties.",
                "requirements": "Reserve maintenance kits",
                "casualties": 0,
                "displaced": 20,
                "urgency": "low"
            }
        ]
    },
    "earthquake": {
        "title": "Urban Earthquake",
        "description": "High magnitude seismic event, collapsed multi-story buildings, fires.",
        "zones": [
            {
                "name": "Zone Central",
                "distance_km": 15,
                "report": "CRITICAL: Multiple high-rise building collapses, 120 trapped casualties, medical clinics flattened.",
                "requirements": "Emergency Trauma Meds, Water, Search Equipment",
                "casualties": 120,
                "displaced": 500,
                "urgency": "critical"
            },
            {
                "name": "Zone West",
                "distance_km": 30,
                "report": "MODERATE: Power grid failure, structural wall cracks, displaced residents in open parks.",
                "requirements": "Blankets, Ready-to-eat Food, Drinking Water",
                "casualties": 5,
                "displaced": 250,
                "urgency": "moderate"
            },
            {
                "name": "Zone East",
                "distance_km": 75,
                "report": "LOW: Stable, minor glass breakage, municipal water operational.",
                "requirements": "Basic first aid supplies",
                "casualties": 0,
                "displaced": 10,
                "urgency": "low"
            }
        ]
    },
    "landslide": {
        "title": "Mountain Landslide Isolation",
        "description": "Continuous downpour triggered mudslides, blocking arterial highway access.",
        "zones": [
            {
                "name": "Zone North",
                "distance_km": 45,
                "report": "CRITICAL: Mountain road cut off, 40 severe casualties, acute medical need, clinic damaged.",
                "requirements": "Critical Medical Kits, Emergency Water",
                "casualties": 40,
                "displaced": 180,
                "urgency": "critical"
            },
            {
                "name": "Zone South",
                "distance_km": 120,
                "report": "MODERATE: Flooded marketplace, drainage blocked, shelter needed for 150 residents.",
                "requirements": "Food Kits, Warm Blankets",
                "casualties": 0,
                "displaced": 150,
                "urgency": "moderate"
            },
            {
                "name": "Zone West",
                "distance_km": 30,
                "report": "LOW: Self-sufficient, minor hillside rainfall, no structural breaches.",
                "requirements": "Routine monitoring stock",
                "casualties": 0,
                "displaced": 0,
                "urgency": "low"
            }
        ]
    },
    "cyclone": {
        "title": "Balanced Cyclone Impact",
        "description": "Category 3 cyclone landfall causing widespread roof damage and tree falls.",
        "zones": [
            {
                "name": "Zone North",
                "distance_km": 45,
                "report": "MODERATE: Coastal village roofs blown off, 100 people displaced, drinking water turbid.",
                "requirements": "Tarpaulins, Blankets, Water Purification",
                "casualties": 8,
                "displaced": 100,
                "urgency": "moderate"
            },
            {
                "name": "Zone East",
                "distance_km": 75,
                "report": "MODERATE: Flooded roads, food supply chain interrupted, grocery stores flooded.",
                "requirements": "Food Kits, Drinking Water Packs",
                "casualties": 2,
                "displaced": 90,
                "urgency": "moderate"
            },
            {
                "name": "Zone West",
                "distance_km": 30,
                "report": "MODERATE: Power grid down, hospital generator failing, basic supplies needed.",
                "requirements": "Medical replenishment, Food Kits",
                "casualties": 0,
                "displaced": 60,
                "urgency": "moderate"
            }
        ]
    }
}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/inventory", methods=["GET", "POST"])
def manage_inventory():
    if request.method == "POST":
        data = request.get_json(force=True) or {}
        new_stock = data.get("stock", {})
        if not new_stock:
            return jsonify({"status": "error", "message": "No stock data provided."}), 400
        updated = inv_tool.update_stock(new_stock)
        return jsonify({
            "status": "success",
            "message": "Warehouse inventory updated successfully.",
            "inventory": updated
        })
    else:
        return jsonify({
            "status": "success",
            "inventory": inv_tool.get_stock()
        })

@app.route("/api/scenarios", methods=["GET"])
def get_scenarios():
    return jsonify({
        "status": "success",
        "scenarios": PRESET_SCENARIOS
    })

@app.route("/api/allocate", methods=["POST"])
def allocate_resources():
    data = request.get_json(force=True) or {}
    zone_list = data.get("zones", [])

    if not zone_list:
        return jsonify({"status": "error", "message": "At least one zone report is required."}), 400

    situations = {}
    for z in zone_list:
        name = z.get("name", "").strip() or "Unnamed Zone"
        situations[name] = {
            "report": z.get("report", ""),
            "requirements": z.get("requirements", ""),
            "casualties": int(z.get("casualties", 0) or 0),
            "displaced": int(z.get("displaced", 0) or 0),
            "urgency": z.get("urgency", "auto"),
            "distance_km": int(z.get("distance_km", 0) or 0)
        }

    current_stock = inv_tool.get_stock()
    board = coordinator.coordinate(situations, current_stock)

    # Calculate inventory utilization summary
    total_allocated = {}
    remaining_stock = {}
    for item, total in current_stock.items():
        used = sum(alloc.get(item, 0) for alloc in board["allocation"].values())
        total_allocated[item] = used
        remaining_stock[item] = max(0, total - used)

    return jsonify({
        "status": "success",
        "board": board,
        "summary": {
            "initial_stock": current_stock,
            "allocated_stock": total_allocated,
            "remaining_stock": remaining_stock
        }
    })

@app.route("/api/replan", methods=["POST"])
def replan_mission():
    data = request.get_json(force=True) or {}
    zone = data.get("zone", "").strip()
    urgent_report = data.get("urgent_report", "").strip()

    if not zone or not urgent_report:
        return jsonify({"status": "error", "message": "Zone name and urgent alert report are required."}), 400

    if not coordinator.last_board:
        return jsonify({"status": "error", "message": "No active mission to replan. Please run allocation first."}), 400

    re_board = coordinator.replan(coordinator.last_board, zone, urgent_report)
    current_stock = inv_tool.get_stock()

    total_allocated = {}
    remaining_stock = {}
    for item, total in current_stock.items():
        used = sum(alloc.get(item, 0) for alloc in re_board["allocation"].values())
        total_allocated[item] = used
        remaining_stock[item] = max(0, total - used)

    return jsonify({
        "status": "success",
        "board": re_board,
        "summary": {
            "initial_stock": current_stock,
            "allocated_stock": total_allocated,
            "remaining_stock": remaining_stock
        }
    })

@app.route("/api/query", methods=["POST"])
def query_assistant():
    data = request.get_json(force=True) or {}
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"status": "error", "message": "Query cannot be empty."}), 400

    res = coordinator.handle_user_query(query)
    return jsonify(res)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
