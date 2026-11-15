import sys
from tools import InventoryTool, LogisticsTool
from agents import NeedsAssessmentAgent, InventoryAgent, LogisticsAgent, FairnessAuditorAgent, ReliefCoordinator

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def print_output(board: dict, title: str):
    print("=" * 75)
    print(f"📍 {title}")
    print("=" * 75)

    print("\n📋 1. ALLOCATION TABLE:")
    print("-" * 75)
    print(f"{'Zone':<14} | {'Tier':<20} | {'Food':<6} | {'Water':<6} | {'Meds':<6} | {'Blankets':<8}")
    print("-" * 75)
    for z, items in board["allocation"].items():
        tier = board["needs"][z]["tier"]
        print(f"{z:<14} | {tier:<20} | {items.get('Food Kits',0):<6} | {items.get('Water Packs',0):<6} | {items.get('Medical Kits',0):<6} | {items.get('Blankets',0):<8}")

    print("\n🚚 2. ROUTE & DISPATCH PLAN:")
    print("-" * 75)
    for z, r in board["routes"].items():
        print(f"• {z:<14} -> Distance: {r['distance_km']} km | Est. Transit: {r['transit_hours']} hrs | {r['dispatch_priority']} ({r['mode']})")

    print("\n⚖️ 3. FAIRNESS AUDIT NOTE:")
    print("-" * 75)
    print(f"Status : {board['fairness_audit']['verdict']}")
    print(f"Details: {board['fairness_audit']['notes']}")
    print("=" * 75)

