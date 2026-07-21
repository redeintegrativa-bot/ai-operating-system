from datetime import datetime
from typing import Any, Dict, List, Optional
from src.providers.base_provider import BaseDefiProvider


class CoinGeckoProvider(BaseDefiProvider):
    def get_name(self) -> str:
        return "coingecko"

    def fetch_data(self, **kwargs) -> Dict[str, Any]:
        query_type = kwargs.get("query_type", "price")
        try:
            import requests
            base_url = "https://api.coingecko.com/api/v3"

            if query_type == "price":
                coin_id = kwargs.get("coin_id", "bitcoin")
                response = requests.get(
                    f"{base_url}/simple/price",
                    params={
                        "ids": coin_id,
                        "vs_currencies": "usd",
                        "include_24hr_vol": "true",
                        "include_24hr_change": "true",
                        "include_market_cap": "true",
                    },
                    timeout=kwargs.get("timeout", 10),
                )
                response.raise_for_status()
                return response.json()

            elif query_type == "coin_markets":
                vs_currency = kwargs.get("vs_currency", "usd")
                category = kwargs.get("category", "")
                params = {
                    "vs_currency": vs_currency,
                    "order": "market_cap_desc",
                    "per_page": kwargs.get("limit", 50),
                    "page": 1,
                    "sparkline": "false",
                }
                if category:
                    params["category"] = category
                response = requests.get(
                    f"{base_url}/coins/markets",
                    params=params,
                    timeout=kwargs.get("timeout", 10),
                )
                response.raise_for_status()
                return response.json()

            elif query_type == "trending":
                response = requests.get(
                    f"{base_url}/search/trending",
                    timeout=kwargs.get("timeout", 10),
                )
                response.raise_for_status()
                return response.json()

            elif query_type == "categories":
                response = requests.get(
                    f"{base_url}/coins/categories",
                    timeout=kwargs.get("timeout", 10),
                )
                response.raise_for_status()
                return response.json()

            else:
                coin_id = kwargs.get("coin_id", "bitcoin")
                response = requests.get(
                    f"{base_url}/coins/{coin_id}",
                    params={
                        "localization": "false",
                        "tickers": "false",
                        "community_data": "false",
                        "developer_data": "false",
                    },
                    timeout=kwargs.get("timeout", 10),
                )
                response.raise_for_status()
                return response.json()

        except Exception as error:
            return self._mock_fallback(query_type, coin_id=kwargs.get("coin_id", "bitcoin"))

    def parse_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        if isinstance(raw_data, dict) and raw_data.get("fallback"):
            return raw_data

        if isinstance(raw_data, dict) and any(key in raw_data for key in ["bitcoin", "ethereum"]):
            results = []
            for coin_id, data in raw_data.items():
                results.append({
                    "coin_id": coin_id,
                    "price_usd": data.get("usd", 0),
                    "market_cap_usd": data.get("usd_market_cap", 0),
                    "volume_24h_usd": data.get("usd_24h_vol", 0),
                    "change_24h_pct": data.get("usd_24h_change", 0),
                })
            return {
                "source": "CoinGecko",
                "query_type": "price",
                "results": results,
                "parsed_at": datetime.now().isoformat(),
            }

        if isinstance(raw_data, list):
            tokens = []
            for item in raw_data:
                tokens.append({
                    "coin_id": item.get("id", ""),
                    "symbol": item.get("symbol", ""),
                    "name": item.get("name", ""),
                    "current_price_usd": item.get("current_price", 0),
                    "market_cap_usd": item.get("market_cap", 0),
                    "volume_24h_usd": item.get("total_volume", 0),
                    "price_change_24h_pct": item.get("price_change_percentage_24h", 0),
                    "circulating_supply": item.get("circulating_supply", 0),
                    "total_supply": item.get("total_supply", 0),
                    "max_supply": item.get("max_supply", 0),
                    "ath_usd": item.get("ath", 0),
                    "ath_date": item.get("ath_date", ""),
                })

            total_market_cap = sum(t.get("market_cap_usd", 0) or 0 for t in tokens)

            return {
                "source": "CoinGecko",
                "query_type": "market_data",
                "token_count": len(tokens),
                "total_market_cap_usd": total_market_cap,
                "tokens": tokens,
                "parsed_at": datetime.now().isoformat(),
            }

        return raw_data


class CoinGeckoCategoriesProvider(CoinGeckoProvider):
    def get_name(self) -> str:
        return "coingecko_categories"

    def fetch_data(self, **kwargs) -> Dict[str, Any]:
        try:
            import requests
            response = requests.get(
                "https://api.coingecko.com/api/v3/coins/categories",
                timeout=kwargs.get("timeout", 10),
            )
            response.raise_for_status()
            return response.json()
        except Exception as error:
            return self._mock_fallback("categories", **kwargs)

    def parse_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        if raw_data.get("fallback"):
            return raw_data

        categories = []
        for item in raw_data:
            categories.append({
                "category_id": item.get("id", ""),
                "name": item.get("name", ""),
                "market_cap_usd": item.get("market_cap", 0),
                "volume_24h_usd": item.get("volume_24h", 0),
                "market_cap_change_24h_pct": item.get("market_cap_change_24h", 0),
                "top_coin": item.get("top_coin", ""),
                "token_count": item.get("token_count", 0),
            })

        return {
            "source": "CoinGecko Categories",
            "category_count": len(categories),
            "categories": categories,
            "parsed_at": datetime.now().isoformat(),
        }
