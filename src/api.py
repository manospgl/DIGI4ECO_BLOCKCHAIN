import os
import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from data_storage_client import DataStorageClient

# ─── 1. CONFIGURATION ──────────────────────────────────────────────────────────
# Base directory of this script
SCRIPT_DIR         = os.path.dirname(os.path.abspath(__file__))

# Paths to your files
ABI_FILE_PATH      = os.path.join(SCRIPT_DIR, 'sc_abi.json')
PRIVATE_KEY_PATH   = os.path.join(SCRIPT_DIR, 'private_key.txt')
DATA_JSON_PATH     = os.path.join(SCRIPT_DIR, 'data_entries.json')  # if you ever batch-load

# On-chain settings
PROVIDER_URL       = os.getenv('PROVIDER_URL',      'http://localhost:8545')
CONTRACT_ADDRESS   = os.getenv('CONTRACT_ADDRESS',  '0x2D23155F7005E926E3825f7b86299cABFB9c7C3c') #server address, skynet v2 11-13-2025 0x2D23155F7005E926E3825f7b86299cABFB9c7C3c 

# ─── 2. BOOTSTRAP FASTAPI & CLIENT ─────────────────────────────────────────────
app = FastAPI(title="Internal DataStorage API", docs_url=None, redoc_url=None)

client = DataStorageClient(
    provider_url         = PROVIDER_URL,
    contract_address     = CONTRACT_ADDRESS,
    abi_file_path        = ABI_FILE_PATH,
    private_key_file_path= PRIVATE_KEY_PATH
)

# ─── 3. Pydantic MODELS ────────────────────────────────────────────────────────
class StoreRequest(BaseModel):
    data_id: int
    checksum: str

class StoreResponse(BaseModel):
    tx_hash: str
    blockchain_id: int
    data_id: int
    checksum: str
    success: bool

class GetDataResponse(BaseModel):
    blockchain_id: int
    data_id: int
    checksum: str

# ─── 4. ENDPOINTS ──────────────────────────────────────────────────────────────
@app.get("/health")
def health_check():
    """Health check endpoint for Docker"""
    return {"status": "healthy", "timestamp": datetime.datetime.now().isoformat()}

@app.post("/store", response_model=StoreResponse)
def store(req: StoreRequest):
    """Sign & broadcast a storeData() txn, wait for mining to get blockchain_id."""
    try:
        # Submit and WAIT for receipt to get blockchain_id from event
        blockchain_id, data_id, checksum, tx_hash = client.store_data(
            data_id          = req.data_id,
            checksum         = req.checksum,
            wait_for_receipt = True  # Wait to get blockchain_id!
        )
        
        return StoreResponse(
            tx_hash=tx_hash, 
            blockchain_id=blockchain_id,  # Real ID from contract
            data_id=data_id,
            checksum=checksum,
            success=True
        )
    except Exception as e:
        raise HTTPException(500, f"Failed to store data: {str(e)}")

@app.get("/data/{blockchain_id}", response_model=GetDataResponse)
def get_data(blockchain_id: int):
    """Fetch the tuple for a given blockchain ID from chain storage."""
    data = client.get_data(blockchain_id)
    if not data:
        raise HTTPException(404, f"No data found for blockchain ID {blockchain_id}")
    return GetDataResponse(
        blockchain_id = data[0],
        data_id       = data[1],
        checksum      = data[2],
    )

# ─── 5. ENTRYPOINT ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)