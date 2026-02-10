import requests
import json
import base64

RPC_URL = "https://mainnet.base.org"
MANAGER_ADDRESS = "0x03a520b32C04BF3bEEf7BEb72E919cf822Ed34f1"

ABI_TOKEN_URI = "0xc87b56dd" # tokenURI(uint256)
ABI_OWNER_OF = "0x6352211e" # ownerOf(uint256)

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
    print(f"Debugging NFT #{nft_id} on Manager {MANAGER_ADDRESS}")
    
    # 1. Check Owner
    data_owner = ABI_OWNER_OF + hex(nft_id)[2:].zfill(64)
    res_owner = call_rpc(MANAGER_ADDRESS, data_owner)
    
    if res_owner and len(res_owner) > 2:
        owner = "0x" + res_owner[-40:]
        print(f"Owner: {owner}")
    else:
        print("Owner: Not found (or error)")
        
    # 2. Check TokenURI
    data_uri = ABI_TOKEN_URI + hex(nft_id)[2:].zfill(64)
    res_uri = call_rpc(MANAGER_ADDRESS, data_uri)
    
    if res_uri and len(res_uri) > 100:
        # Decode string
        try:
            offset = int(res_uri[2:66], 16) * 2
            length = int(res_uri[2+offset:2+offset+64], 16) * 2
            hex_data = res_uri[2+offset+64 : 2+offset+64+length]
            uri_str = bytes.fromhex(hex_data).decode('utf-8')
            print(f"TokenURI (Raw): {uri_str[:50]}...")
            
            if uri_str.startswith("data:application/json;base64,"):
                b64_data = uri_str.split(",")[1]
                json_str = base64.b64decode(b64_data).decode('utf-8')
                metadata = json.loads(json_str)
                print("\nMetadata:")
                print(json.dumps(metadata, indent=2))
            else:
                print(f"URI: {uri_str}")
                
        except Exception as e:
            print(f"Error parse URI: {e}")
    else:
        print("TokenURI: Failed to fetch")

if __name__ == "__main__":
    main()
