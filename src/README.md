# DIGI4ECO MVP Data Storage

A lightweight reference implementation that stores only the minimum information on chain:
- `blockchainId`: sequential identifier allocated by the smart contract
- `dataId`: caller-provided reference back to your off-chain dataset
- `checksum`: integrity hash (string) that validates the off-chain payload

The `src` directory contains everything needed to compile, deploy, and expose the contract through a FastAPI service.

## Quick Start

### 1. Set up Python environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Compile the smart contract
```bash
python3 compiler.py
```
> **Apple silicon note:** pre-0.8.24 macOS solc binaries are Intel-only. If `compiler.py` fails, either install Rosetta or compile `DIGI4ECO.sol` in Remix and copy the ABI/bytecode into `sc_abi.json` and `sc_bytecode.bin`.

### 3. Deploy the contract
```bash
python3 deploy_contract.py
```
The script prints the deployed address, e.g. `0x1234...`. Copy it for the API.

### 4. Configure the API
Set `CONTRACT_ADDRESS` via environment variable or edit the default in `api.py`:
```bash
export CONTRACT_ADDRESS=0xYOUR_DEPLOYED_ADDRESS
```
(Optional) override `PROVIDER_URL` if your node is not `http://localhost:8545`.

### 5. Run the API
```bash
python3 api.py
```
Or run the included Docker wrapper:
```bash
./docker_run.sh
```
The service listens on `http://127.0.0.1:8000`.

## API Usage

### POST `/store`
```bash
curl -X POST http://127.0.0.1:8000/store \
  -H "Content-Type: application/json" \
  -d '{
        "data_id": 987654321,
        "checksum": "a4c0f6f8eed97e8866f7a9d10f8216c3efd6191a4f0bfe88794ec19fef9f35b3"
      }'
```
Successful response:
```json
{
  "tx_hash": "0x...",
  "blockchain_id": 42,
  "data_id": 987654321,
  "checksum": "a4c0f6f8eed97e8866f7a9d10f8216c3efd6191a4f0bfe88794ec19fef9f35b3",
  "success": true
}
```

### GET `/data/{blockchain_id}`
```bash
curl http://127.0.0.1:8000/data/42
```
Response:
```json
{
  "blockchain_id": 42,
  "data_id": 987654321,
  "checksum": "a4c0f6f8eed97e8866f7a9d10f8216c3efd6191a4f0bfe88794ec19fef9f35b3"
}
```

### Event payload
Every successful store emits `DataStored(blockchainId, dataId, checksum)`.

## Python client example
```python
from data_storage_client import DataStorageClient

client = DataStorageClient(
    provider_url="http://localhost:8545",
    contract_address="0xYOUR_DEPLOYED_ADDRESS",
    abi_file_path="sc_abi.json",
    private_key_file_path="private_key.txt"
)

blockchain_id, data_id, checksum, tx_hash = client.store_data(
    data_id=123,
    checksum="deadbeef",
    wait_for_receipt=True
)
print(blockchain_id, data_id, checksum, tx_hash)
```

## Directory layout
```
src
├── api.py                 # FastAPI service
├── compiler.py            # solc wrapper (ABI + bytecode generator)
├── data_storage_client.py # Web3 helper used by the API
├── deploy_contract.py     # Deployment script
├── DIGI4ECO.sol           # Solidity smart contract
├── docker_run.sh          # Convenience script to run the API in Docker
├── docker-compose.yml
├── Dockerfile
├── logs/
│   ├── deployments.json
│   └── test_results.json
├── README.md              # This file
├── requirements.txt
├── sc_abi.json
├── sc_bytecode.bin
└── venv/                  # Optional local virtual environment
```

## Troubleshooting

- **Cannot compile contract on macOS (M1/M2/M3):** install Rosetta (`softwareupdate --install-rosetta`) or compile in Remix and drop the ABI/bytecode into the generated files.
- **`ConnectionError: Failed to connect to the Ethereum node.`** Ensure your execution node is reachable at `PROVIDER_URL` and that it has unlocked accounts for the provided private key.
- **Transactions stuck in `pending`:** confirm the account has sufficient ETH on the target network and the gas price is acceptable.

## License

DIGI4ECO MVP is part of the DIGI4ECO initiative for blockchain-based data storage solutions.
