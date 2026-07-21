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
            timeout = kwargs.get("timeout", 10)

            if query_type == "overview":
                response = requests.get(
                    "https://l2beat.com/api/scaling/summary",
                    timeout=timeout,
                )
                response.raise_for_status()
                return response.json()

            elif query_type == "activity":
                response = requests.get(
                    "https://l2beat.com/api/scaling/activity",
                    timeout=timeout,
                )
                response.raise_for_status()
                return response.json()

            else:
                response = requests.get(
                    "https://l2beat.com/api/scaling/summary",
                    timeout=timeout,
                )
                response.raise_for_status()
                return response.json()

        except Exception as error:
            return self._mock_fallback(query_type, **kwargs)

    def parse_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        if raw_data.get("fallback"):
            return raw_data

        projects = raw_data.get("projects", raw_data)

        if isinstance(projects, dict) and "data" in projects:
            projects = projects["data"]

        parsed_projects = []

        if isinstance(projects, dict):
            items = projects.values()
        elif isinstance(projects, list):
            items = projects
        else:
            items = []

        for project in items:
            if not isinstance(project, dict):
                continue

            tvs_data = project.get("tvs", {})
            tvs_breakdown = tvs_data.get("breakdown", {}) if isinstance(tvs_data, dict) else {}
            tvl = tvs_breakdown.get("total", 0) if isinstance(tvs_breakdown, dict) else 0

            parsed_projects.append({
                "name": project.get("name", ""),
                "slug": project.get("slug", ""),
                "category": project.get("category", "other"),
                "stage": project.get("stage", ""),
                "type": project.get("type", ""),
                "host_chain": project.get("hostChain", ""),
                "tvl_usd": tvl,
                "change_7d_tvl_pct": (tvs_data.get("change7d", 0) or 0) * 100 if isinstance(tvs_data, dict) else 0,
                "purposes": project.get("purposes", []),
                "providers": project.get("providers", []),
            })

        parsed_projects.sort(key=lambda x: x.get("tvl_usd", 0) or 0, reverse=True)

        total_tvl = sum(p.get("tvl_usd", 0) or 0 for p in parsed_projects)

        for p in parsed_projects[:50]:
            p["market_share_pct"] = round((p.get("tvl_usd", 0) / total_tvl * 100), 2) if total_tvl > 0 else 0

        return {
            "source": "L2Beat",
            "project_count": len(parsed_projects),
            "total_tvl_usd": total_tvl,
            "projects": parsed_projects[:50],
            "dominance": [
                {"name": p["name"], "share_pct": p.get("market_share_pct", 0)}
                for p in parsed_projects[:5]
            ],
            "parsed_at": datetime.now().isoformat(),
        }
