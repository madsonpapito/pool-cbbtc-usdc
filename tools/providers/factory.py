from typing import Dict, Any, Type
from tools.providers.base_provider import BaseProvider
from tools.providers.uniswap_v3_provider import UniswapV3Provider
from tools.providers.byreal_provider import ByRealProvider

class ProviderFactory:
    """
    Registry and factory for specialized pool providers.
    """
    
    _providers: Dict[str, Type[BaseProvider]] = {
        "uniswap_v3": UniswapV3Provider,
        "byreal": ByRealProvider
    }

    @classmethod
    def create(cls, config: Dict[str, Any]) -> BaseProvider:
        exchange = config.get("exchange", "uniswap_v3")
        provider_class = cls._providers.get(exchange)
        
        if not provider_class:
            raise ValueError(f"No provider found for exchange: {exchange}")
            
        return provider_class(config)
