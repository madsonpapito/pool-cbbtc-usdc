import requests
import json

RPC_URL = "https://base-rpc.publicnode.com"
NPM_ADDRESS = "0x03a520b32C04BF3bEEf7BEb72E919cf822EdC299"  # Note: using original case
NFT_ID = 4227642
COLLECT_TOPIC = "0x40d0efd1a53d60ecbf40971b9daf7dc90178c3aadc7aab1765632738fa8b8f01"

# The exact block of the Jan 23 transaction
BLOCK = 41196555

nft_id_topic = "0x" + f"{NFT_ID:064x}"

print(f"Searching for Collect events...")
print(f"NPM Address: {NPM_ADDRESS}")
print(f"Topic0: {COLLECT_TOPIC}")
print(f"Topic1: {nft_id_topic}")
print(f"Block: {BLOCK}")

payload = {
    "jsonrpc": "2.0",
    "method": "eth_getLogs",
    "params": [{
        "address": NPM_ADDRESS,
        "topics": [COLLECT_TOPIC, nft_id_topic],
        "fromBlock": hex(BLOCK - 10),
        "toBlock": hex(BLOCK + 10)
    }],
    "id": 1
}

r = requests.post(RPC_URL, json=payload, timeout=30)
data = r.json()

print(f"\nResponse: {json.dumps(data, indent=2)}")
