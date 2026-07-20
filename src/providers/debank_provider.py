from datetime import datetime
from typing import Any, Dict, List, Optional
from src.providers.base_provider import BaseDefiProvider


class DeBankProvider(BaseDefiProvider):
    def get_name(self) -> str:
        return "debank"

    def fetch_data(self, **kwargs) -> Dict[str, Any]:
        query_type = kwargs.get("query_type", "portfolio")
        try:
            import requests
            base_url = "https://api.debank.com"

            if query_type == "portfolio":
                user_address = kwargs.get("user_address", "")
                response = requests.get(
                    f"{base_url}/portfolio/total",
                    params={"user_addr": user_address},
                    timeout=kwargs.get("timeout", 10),
                )
                response.raise_for_status()
                return response.json()

            elif query_type == "token_list":
                user_address = kwargs.get("user_address", "")
                chain = kwargs.get("chain", "eth")
                response = requests.get(
                    f"{base_url}/token/list",
                    params={"user_addr": user_address, "chain": chain},
                    timeout=kwargs.get("timeout", 10),
                )
                response.raise_for_status()
                return response.json()

            elif query_type == "protocol_list":
                user_address = kwargs.get("user_address", "")
                chain = kwargs.get("chain", "eth")
                response = requests.get(
                    f"{base_url}/protocol/list",
                    params={"user_addr": user_address, "chain": chain},
                    timeout=kwargs.get("timeout", 10),
                )
                response.raise_for_status()
                return response.json()

            elif query_type == "nft_list":
                user_address = kwargs.get("user_address", "")
                response = requests.get(
                    f"{base_url}/nft/list",
                    params={"user_addr": user_address},
                    timeout=kwargs.get("timeout", 10),
                )
                response.raise_for_status()
                return response.json()

            elif query_type == "history":
                user_address = kwargs.get("user_address", "")
                chain = kwargs.get("chain", "eth")
                response = requests.get(
                    f"{base_url}/history/list",
                    params={"user_addr": user_address, "chain": chain},
                    timeout=kwargs.get("timeout", 10),
                )
                response.raise_for_status()
                return response.json()

            else:
                response = requests.get(
                    f"{base_url}/portfolio/total",
                    params={"user_addr": kwargs.get("user_address", "")},
                    timeout=kwargs.get("timeout", 10),
                )
                response.raise_for_status()
                return response.json()

        except Exception as error:
            return self._mock_fallback(query_type, **kwargs)

    def parse_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        if raw_data.get("fallback"):
            return raw_data

        total_usd_value = raw_data.get("data", {}).get("total_usd_value", 0)
        if not total_usd_value:
            total_usd_value = raw_data.get("total_usd_value", 0)

        chain_totals = raw_data.get("data", {}).get("chain_list", [])
        if not chain_totals:
            chain_totals = raw_data.get("chain_list", [])

        parsed_chains = []
        for chain in chain_totals:
            parsed_chains.append({
                "chain_id": chain.get("id", ""),
                "usd_value": chain.get("usd_value", 0),
                "token_count": chain.get("token_count", 0),
            })

        return {
            "source": "DeBank",
            "query_type": "portfolio",
            "total_usd_value": total_usd_value,
            "chain_breakdown": parsed_chains,
            "parsed_at": datetime.now().isoformat(),
        }


class DeBankProtocolListProvider(DeBankProvider):
    def get_name(self) -> str:
        return "debank_protocols"

    def fetch_data(self, **kwargs) -> Dict[str, Any]:
        try:
            import requests
            user_address = kwargs.get("user_address", "")
            response = requests.get(
                "https://api.debank.com/protocol/list",
                params={"user_addr": user_address},
                timeout=kwargs.get("timeout", 10),
            )
            response.raise_for_status()
            return response.json()
        except Exception as error:
            return self._mock_fallback("protocol_list", **kwargs)

    def parse_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        if raw_data.get("fallback"):
            return raw_data

        protocols = raw_data.get("data", [])
        if not protocols:
            protocols = raw_data.get("protocols", [])

        parsed_protocols = []
        for protocol in protocols:
            parsed_protocols.append({
                "protocol_id": protocol.get("id", ""),
                "name": protocol.get("name", ""),
                "chain": protocol.get("chain", ""),
                "portfolio_item_list": protocol.get("portfolio_item_list", []),
                "usd_value": sum(
                    item.get("stats", {}).get("net_usd_value", 0)
                    for item in protocol.get("portfolio_item_list", [])
                ),
            })

        total_usd = sum(p.get("usd_value", 0) for p in parsed_protocols)

        return {
            "source": "DeBank Protocols",
            "protocol_count": len(parsed_protocols),
            "protocols": sorted(parsed_protocols, key=lambda x: x.get("usd_value", 0), reverse=True),
            "total_usd_value": total_usd,
            "parsed_at": datetime.now().isoformat(),
        }
