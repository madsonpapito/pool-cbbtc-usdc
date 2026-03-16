from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseProvider(ABC):
    """
    Base class for liquidity pool data providers.
    All providers (Uniswap V3, ByReal, etc.) must implement these methods.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.nft_id = config.get("nft_id")
        self.network = config.get("network", "base")
        self.exchange = config.get("exchange", "uniswap_v3")

    @abstractmethod
    def fetch_position_data(self) -> Optional[Dict[str, Any]]:
        """
        Fetch real-time position data (liquidity, current prices, in-range status).
        Returns a dictionary compatible with the dashboard expectations.
        """
        pass

    @abstractmethod
    def fetch_fees_data(self) -> Optional[Dict[str, Any]]:
        """
        Fetch historical collected fees and events.
        """
        pass

    def get_pool_dir(self) -> str:
        """Helper to get the directory for this pool's data."""
        return f"tools/pools/{self.nft_id}"
