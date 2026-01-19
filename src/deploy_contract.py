import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from web3 import Web3

# ─── BASIC PATHS ────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
LOG_DIR = SCRIPT_DIR / "logs"
DEPLOYMENTS_LOG = LOG_DIR / "deployments.json"


# ─── HELPERS ───────────────────────────────────────────────────────────────────
def ensure_log_dir():
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def load_log_entries():
    if DEPLOYMENTS_LOG.exists():
        with DEPLOYMENTS_LOG.open("r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def save_log_entries(entries):
    ensure_log_dir()
    with DEPLOYMENTS_LOG.open("w") as f:
        json.dump(entries, f, indent=2)


def get_solc_version():
    try:
        result = subprocess.run(
            ["solc", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip().splitlines()[0]
    except Exception:
        return "unknown"


def log_deployment(success, contract_address="", error_message=None):
    entries = load_log_entries()
    entries.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "contract_address": contract_address,
        "success": success,
        "error_message": error_message,
        "solc_version": get_solc_version()
    })
    save_log_entries(entries)


# ─── WEB3 INITIALIZATION ───────────────────────────────────────────────────────
web3 = Web3(Web3.HTTPProvider("http://localhost:8545"))

if web3.is_connected:
    print("Connected to Ethereum node")
else:
    print("Failed to connect")

# Load the private key from a file
with open(SCRIPT_DIR / 'private_key.txt', 'r') as key_file:
    private_key = key_file.read().strip()

# Get the account address from the private key
account = web3.eth.account.from_key(private_key).address

# Load ABI and Bytecode
with open(SCRIPT_DIR / 'sc_abi.json', 'r') as abi_file:
    abi = json.load(abi_file)

with open(SCRIPT_DIR / 'sc_bytecode.bin', 'r') as bin_file:
    bytecode = bin_file.read()

# Create contract object
HelloWorld = web3.eth.contract(abi=abi, bytecode=bytecode)


# ─── DEPLOYMENT ────────────────────────────────────────────────────────────────
def deploy_contract():
    try:
        transaction = HelloWorld.constructor().build_transaction({
            'from': account,
            'nonce': web3.eth.get_transaction_count(account),
            'gas': 3000000,
            'gasPrice': web3.to_wei('20', 'gwei')
        })

        # Sign the transaction with the private key
        signed_txn = web3.eth.account.sign_transaction(transaction, private_key)

        # Send the signed transaction
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)

        # Wait for the transaction receipt
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

        print(f"Contract deployed at address: {tx_receipt.contractAddress}")
        print(f"Transaction receipt status: {tx_receipt.status}")

        log_deployment(
            success=True,
            contract_address=tx_receipt.contractAddress
        )
        return tx_receipt.contractAddress
    except Exception as exc:
        log_deployment(
            success=False,
            contract_address="",
            error_message=str(exc)
        )
        raise


if __name__ == "__main__":
    contract_address = deploy_contract()

    code = web3.eth.get_code(contract_address)
    if code == b'' or code == '0x':
        print("No contract code found at the address.")
    else:
        print("Contract code found at the address. Deployment successful.")
