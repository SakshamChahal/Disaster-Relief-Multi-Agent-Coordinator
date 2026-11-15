from typing import Dict, Any, List, Optional

class Blackboard:
    def __init__(self, zone_reports: Dict[str, str], stock: Dict[str, int] = None):
        self.state: Dict[str, Any] = {
            "zone_reports": dict(zone_reports),
            "needs": {},
            "inventory": dict(stock) if stock else {},
            "allocation": {},
            "routes": {},
            "fairness_audit": {},
            "history": []
        }

    def set(self, key: str, value: Any) -> None:
        self.state[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self.state.get(key, default)

    def log_event(self, event: str) -> None:
        self.state["history"].append(event)

    def snapshot(self) -> Dict[str, Any]:
        return self.state

class ConversationCache:
    def __init__(self):
        self._query_cache: Dict[str, Any] = {}
        self._chat_history: List[Dict[str, str]] = []

    def get(self, query: str) -> Optional[Any]:
        key = query.strip().lower()
        return self._query_cache.get(key)

    def set(self, query: str, response: Any) -> None:
        key = query.strip().lower()
        self._query_cache[key] = response

    def add_turn(self, role: str, message: str) -> None:
        self._chat_history.append({"role": role, "message": message})

    def get_history(self) -> List[Dict[str, str]]:
        return list(self._chat_history)
