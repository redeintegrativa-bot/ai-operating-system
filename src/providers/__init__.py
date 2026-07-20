from .base_provider import BaseDefiProvider, ProviderResponse
from .defillama_provider import DefiLlamaProvider
from .coingecko_provider import CoinGeckoProvider
from .dexscreener_provider import DexScreenerProvider
from .geckoterminal_provider import GeckoTerminalProvider
from .debank_provider import DeBankProvider
from .l2beat_provider import L2BeatProvider

AVAILABLE_PROVIDERS = {
    "defillama": DefiLlamaProvider,
    "coingecko": CoinGeckoProvider,
    "dexscreener": DexScreenerProvider,
    "geckoterminal": GeckoTerminalProvider,
    "debank": DeBankProvider,
    "l2beat": L2BeatProvider,
}

def get_provider(provider_name: str) -> BaseDefiProvider:
    provider_class = AVAILABLE_PROVIDERS.get(provider_name.lower())
    if provider_class is None:
        raise ValueError(f"Unknown provider: {provider_name}. Available: {list(AVAILABLE_PROVIDERS.keys())}")
    return provider_class()

def get_all_providers() -> dict:
    return {name: cls() for name, cls in AVAILABLE_PROVIDERS.items()}

__all__ = [
    "BaseDefiProvider",
    "ProviderResponse",
    "DefiLlamaProvider",
    "CoinGeckoProvider",
    "DexScreenerProvider",
    "GeckoTerminalProvider",
    "DeBankProvider",
    "L2BeatProvider",
    "get_provider",
    "get_all_providers",
]