def run_evaluation():
    stock = {"Food Kits": 400, "Water Packs": 600, "Medical Kits": 150, "Blankets": 250}
    inv_tool = InventoryTool(stock)
    log_tool = LogisticsTool()

    needs_agent = NeedsAssessmentAgent()
    inv_agent = InventoryAgent(inv_tool)
    log_agent = LogisticsAgent(log_tool)
    fairness_agent = FairnessAuditorAgent()

    coordinator = ReliefCoordinator(needs_agent, inv_agent, log_agent, fairness_agent)

    # 1. Baseline Allocation Mission
    sample_scenario = {
        "Zone South": "CRITICAL: Flooding, 75 casualties, drinking water contaminated, homes collapsed.",
        "Zone East": "MODERATE: 250 people displaced in temporary shelters, food shortages.",
        "Zone North": "LOW: Minor localized road flooding, self-sufficient, no casualties."
    }
    board = coordinator.coordinate(sample_scenario, inv_tool.get_stock())
    print_output(board, "BASELINE DISASTER RELIEF MISSION")

    # 2. Evaluation Target (5 Scenarios)
    scenarios = [
        {
            "name": "Scenario 1: Coastal Flood Crisis",
            "expected_order": ["Zone South", "Zone East", "Zone North"],
            "stock": {"Food Kits": 300, "Water Packs": 500, "Medical Kits": 100, "Blankets": 150},
            "zones": {
                "Zone South": "CRITICAL: 90 casualties, severe flooding, trapped.",
                "Zone East": "MODERATE: 200 displaced, food shortage.",
                "Zone North": "LOW: Minor damage, monitoring situation."
            }
        },
        {
            "name": "Scenario 2: Urban Earthquake",
            "expected_order": ["Zone Central", "Zone West", "Zone East"],
            "stock": {"Food Kits": 450, "Water Packs": 600, "Medical Kits": 200, "Blankets": 300},
            "zones": {
                "Zone Central": "CRITICAL: High casualties, building collapse.",
                "Zone West": "MODERATE: Power failure, displaced residents.",
                "Zone East": "LOW: Stable, minor glass breakage."
            }
        },
        {
            "name": "Scenario 3: Mountain Landslide Isolation",
            "expected_order": ["Zone North", "Zone South", "Zone West"],
            "stock": {"Food Kits": 200, "Water Packs": 300, "Medical Kits": 120, "Blankets": 180},
            "zones": {
                "Zone North": "CRITICAL: Road cut off, 40 casualties, acute medical need.",
                "Zone South": "MODERATE: Flooded marketplace, shelter needed.",
                "Zone West": "LOW: Self-sufficient, minor rainfall."
            }
        },
        {
            "name": "Scenario 4: Extreme Resource Scarcity",
            "expected_order": ["Zone South", "Zone East", "Zone North"],
            "stock": {"Food Kits": 50, "Water Packs": 80, "Medical Kits": 30, "Blankets": 40},
            "zones": {
                "Zone South": "CRITICAL: Severe casualties, hospital flooded.",
                "Zone East": "MODERATE: Food and clean water shortage.",
                "Zone North": "LOW: Stable, no immediate danger."
            }
        },
        {
            "name": "Scenario 5: Balanced Cyclone Impact",
            "expected_order": ["Zone North", "Zone East", "Zone West"],
            "stock": {"Food Kits": 300, "Water Packs": 450, "Medical Kits": 150, "Blankets": 200},
            "zones": {
                "Zone North": "MODERATE: Roofs damaged, 100 displaced.",
                "Zone East": "MODERATE: Flooded roads, food shortages.",
                "Zone West": "MODERATE: Power grid down, basic supplies needed."
            }
        }
    ]

    print("\n" + "=" * 80)
    print("📊 EVALUATION TARGET: 5 SCENARIOS WITH KNOWN NEED RANKING")
    print("=" * 80)

    summary_rows = []
    for sc in scenarios:
        res = coordinator.coordinate(sc["zones"], sc["stock"])
        ranked_zones = sorted(res["needs"].keys(), key=lambda z: res["needs"][z]["need_score"], reverse=True)
        agreement = "100% Agreement" if ranked_zones == sc["expected_order"] else "Partial / Tie"
        zero_starvation = all(sum(s.values()) > 0 for s in res["allocation"].values())

        summary_rows.append({
            "Scenario": sc["name"][:32],
            "Top Zone": ranked_zones[0],
            "Agreement": agreement,
            "Zero Starvation": "PASS (No zero zones)" if zero_starvation else "FAIL"
        })

    print(f"{'Scenario':<34} | {'Top Zone':<14} | {'Ranking Agreement':<18} | {'Zero-Starvation':<16}")
    print("-" * 88)
    for row in summary_rows:
        print(f"{row['Scenario']:<34} | {row['Top Zone']:<14} | {row['Agreement']:<18} | {row['Zero Starvation']:<16}")
    print("=" * 80)

    # 3. Dynamic Re-Planning
    print("\n" + "=" * 75)
    print("🚨 INCOMING MID-RUN ALERT:")
    print("  'FLASH FLOOD & DAM BURST near Zone North! 110 casualties, immediate medical surge needed!'")
    print("=" * 75)

    urgent_alert = "CRITICAL: Dam burst near Zone North! 110 casualties, immediate medical surge needed!"
    re_board = coordinator.replan(board, "Zone North", urgent_alert)
    print_output(re_board, "DYNAMIC RE-PLANNING EXECUTION (AFTER MID-RUN ALERT)")

    # 4. Scope Restriction Guardrail & Backend Cache Memory Test
    print("\n" + "=" * 80)
    print("🛡️ SCOPE RESTRICTION GUARDRAIL & BACKEND CACHE MEMORY TEST")
    print("=" * 80)

    test_queries = [
        "What is the current inventory stock?",
        "Write a poem about Bollywood movies.",
        "Who won the FIFA World Cup?",
        "What is the current inventory stock?",
        "What is the fairness rule and SOP guidance for critical casualties?"
    ]

    for q in test_queries:
        res = coordinator.handle_user_query(q)
        print(f"❓ Query  : '{q}'")
        print(f"   Status : {res['status']} [Source: {res['source']}]")
        print(f"   Output : {res['response']}")
        print("-" * 75)

if __name__ == "__main__":
    run_evaluation()
