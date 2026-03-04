import sys
import os
from web3 import Web3

print("Starting trace test...")
BASE_RPC_URL = "https://mainnet.base.org"
print("Connecting to Web3...")
try:
    w3 = Web3(Web3.HTTPProvider(BASE_RPC_URL, request_kwargs={"timeout": 10}))
    print(f"Web3 connected: {w3.is_connected()}")
    print(f"Chain ID: {w3.eth.chain_id}")
except Exception as e:
    print(f"Web3 Error: {e}")
    sys.exit(1)

NFPM_ADDRESS = "0x03a520b32C04BF3bEEf7BEb72E919cf822Ed34f1"
NFT_ID = 4660395

print(f"Fetching position data for NFT: {NFT_ID}...")
NFPM_ABI = [
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "positions",
        "outputs": [
            {"internalType": "uint96", "name": "nonce", "type": "uint96"},
            {"internalType": "address", "name": "operator", "type": "address"},
            {"internalType": "address", "name": "token0", "type": "address"},
            {"internalType": "address", "name": "token1", "type": "address"},
            {"internalType": "uint24", "name": "fee", "type": "uint24"},
            {"internalType": "int24", "name": "tickLower", "type": "int24"},
            {"internalType": "int24", "name": "tickUpper", "type": "int24"},
            {"internalType": "uint128", "name": "liquidity", "type": "uint128"},
            {"internalType": "uint256", "name": "feeGrowthInside0LastX128", "type": "uint256"},
            {"internalType": "uint256", "name": "feeGrowthInside1LastX128", "type": "uint256"},
            {"internalType": "uint128", "name": "tokensOwed0", "type": "uint128"},
            {"internalType": "uint128", "name": "tokensOwed1", "type": "uint128"},
        ],
        "stateMutability": "view",
        "type": "function",
    }
]

try:
    contract = w3.eth.contract(address=w3.to_checksum_address(NFPM_ADDRESS), abi=NFPM_ABI)
    print("Calling positions()...")
    position = contract.functions.positions(NFT_ID).call()
    print(f"OK - liquidity: {position[7]}")
except Exception as e:
    print(f"Contract Error: {e}")

print("Trace test complete.")
