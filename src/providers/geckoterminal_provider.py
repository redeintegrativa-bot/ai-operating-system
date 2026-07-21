from datetime import datetime
from typing import Any, Dict, List, Optional
from src.providers.base_provider import BaseDefiProvider


CHAIN_MAP = {
    "ethereum": "eth",
    "bsc": "bsc",
    "polygon": "polygon",
    "arbitrum": "arbitrum",
    "avalanche": "avax",
    "optimism": "optimism",
    "base": "base",
    "solana": "solana",
}


class GeckoTerminalProvider(BaseDefiProvider):
    cache_timeout_seconds: int = 120

    def _resolve_chain(self, chain: str) -> str:
        return CHAIN_MAP.get(chain.lower(), chain.lower())

    def get_name(self) -> str:
        return "geckoterminal"

    def fetch_data(self, **kwargs) -> Dict[str, Any]:
        query_type = kwargs.get("query_type", "trending_pools")
        try:
            import requests
            base_url = "https://api.geckoterminal.com/api/v2"

            if query_type == "trending_pools":
                chain = self._resolve_chain(kwargs.get("chain", "ethereum"))
                response = requests.get(
                    f"{base_url}/networks/{chain}/trending_pools",
                    timeout=kwargs.get("timeout", 10),
                )
                response.raise_for_status()
                return response.json()

            elif query_type == "ohlcv":
                chain = self._resolve_chain(kwargs.get("chain", "ethereum"))
                pool_address = kwargs.get("pool_address", "")
                timeframe = kwargs.get("timeframe", "day")
                response = requests.get(
                    f"{base_url}/networks/{chain}/pools/{pool_address}/ohlcv/{timeframe}",
                    timeout=kwargs.get("timeout", 10),
                )
                response.raise_for_status()
                return response.json()

            elif query_type == "pool_info":
                chain = self._resolve_chain(kwargs.get("chain", "ethereum"))
                pool_address = kwargs.get("pool_address", "")
                response = requests.get(
                    f"{base_url}/networks/{chain}/pools/{pool_address}",
                    timeout=kwargs.get("timeout", 10),
                )
                response.raise_for_status()
                return response.json()

            elif query_type == "simple_price":
                network = self._resolve_chain(kwargs.get("network", "ethereum"))
                addresses = kwargs.get("addresses", "")
                response = requests.get(
                    f"{base_url}/simple/networks/{network}/token_price/{addresses}",
                    timeout=kwargs.get("timeout", 10),
                )
                response.raise_for_status()
                return response.json()

            elif query_type == "top_pools":
                chain = self._resolve_chain(kwargs.get("chain", "ethereum"))
                response = requests.get(
                    f"{base_url}/networks/{chain}/pools",
                    timeout=kwargs.get("timeout", 10),
                )
                response.raise_for_status()
                return response.json()

            else:
                chain = self._resolve_chain(kwargs.get("chain", "ethereum"))
                response = requests.get(
                    f"{base_url}/networks/{chain}/trending_pools",
                    timeout=kwargs.get("timeout", 10),
                )
                response.raise_for_status()
                return response.json()

        except Exception as error:
            return self._mock_fallback(query_type, **kwargs)

    def parse_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        if raw_data.get("fallback"):
            return raw_data

        data = raw_data.get("data", raw_data)

        if isinstance(data, dict) and "attributes" in data:
            attributes = data.get("attributes", {})
            return {
                "source": "GeckoTerminal",
                "query_type": "pool_detail",
                "pool": {
                    "name": attributes.get("name", ""),
                    "base_token_price_usd": attributes.get("base_token_price_usd", "0"),
                    "quote_token_price_usd": attributes.get("quote_token_price_usd", "0"),
                    "reserve_in_usd": attributes.get("reserve_in_usd", "0"),
                    "volume_usd_24h": attributes.get("volume_usd", {}).get("h24", "0"),
                    "price_change_24h_pct": attributes.get("price_change_percentage", {}).get("h24", 0),
                    "transactions_24h": attributes.get("transactions", {}).get("h24", 0),
                    "pool_created_at": attributes.get("pool_created_at", ""),
                },
                "parsed_at": datetime.now().isoformat(),
            }

        pools = []
        if isinstance(data, list):
            items = data
        else:
            items = data if isinstance(data, list) else data.get("data", [])

        for item in items[:50]:
            attributes = item.get("attributes", {})
            pools.append({
                "name": attributes.get("name", ""),
                "base_token_price_usd": attributes.get("base_token_price_usd", "0"),
                "quote_token_price_usd": attributes.get("quote_token_price_usd", "0"),
                "reserve_in_usd": attributes.get("reserve_in_usd", "0"),
                "volume_usd_24h": attributes.get("volume_usd", {}).get("h24", "0"),
                "price_change_24h_pct": attributes.get("price_change_percentage", {}).get("h24", 0),
                "transactions_24h": attributes.get("transactions", {}).get("h24", 0),
                "network": item.get("relationships", {}).get("network", {}).get("data", {}).get("id", ""),
                "dex": item.get("relationships", {}).get("dex", {}).get("data", {}).get("id", ""),
            })

        return {
            "source": "GeckoTerminal",
            "query_type": "pools",
            "pool_count": len(pools),
            "pools": pools,
            "parsed_at": datetime.now().isoformat(),
        }
