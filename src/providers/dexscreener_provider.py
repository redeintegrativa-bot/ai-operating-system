from datetime import datetime
from typing import Any, Dict, List, Optional
from src.providers.base_provider import BaseDefiProvider


class DexScreenerProvider(BaseDefiProvider):
    def get_name(self) -> str:
        return "dexscreener"

    def fetch_data(self, **kwargs) -> Dict[str, Any]:
        query_type = kwargs.get("query_type", "search")
        try:
            import requests
            base_url = "https://api.dexscreener.com/latest/dex"

            if query_type == "search":
                query = kwargs.get("query", "")
                response = requests.get(
                    f"{base_url}/search",
                    params={"q": query},
                    timeout=kwargs.get("timeout", 10),
                )
                response.raise_for_status()
                return response.json()

            elif query_type == "pairs":
                chain = kwargs.get("chain", "ethereum")
                pair_address = kwargs.get("pair_address", "")
                response = requests.get(
                    f"{base_url}/pairs/{chain}/{pair_address}",
                    timeout=kwargs.get("timeout", 10),
                )
                response.raise_for_status()
                return response.json()

            elif query_type == "token_pairs":
                chain = kwargs.get("chain", "ethereum")
                token_address = kwargs.get("token_address", "")
                response = requests.get(
                    f"{base_url}/tokens/{token_address}",
                    timeout=kwargs.get("timeout", 10),
                )
                response.raise_for_status()
                return response.json()

            else:
                response = requests.get(
                    f"{base_url}/search",
                    params={"q": kwargs.get("query", "")},
                    timeout=kwargs.get("timeout", 10),
                )
                response.raise_for_status()
                return response.json()

        except Exception as error:
            return self._mock_fallback(query_type, **kwargs)

    def parse_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        if raw_data.get("fallback"):
            return raw_data

        pairs = raw_data.get("pairs", [])
        if not pairs:
            pairs = raw_data.get("pair", [])
        if isinstance(pairs, dict):
            pairs = [pairs]

        parsed_pairs = []
        for pair in pairs:
            parsed_pairs.append({
                "chain_id": pair.get("chainId", ""),
                "dex_id": pair.get("dexId", ""),
                "pair_address": pair.get("pairAddress", ""),
                "base_token": {
                    "symbol": pair.get("baseToken", {}).get("symbol", ""),
                    "name": pair.get("baseToken", {}).get("name", ""),
                    "address": pair.get("baseToken", {}).get("address", ""),
                },
                "quote_token": {
                    "symbol": pair.get("quoteToken", {}).get("symbol", ""),
                    "name": pair.get("quoteToken", {}).get("name", ""),
                    "address": pair.get("quoteToken", {}).get("address", ""),
                },
                "price_usd": pair.get("priceUsd", "0"),
                "volume_24h_usd": pair.get("volume", {}).get("h24", 0),
                "liquidity_usd": pair.get("liquidity", {}).get("usd", 0),
                "fdv_usd": pair.get("fdv", 0),
                "pair_created_at": pair.get("pairCreatedAt", 0),
                "txns_24h": {
                    "buys": pair.get("txns", {}).get("h24", {}).get("buys", 0),
                    "sells": pair.get("txns", {}).get("h24", {}).get("sells", 0),
                },
                "price_change_24h_pct": pair.get("priceChange", {}).get("h24", 0),
                "url": f"https://dexscreener.com/{pair.get('chainId', '')}/{pair.get('pairAddress', '')}",
            })

        return {
            "source": "DexScreener",
            "pair_count": len(parsed_pairs),
            "pairs": parsed_pairs,
            "total_volume_24h_usd": sum(float(p.get("volume_24h_usd", 0) or 0) for p in parsed_pairs),
            "total_liquidity_usd": sum(float(p.get("liquidity_usd", 0) or 0) for p in parsed_pairs),
            "parsed_at": datetime.now().isoformat(),
        }
