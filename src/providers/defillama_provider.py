from datetime import datetime
from typing import Any, Dict, List, Optional
from src.providers.base_provider import BaseDefiProvider


class DefiLlamaProvider(BaseDefiProvider):
    def get_name(self) -> str:
        return "defillama"

    def fetch_data(self, **kwargs) -> Dict[str, Any]:
        query_type = kwargs.get("query_type", "overview")
        try:
            import requests
            base_url = "https://api.llama.fi"
            if query_type == "overview":
                response = requests.get(f"{base_url}/overview/ethereum", timeout=kwargs.get("timeout", 10))
                response.raise_for_status()
                return response.json()
            elif query_type == "yields":
                response = requests.get(f"{base_url}/pools", timeout=kwargs.get("timeout", 10))
                response.raise_for_status()
                return response.json()
            elif query_type == "protocol":
                protocol = kwargs.get("protocol", "")
                response = requests.get(f"{base_url}/protocol/{protocol}", timeout=kwargs.get("timeout", 10))
                response.raise_for_status()
                return response.json()
            elif query_type == "chains":
                response = requests.get(f"{base_url}/chains", timeout=kwargs.get("timeout", 10))
                response.raise_for_status()
                return response.json()
            elif query_type == "protocols":
                response = requests.get(f"{base_url}/protocols", timeout=kwargs.get("timeout", 15))
                response.raise_for_status()
                return response.json()
            else:
                response = requests.get(f"{base_url}/overview/ethereum", timeout=kwargs.get("timeout", 10))
                response.raise_for_status()
                return response.json()
        except Exception as error:
            return self._mock_fallback(query_type, **kwargs)

    def parse_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        if raw_data.get("fallback"):
            return raw_data

        protocols = []
        if isinstance(raw_data, list):
            for item in raw_data:
                protocols.append({
                    "name": item.get("name", ""),
                    "tvl_usd": item.get("tvl", 0),
                    "change_1d": item.get("change_1d", 0),
                    "change_7d": item.get("change_7d", 0),
                    "chain": item.get("chain", "ethereum"),
                    "category": item.get("category", "other"),
                    "symbol": item.get("symbol", ""),
                })
        elif isinstance(raw_data, dict) and "tvl" in raw_data:
            protocols.append({
                "name": raw_data.get("name", ""),
                "tvl_usd": raw_data.get("tvl", 0),
                "change_1d": raw_data.get("change_1d", 0),
                "change_7d": raw_data.get("change_7d", 0),
                "chain": raw_data.get("chain", "ethereum"),
                "category": raw_data.get("category", "other"),
                "symbol": raw_data.get("symbol", ""),
            })

        total_tvl = sum(p.get("tvl_usd", 0) or 0 for p in protocols)

        top_protocols = sorted(protocols, key=lambda x: x.get("tvl_usd", 0) or 0, reverse=True)[:20]

        return {
            "source": "DefiLlama",
            "total_tvl_usd": total_tvl,
            "protocol_count": len(protocols),
            "top_protocols": top_protocols,
            "dominance": [
                {"name": p["name"], "share_pct": round((p.get("tvl_usd", 0) / total_tvl * 100), 2) if total_tvl > 0 else 0}
                for p in top_protocols[:5]
            ],
            "parsed_at": datetime.now().isoformat(),
        }


class DefiLlamaYieldsProvider(DefiLlamaProvider):
    def get_name(self) -> str:
        return "defillama_yields"

    def fetch_data(self, **kwargs) -> Dict[str, Any]:
        try:
            import requests
            response = requests.get("https://yields.llama.fi/pools", timeout=kwargs.get("timeout", 10))
            response.raise_for_status()
            return response.json()
        except Exception as error:
            return self._mock_fallback("yields", **kwargs)

    def parse_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        if raw_data.get("fallback"):
            return raw_data

        pools = raw_data.get("data", [])
        if not pools:
            pools = raw_data.get("pools", [])

        parsed_pools = []
        for pool in pools[:100]:
            parsed_pools.append({
                "pool": pool.get("pool", ""),
                "chain": pool.get("chain", ""),
                "project": pool.get("project", ""),
                "symbol": pool.get("symbol", ""),
                "tvl_usd": pool.get("tvlUsd", 0),
                "apy_base": pool.get("apyBase", 0),
                "apy_reward": pool.get("apyReward", 0),
                "apy_total": pool.get("apy", pool.get("apyBase", 0)),
                "apy_7d": pool.get("apyBase7d", 0),
                "apy_30d": pool.get("apyBase30d", 0),
                "il_risk": pool.get("ilRisk", "no"),
            })

        top_yield = sorted(parsed_pools, key=lambda x: x.get("apy_total", 0), reverse=True)[:10]

        return {
            "source": "DefiLlama Yields",
            "pool_count": len(parsed_pools),
            "top_yields": top_yield,
            "average_apy": round(sum(p.get("apy_total", 0) for p in parsed_pools) / len(parsed_pools), 2) if parsed_pools else 0,
            "total_tvl_usd": sum(p.get("tvl_usd", 0) for p in parsed_pools),
            "parsed_at": datetime.now().isoformat(),
        }
