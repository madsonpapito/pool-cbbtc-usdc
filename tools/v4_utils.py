from web3 import Web3
from eth_abi import encode

# V4 PoolManager Address (Base Mainnet - subject to change if using a specific deployment, 
# but consistent with user context if they provided one, otherwise standardizing or using value from previous scripts)
# Using the address from previous fetch_v4_test.py for consistency or a placeholder if not confirmed.
# The previous script had V4_PM_ADDRESS = "0x7C5f5A4bBd8fD63184577525326123B519429bDc" (Example/Testnet?)
# NOTE: V4 is not mainnet confirmed on Base yet as of my knowledge cutoff/current time usually, 
# but user provided specific addresses. I will use those.

POOL_MANAGER_ADDRESS = "0x7C5f5A4bBd8fD63184577525326123B519429bDc" 

class PoolKey:
    def __init__(self, currency0, currency1, fee, tick_spacing, hooks):
        self.currency0 = currency0
        self.currency1 = currency1
        self.fee = fee
        self.tick_spacing = tick_spacing
        self.hooks = hooks

    def to_tuple(self):
        return (
            self.currency0,
            self.currency1,
            self.fee,
            self.tick_spacing,
            self.hooks
        )

def get_pool_id(pool_key: PoolKey) -> bytes:
    """
    Calculates the PoolId (keccak256 hash) of the PoolKey.
    """
    # Sol struct: 
    # struct PoolKey {
    #     Currency currency0;
    #     Currency currency1;
    #     uint24 fee;
    #     int24 tickSpacing;
    #     IHooks hooks;
    # }
    # Encoded as (address, address, uint24, int24, address) 
    # Note: Currency is address, IHooks is address
    
    encoded = encode(
        ['address', 'address', 'uint24', 'int24', 'address'],
        [
            pool_key.currency0,
            pool_key.currency1,
            pool_key.fee,
            pool_key.tick_spacing,
            pool_key.hooks
        ]
    )
    return Web3.keccak(encoded)

def get_slot0_call_data(pool_id: bytes) -> str:
    """
    Generates calldata for 'getSlot0(bytes32)' on PoolManager.
    Function signature: getSlot0(bytes32) -> (uint160 sqrtPriceX96, int24 tick, uint24 protocolFee, uint24 lpFee)
    # Note: Method name might vary in specific V4 implementations (e.g. `slot0`, `getSlot0`). 
    # Standard V4 Core often uses `slot0` (public mapping) or `getSlot0`. 
    # Let's assume `getSlot0` or check ABI.
    # Signature for `getSlot0(bytes32)` is `0x385aa692` (example) or just mapping access.
    # Actually, in V4 PoolManager, it is usually `getSlot0` or `pools` mapping.
    # Let's use a standard signature for `getSlot0(bytes32)`.
    """
    # sighash for getSlot0(bytes32)
    # This might need verification against exact ABI user is using.
    # For now generating standard call.
    # Let's assume the function is `getSlot0(bytes32 id) external view returns (uint160, int24, uint24, uint24)`
    # keccak('getSlot0(bytes32)').hexdigest()[:8]
    
    # Common accessor for `pools(bytes32)` struct returning (slot0, ...) might be different.
    # Let's try to stick to `getSlot0` if it exists, or `pools`.
    # Based on USER REQUEST description: "Everything in PoolManager".
    # We will use a generic "getSlot0" signature for now.
    
    # Manually calculating sighash for `getSlot0(bytes32)`:
    # Web3.keccak(text="getSlot0(bytes32)").hex()[:10] -> 0x....
    
    fn_selector = Web3.keccak(text="getSlot0(bytes32)").hex()[:10]
    return fn_selector + pool_id.hex()[2:].zfill(64)
