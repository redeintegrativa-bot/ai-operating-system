from datetime import datetime
from typing import Any, Dict, List, Optional
from src.providers.base_provider import BaseDefiProvider


class L2BeatProvider(BaseDefiProvider):
    cache_timeout_seconds: int = 600

    def get_name(self) -> str:
        return "l2beat"

    def fetch_data(self, **kwargs) -> Dict[str, Any]:
        query_type = kwargs.get("query_type", "overview")
        try:
            import requests
            base_url = "https://api.l2beat.com/v1"

            if query_type == "overview":
                response = requests.get(
                    f"{base_url}/scaling/overview",
                    timeout=kwargs.get("timeout", 10),
                )
                response.raise_for_status()
                return response.json()

            elif query_type == "status":
                response = requests.get(
                    f"{base_url}/scaling/status",
                    timeout=kwargs.get("timeout", 10),
                )
                response.raise_for_status()
                return response.json()

            elif query_type == "tvl":
                response = requests.get(
                    f"{base_url}/scaling/tvl",
                    timeout=kwargs.get("timeout", 10),
                )
                response.raise_for_status()
                return response.json()

            elif query_type == "activity":
                response = requests.get(
                    f"{base_url}/scaling/activity",
                    timeout=kwargs.get("timeout", 10),
                )
                response.raise_for_status()
                return response.json()

            else:
                response = requests.get(
                    f"{base_url}/scaling/overview",
                    timeout=kwargs.get("timeout", 10),
                )
                response.raise_for_status()
                return response.json()

        except Exception as error:
            return self._mock_fallback(query_type, **kwargs)

    def parse_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        if raw_data.get("fallback"):
            return raw_data

        projects = raw_data.get("data", raw_data)
        if isinstance(projects, dict):
            projects = projects.get("projects", [])
        if isinstance(projects, dict):
            projects = list(projects.values())

        parsed_projects = []
        if isinstance(projects, list):
            for project in projects[:50]:
                if isinstance(project, dict):
                    parsed_projects.append({
                        "name": project.get("name", ""),
                        "slug": project.get("slug", ""),
                        "category": project.get("category", "other"),
                        "stage": project.get("stage", ""),
                        "tvl_usd": project.get("tvl", project.get("totalTvl", 0)),
                        "market_share_pct": project.get("marketShare", 0),
                        "purpose": project.get("purpose", ""),
                        "technology": project.get("technology", ""),
                        "da_layer": project.get("daLayer", project.get("dataAvailability", "")),
                        "transactions_30d": project.get("activity", {}).get("transactions30d", 0),
                        "change_7d_tvl_pct": project.get("change_7d", 0),
                    })

        total_tvl = sum(p.get("tvl_usd", 0) or 0 for p in parsed_projects)
        total_tx_30d = sum(p.get("transactions_30d", 0) or 0 for p in parsed_projects)

        return {
            "source": "L2Beat",
            "project_count": len(parsed_projects),
            "total_tvl_usd": total_tvl,
            "total_transactions_30d": total_tx_30d,
            "projects": parsed_projects,
            "dominance": [
                {"name": p["name"], "share_pct": round((p.get("tvl_usd", 0) / total_tvl * 100), 2) if total_tvl > 0 else 0}
                for p in sorted(parsed_projects, key=lambda x: x.get("tvl_usd", 0) or 0, reverse=True)[:5]
            ],
            "parsed_at": datetime.now().isoformat(),
        }
