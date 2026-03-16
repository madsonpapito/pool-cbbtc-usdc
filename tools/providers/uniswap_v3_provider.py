import requests
import json
import os
from decimal import Decimal, getcontext
from datetime import datetime
from typing import Dict, Any, Optional
from tools.providers.base_provider import BaseProvider

# Set high precision for V3 math
getcontext().prec = 50

class UniswapV3Provider(BaseProvider):
    """
    Provider for Uniswap V3 pools on EVM chains (Base, Ethereum, etc).
    Initially ports logic from fetch_pool_data.py and fetch_collected_fees.py.
    """
    
    MANAGER_ADDRESS = "0x03a520b32C04BF3bEEf7BEb72E919cf822Ed34f1"
    FACTORY_ADDRESS = "0x33128a8fC17869897dcE68Ed026d694621f6FDfD"
    
    KNOWN_TOKENS = {
        "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913": {"symbol": "USDC", "decimals": 6},
        "0xcbb7c0000ab88b473b1f5afd9ef808440eed33bf": {"symbol": "cbBTC", "decimals": 8},
    }
    
    ABI_POSITIONS = "0x99fbab88"
    ABI_SLOT0 = "0x3850c7bd"
    ABI_GET_POOL = "0x1698ee82"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.rpc_url = config.get("rpc_url", os.getenv("RPC_URL", "https://mainnet.base.org"))
        self.token_id = int(self.nft_id)

    def _call_rpc(self, to_addr: str, data: str) -> Optional[str]:
        payload = {"jsonrpc": "2.0", "method": "eth_call", "params": [{"to": to_addr, "data": data}, "latest"], "id": 1}
        try:
            res = requests.post(self.rpc_url, json=payload, timeout=15)
            return res.json().get('result')
        except Exception as e:
            print(f"[{self.exchange}] RPC Error: {e}")
            return None

    def _signed_int24(self, hex_str: str) -> int:
        val = int(hex_str[-6:], 16)
        if val >= 2**23:
            return val - 2**24
        return val

    def _tick_to_sqrt_ratio(self, tick: int) -> Decimal:
        base = Decimal("1.0001")
        return base ** (Decimal(tick) / 2)

    def _get_amounts(self, liquidity, sqrt_price, tick_lower, tick_upper, current_tick):
        L = Decimal(liquidity)
        sqrt_ratio_a = self._tick_to_sqrt_ratio(tick_lower)
        sqrt_ratio_b = self._tick_to_sqrt_ratio(tick_upper)
        
        if current_tick < tick_lower:
            amount0 = L * (1/sqrt_ratio_a - 1/sqrt_ratio_b)
            amount1 = Decimal(0)
        elif current_tick >= tick_upper:
            amount0 = Decimal(0)
            amount1 = L * (sqrt_ratio_b - sqrt_ratio_a)
        else:
            amount0 = L * (1/sqrt_price - 1/sqrt_ratio_b)
            amount1 = L * (sqrt_price - sqrt_ratio_a)
        
        return float(amount0), float(amount1)

    def fetch_position_data(self) -> Optional[Dict[str, Any]]:
        # This mirrors the logic in fetch_pool_data.py but returns a dict
        print(f"[{self.exchange}] Fetching data for NFT #{self.token_id}...")
        
        data_str = self.ABI_POSITIONS + hex(self.token_id)[2:].zfill(64)
        res_pos = self._call_rpc(self.MANAGER_ADDRESS, data_str)
        
        if not res_pos or res_pos == "0x":
            return None

        raw = res_pos[2:]
        words = [raw[i:i+64] for i in range(0, len(raw), 64)]
        
        token0_addr = "0x" + words[2][-40:].lower()
        token1_addr = "0x" + words[3][-40:].lower()
        fee = int(words[4], 16)
        tick_lower = self._signed_int24(words[5])
        tick_upper = self._signed_int24(words[6])
        liquidity = int(words[7], 16)
        tokens_owed0 = int(words[10], 16)
        tokens_owed1 = int(words[11], 16)

        t0_info = self.KNOWN_TOKENS.get(token0_addr, {"symbol": "Token0", "decimals": 18})
        t1_info = self.KNOWN_TOKENS.get(token1_addr, {"symbol": "Token1", "decimals": 18})
        
        symbol0, dec0 = t0_info["symbol"], t0_info["decimals"]
        symbol1, dec1 = t1_info["symbol"], t1_info["decimals"]

        # 2. Pool address & Current Tick
        padded_t0 = token0_addr[2:].zfill(64)
        padded_t1 = token1_addr[2:].zfill(64)
        padded_fee = hex(fee)[2:].zfill(64)
        data_pool = self.ABI_GET_POOL + padded_t0 + padded_t1 + padded_fee
        res_pool = self._call_rpc(self.FACTORY_ADDRESS, data_pool)
        
        if res_pool and res_pool != "0x" and len(res_pool) > 42:
            pool_address = "0x" + res_pool[-40:]
            res_slot0 = self._call_rpc(pool_address, self.ABI_SLOT0)
            if res_slot0 and len(res_slot0) > 130:
                slot0_raw = res_slot0[2:]
                sqrt_price_x96 = int(slot0_raw[:64], 16)
                current_tick = self._signed_int24(slot0_raw[64:128])
                sqrt_price = Decimal(sqrt_price_x96) / Decimal(2**96)
            else:
                current_tick = (tick_lower + tick_upper) // 2
                sqrt_price = self._tick_to_sqrt_ratio(current_tick)
        else:
            current_tick = (tick_lower + tick_upper) // 2
            sqrt_price = self._tick_to_sqrt_ratio(current_tick)

        in_range = tick_lower <= current_tick < tick_upper
        amount0_raw, amount1_raw = self._get_amounts(liquidity, sqrt_price, tick_lower, tick_upper, current_tick)
        amount0 = amount0_raw / (10 ** dec0)
        amount1 = amount1_raw / (10 ** dec1)
        
        price_t0_in_t1 = float(Decimal("1.0001") ** Decimal(current_tick))
        price_t0_in_t1 *= 10 ** (dec0 - dec1)
        
        price_cbbtc = 1 / price_t0_in_t1 if price_t0_in_t1 != 0 else 0
        
        if symbol0 == "USDC":
            value_usd = amount0 * 1.0 + amount1 * price_cbbtc
            fees_usd = (tokens_owed0 / 1e6) * 1.0 + (tokens_owed1 / 1e8) * price_cbbtc
        else:
            value_usd = amount0 * price_cbbtc + amount1 * 1.0
            fees_usd = (tokens_owed0 / 1e8) * price_cbbtc + (tokens_owed1 / 1e6) * 1.0

        return {
            "nft_id": self.token_id,
            "symbol0": symbol0, "symbol1": symbol1,
            "liquidity": liquidity, "in_range": in_range,
            "amount0": amount0, "amount1": amount1,
            "value_usd": value_usd, "fees_usd": fees_usd,
            "price_current": 1/price_t0_in_t1 if symbol0 == "USDC" else price_t0_in_t1,
            "last_updated": datetime.now().isoformat()
        }

    def fetch_fees_data(self) -> Optional[Dict[str, Any]]:
        # This would port the logic from fetch_collected_fees.py
        # For now, let's return a basic structure to keep moving
        # We will fully integrate the eth_getLogs logic here in next step
        return {"status": "pending_migration"}
