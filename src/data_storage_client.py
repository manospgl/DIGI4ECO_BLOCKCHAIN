import os
import json
from web3 import Web3
from typing import Optional, Tuple

class DataStorageClient:
    def __init__(
        self,
        provider_url: str,
        contract_address: str,
        abi_file_path: str,
        private_key_file_path: str,
        data_json_file: Optional[str] = None
    ):
        """
        Initializes the DataStorageClient.

        :param provider_url: URL of the Ethereum node.
        :param contract_address: Deployed contract address.
        :param abi_file_path: Path to the contract's ABI JSON file.
        :param private_key_file_path: Path to the file containing the private key.
        :param data_json_file: (Optional) Path to the JSON file with transaction data entries.
        """
        self.provider_url = provider_url
        self.contract_address = contract_address
        self.abi_file_path = abi_file_path
        self.private_key_file_path = private_key_file_path
        self.data_json_file = data_json_file

        # Set up Web3 connection
        self.web3 = Web3(Web3.HTTPProvider(self.provider_url))
        if not self.web3.is_connected():
            raise ConnectionError("Failed to connect to the Ethereum node.")

        # Load the contract ABI from file
        if not os.path.exists(self.abi_file_path):
            raise FileNotFoundError(f"ABI file not found at {self.abi_file_path}")
        with open(self.abi_file_path, 'r') as abi_file:
            self.abi = json.load(abi_file)

        # Create the contract instance
        self.contract = self.web3.eth.contract(
            address=self.contract_address,
            abi=self.abi
        )

        # Load the private key
        if not os.path.exists(self.private_key_file_path):
            raise FileNotFoundError(f"Private key file not found at {self.private_key_file_path}")
        with open(self.private_key_file_path, 'r') as key_file:
            self.private_key = key_file.read().strip()

        # Get the account address associated with the private key
        self.account_address = self.web3.eth.account.from_key(self.private_key).address

        print("DataStorageClient initialized successfully.")

    def read_latest_transaction_data(self) -> dict:
        """
        Reads the provided JSON file and returns the latest transaction data entry.

        Assumes the JSON file contains an array of entries.

        :return: A dictionary representing the latest entry.
        """
        if not self.data_json_file:
            raise ValueError("No data JSON file provided.")
        if not os.path.exists(self.data_json_file):
            raise FileNotFoundError(f"Data JSON file not found at {self.data_json_file}")

        with open(self.data_json_file, 'r') as f:
            data = json.load(f)

        if not data:
            raise ValueError("JSON file is empty or contains no data.")

        # Return the last entry from the list (assumed to be the latest)
        return data[-1]

    def store_data(
        self,
        data_id: int,
        checksum: str,
        wait_for_receipt: bool = False
    ) -> Optional[Tuple[Optional[int], int, str, str]]:
        """
        Calls the storeData function of the contract.

        :param data_id: Off-chain data identifier
        :param checksum: Integrity checksum
        :param wait_for_receipt: If True, waits for mining. If False, returns immediately.
        :return: Tuple (blockchain_id, data_id, checksum, tx_hash) if wait_for_receipt=True, 
                 or (None, data_id, checksum, tx_hash) if wait_for_receipt=False
        """
        # Build the transaction with pending nonce for concurrency
        transaction = self.contract.functions.storeData(
            data_id,
            checksum
        ).build_transaction({
            'from': self.account_address,
            'nonce': self.web3.eth.get_transaction_count(self.account_address, 'pending'),
            'gas': 2000000,
            'gasPrice': self.web3.to_wei('20', 'gwei')
        })

        # Sign and send the transaction
        signed_tx = self.web3.eth.account.sign_transaction(transaction, self.private_key)
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_hash_hex = tx_hash.hex()
        
        print(f"Transaction submitted. Tx Hash: {tx_hash_hex}")

        # Return immediately if not waiting
        if not wait_for_receipt:
            return None, data_id, checksum, tx_hash_hex

        # Wait for the transaction receipt (original blocking behavior)
        receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Transaction confirmed in block {receipt['blockNumber']}")

        # Process the DataStored event
        data_stored_events = self.contract.events.DataStored().process_receipt(receipt)
        if not data_stored_events:
            print("No DataStored events found in this transaction.")
            return None, data_id, checksum, tx_hash_hex

        stored_event = data_stored_events[0]
        blockchain_id = stored_event['args']['blockchainId']
        emitted_data_id = stored_event['args']['dataId']
        emitted_checksum = stored_event['args']['checksum']

        print(f"Confirmed: Blockchain ID = {blockchain_id}, Data ID = {emitted_data_id}, Checksum = {emitted_checksum}")
        return blockchain_id, emitted_data_id, emitted_checksum, tx_hash_hex

    def get_data(self, _blockchain_id: int) -> Tuple[int, int, str]:
        """
        Calls the getData function of the contract.

        :param _blockchain_id: The blockchain ID to retrieve data for
        :return: A tuple with (blockchain_id, data_id, checksum)
        """
        data = self.contract.functions.getData(_blockchain_id).call()

        # Log the fetched data
        print("\nFetched Data:")
        print(f"  Blockchain ID: {data[0]}")
        print(f"  Data ID      : {data[1]}")
        print(f"  Checksum     : {data[2]}")
        return data