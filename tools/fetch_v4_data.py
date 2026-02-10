import requests
import json
import base64
from decimal import Decimal, getcontext
try:
    from eth_abi import encode
    from eth_utils import keccak
except ImportError:
    print("Warning: eth_abi or eth_utils not installed. Pool ID calculation will fail.")

# Configuration
RPC_URL = "https://mainnet.base.org"
PM_ADDRESS = "0x7c5f5a4bbd8fd63184577525326123b519429bdc" # V4 Position Manager
POOL_MGR_ADDRESS = "0x498581ff71fa93bfe3c234a3787309Ea5d034244" 

# ABIs
ABI_TOKEN_URI = "0xc87b56dd"
ABI_SLOT0 = "0x3850c7bd" 

def call_rpc(to_addr, data):
    payload = {"jsonrpc": "2.0", "method": "eth_call", "params": [{"to": to_addr, "data": data}, "latest"], "id": 1}
    try:
        res = requests.post(RPC_URL, json=payload, timeout=10)
        return res.json().get('result')
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    nft_id = 1345196
    print(f"Fetching V4 Data for NFT #{nft_id}...")
    
    # 1. Fetch Metadata via TokenURI
    data_uri = ABI_TOKEN_URI + hex(nft_id)[2:].zfill(64)
    res_uri = call_rpc(PM_ADDRESS, data_uri)
    
    if not res_uri or len(res_uri) < 100:
        print("Failed to fetch TokenURI.")
        return

    try:
        offset = int(res_uri[2:66], 16) * 2
        length = int(res_uri[2+offset:2+offset+64], 16) * 2
        hex_data = res_uri[2+offset+64 : 2+offset+64+length]
        uri_str = bytes.fromhex(hex_data).decode('utf-8')
        
        if uri_str.startswith("data:application/json;base64,"):
            b64_data = uri_str.split(",")[1]
            json_str = base64.b64decode(b64_data).decode('utf-8')
            metadata = json.loads(json_str)
            print("\nMetadata Found:")
            print(f"Name: {metadata.get('name')}")
            
            # 2. Reconstruct Pool Key from known data (verified by metadata)
            # Tokens: cbBTC (Base), USDC (Base)
            ADDR_USDC = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"
            ADDR_CBBTC = "0xcbb7c0000ab88b473b1f5afd9ef808440eed33bf"
            
            t0, t1 = sorted([ADDR_USDC.lower(), ADDR_CBBTC.lower()])
            fee = 500 # 0.05%
            tick_spacing = 10
            hooks = "0x0000000000000000000000000000000000000000"
            
            print(f"\nPool Key Config:")
            print(f"  Token0: {t0}")
            print(f"  Token1: {t1}")
            print(f"  Fee: {fee}")
            
            # 3. Calculate Pool ID
            encoded = encode(
                ['address', 'address', 'uint24', 'int24', 'address'],
                [t0, t1, fee, tick_spacing, hooks]
            )
            pool_id_bytes = keccak(encoded)
            pool_id_hex = "0x" + pool_id_bytes.hex()
            print(f"Pool ID: {pool_id_hex}")
            
            # 4. Fetch Slot0
            data_slot0 = ABI_SLOT0 + pool_id_bytes.hex()
            res_slot0 = call_rpc(POOL_MGR_ADDRESS, data_slot0)
            
            if res_slot0:
                print(f"Slot0 Raw: {res_slot0}")
                raw = res_slot0[2:]
                val = int(raw[0:64], 16)
                
                sqrtPriceX96 = val & ((1 << 160) - 1)
                tick = (val >> 160) & ((1 << 24) - 1)
                if tick >= 2**23: tick -= 2**24
                
                print(f"SqrtPriceX96: {sqrtPriceX96}")
                print(f"Current Tick: {tick}")
                
                # Price Calculation
                price0 = float(Decimal("1.0001") ** Decimal(tick))
                
                if t0 == ADDR_USDC.lower():
                    # t0 is USDC (6), t1 is cbBTC (8)
                    # price0 is USDC per cbBTC? No. 
                    # Price is amount of t1 per 1 t0? Or t0 per t1?
                    # V3/V4: 1.0001^tick = price of Token0 in terms of Token1.
                    # So price0 = cbBTC per 1 USDC.
                    # value = 0.0000...
                    
                    # Adjusted for decimals:
                    # real_price = price0 * 10^(dec0 - dec1) 
                    #            = price0 * 10^(6 - 8) = price0 * 0.01
                    
                    price_t0_in_t1 = price0 * (10**(6-8))
                    
                    # We want cbBTC price in USDC (USDC per 1 cbBTC)
                    # This is 1 / price_t0_in_t1
                    if price_t0_in_t1:
                        price_usd = 1 / price_t0_in_t1
                        print(f"cbBTC Price: ${price_usd:,.2f}")
                else:
                    # t0 is cbBTC
                    price_t0_in_t1 = price0 * (10**(8-6))
                    print(f"cbBTC Price: ${price_t0_in_t1:,.2f}")
            else:
                print("Failed to fetch Slot0")
                
        else:
            print("TokenURI is not JSON/Base64")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
