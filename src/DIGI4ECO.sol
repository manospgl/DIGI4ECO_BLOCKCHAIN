pragma solidity ^0.8.0;

contract DataStorage {
    struct Data {
        uint256 blockchainId;  // Auto-incremented blockchain storage ID
        uint256 dataId;        // Off-chain data identifier provided by the caller
        string checksum;       // Integrity checksum provided by the caller
    }

    mapping(uint256 => Data) private dataStore;  // blockchainId => Data
    uint256 private currentBlockchainId = 1;  // Start blockchain IDs from 1

    event DataStored(uint256 indexed blockchainId, uint256 dataId, string checksum);

    function storeData(
        uint256 _dataId,
        string memory _checksum
    ) public {
        dataStore[currentBlockchainId] = Data(
            currentBlockchainId, 
            _dataId,
            _checksum
        );
        emit DataStored(currentBlockchainId, _dataId, _checksum);
        currentBlockchainId++;
    }

    function getData(uint256 _blockchainId) public view returns (
        uint256, uint256, string memory
    ) {
        Data memory data = dataStore[_blockchainId];
        return (
            data.blockchainId, 
            data.dataId,
            data.checksum
        );
    }
}
