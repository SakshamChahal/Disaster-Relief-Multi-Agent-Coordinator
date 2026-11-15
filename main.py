import sys
import os
import webbrowser
from typing import Dict
from tools import InventoryTool, LogisticsTool, load_inventory, save_inventory
from agents import NeedsAssessmentAgent, InventoryAgent, LogisticsAgent, FairnessAuditorAgent, ReliefCoordinator

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def print_banner():
    print("=" * 75)
    print("📍 DISASTER RELIEF MULTI-AGENT SYSTEM & LOGISTICS COORDINATOR")
    print("   Autonomous Triage • Zero-Starvation Allocation • Route Logistics")
    print("=" * 75)

def display_inventory(stock: Dict[str, int]):
    print("\n📦 CURRENT WAREHOUSE INVENTORY:")
    print("-" * 75)
    for item, qty in stock.items():
        print(f"  • {item:<16} : {qty:>5} units")
    print("-" * 75)

def prompt_inventory_update(inv_tool: InventoryTool) -> Dict[str, int]:
    current_stock = inv_tool.get_stock()
    display_inventory(current_stock)

    try:
        choice = input("\nDo you want to update inventory stock? (y/N) [Default: N]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        choice = "n"

    if choice in ["y", "yes"]:
        print("\n✏️  Enter updated quantities (press Enter to keep existing value):")
        updated_stock = {}
        for item, current_val in current_stock.items():
            try:
                val_str = input(f"  • {item} [{current_val}]: ").strip()
                if val_str:
                    updated_stock[item] = max(0, int(val_str))
                else:
                    updated_stock[item] = current_val
            except ValueError:
                print(f"    Invalid number. Retaining current value ({current_val}).")
                updated_stock[item] = current_val
            except (EOFError, KeyboardInterrupt):
                updated_stock[item] = current_val

        # Option to add custom new item
        try:
            add_more = input("\nDo you want to add a new resource item? (y/N) [Default: N]: ").strip().lower()
            if add_more in ["y", "yes"]:
                new_item = input("  Enter item name (e.g., Tents, Baby Food): ").strip()
                if new_item:
                    new_qty_str = input(f"  Enter quantity for {new_item}: ").strip()
                    updated_stock[new_item] = max(0, int(new_qty_str or 0))
        except (EOFError, KeyboardInterrupt):
            pass

        saved = inv_tool.update_stock(updated_stock)
        print("\n✅ Warehouse inventory updated successfully!")
        display_inventory(saved)
        return saved
    else:
        print("Using current warehouse inventory.")
        return current_stock

def print_allocation_output(board: dict, title: str):
    print("\n" + "=" * 75)
    print(f"📍 {title}")
    print("=" * 75)

    print("\n📋 1. ALLOCATION TABLE:")
    print("-" * 75)
    items_list = list(board["inventory"].keys())
    header_str = f"{'Zone':<14} | {'Tier':<22} | " + " | ".join(f"{it[:6]:<6}" for it in items_list)
    print(header_str)
    print("-" * 75)

    for z, items in board["allocation"].items():
        tier = board["needs"][z]["tier"]
        row_str = f"{z:<14} | {tier:<22} | " + " | ".join(f"{items.get(it, 0):<6}" for it in items_list)
        print(row_str)

    print("\n🚚 2. ROUTE & DISPATCH PLAN:")
    print("-" * 75)
    for z, r in board["routes"].items():
        print(f"• {z:<14} -> Distance: {r['distance_km']} km | Est. Transit: {r['transit_hours']} hrs | {r['dispatch_priority']} ({r['mode']})")

    print("\n⚖️ 3. FAIRNESS AUDIT NOTE:")
    print("-" * 75)
    print(f"Status : {board['fairness_audit']['verdict']}")
    print(f"Details: {board['fairness_audit']['notes']}")
    print("=" * 75 + "\n")

def run_cli_mission(inv_tool: InventoryTool):
    print("\n" + "-" * 75)
    print("📝 CLI FIELD SITUATION INPUT")
    print("-" * 75)
    print("Enter zone situations (or press Enter on zone name when finished).")

    zones = {}
    default_zones = [
        ("Zone South", "CRITICAL: Flooding, 75 casualties, drinking water contaminated, homes collapsed."),
        ("Zone East", "MODERATE: 250 people displaced in temporary shelters, food shortages."),
        ("Zone North", "LOW: Minor localized road flooding, self-sufficient, no casualties.")
    ]

    use_defaults = input("Use standard scenario (Zone South/East/North)? (Y/n) [Default: Y]: ").strip().lower()
    if use_defaults not in ["n", "no"]:
        for name, rep in default_zones:
            zones[name] = rep
    else:
        idx = 1
        while True:
            try:
                name = input(f"\nZone {idx} Name (leave empty to finish): ").strip()
                if not name:
                    break
                report = input(f"  Situation Report for {name}: ").strip()
                reqs = input(f"  Field Requirements / Needed Supplies: ").strip()
                cas_str = input(f"  Casualties count [0]: ").strip()
                dist_str = input(f"  Distance in km [50]: ").strip()

                zones[name] = {
                    "report": report,
                    "requirements": reqs,
                    "casualties": int(cas_str or 0),
                    "distance_km": int(dist_str or 50)
                }
                idx += 1
            except (EOFError, KeyboardInterrupt):
                break

    if not zones:
        print("No zones provided. Using standard baseline scenario.")
        zones = dict(default_zones)

    log_tool = LogisticsTool()
    coordinator = ReliefCoordinator(
        NeedsAssessmentAgent(),
        InventoryAgent(inv_tool),
        LogisticsAgent(log_tool),
        FairnessAuditorAgent()
    )

    board = coordinator.coordinate(zones, inv_tool.get_stock())
    print_allocation_output(board, "AGENTIC DISASTER RELIEF ALLOCATION")

def start_web_frontend(port: int = 5000):
    from app import app
    url = f"http://127.0.0.1:{port}"
    print("\n" + "=" * 75)
    print("🌐 FIELD USER WEB FRONTEND READY")
    print("=" * 75)
    print(f"👉 Application URL: {url}")
    print("   Open the URL in your browser to enter situations and field requirements.")
    print("   The AI agents will evaluate need scores, audit fairness, and allocate stock.")
    print("   Press Ctrl+C to stop the server.")
    print("=" * 75 + "\n")

    try:
        webbrowser.open(url)
    except Exception:
        pass

    app.run(host="127.0.0.1", port=port, debug=False)

def main():
    print_banner()

    inv_tool = InventoryTool()

    # Check CLI arguments
    if "--server" in sys.argv:
        start_web_frontend()
        return

    if "--eval" in sys.argv:
        import evaluate
        evaluate.run_evaluation()
        return

    if "--cli" in sys.argv:
        prompt_inventory_update(inv_tool)
        run_cli_mission(inv_tool)
        return

    # Step 1: Ask deployer for inventory updates
    prompt_inventory_update(inv_tool)

    # Step 2: Choose execution mode
    print("\n🚀 Select execution mode:")
    print("  [1] Launch Web Frontend for Field Users (Recommended - Default)")
    print("  [2] Enter Situation Reports & Requirements via Terminal (CLI Mode)")
    print("  [3] Run Evaluation Benchmarks (5 Scenarios & Guardrail Tests)")

    try:
        mode = input("\nEnter choice [1]: ").strip()
    except (EOFError, KeyboardInterrupt):
        mode = "1"

    if mode == "2":
        run_cli_mission(inv_tool)
    elif mode == "3":
        import evaluate
        evaluate.run_evaluation()
    else:
        start_web_frontend()

if __name__ == "__main__":
    main()
