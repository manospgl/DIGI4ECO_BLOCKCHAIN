# DIGI4ECO UNIC's Repository

This repository maintains the development and deployment of smart contracts that are deployed in a private Besu network for the purposes of the DIGI4ECO EU project. It serves as the backend of the whole system.

## 🚀 **Latest Updates**

### ✅ **Major Improvements:**
- **Automated Deployment**: Complete pipeline for smart contract compilation, deployment, and verification
- **Docker Containerization**: Full API containerization with health checks and monitoring
- **Fixed Issues**: Resolved contract address extraction and dependency conflicts
- **Enhanced Documentation**: Comprehensive guides and troubleshooting

### 🔧 **Current Status:**
- ✅ **Smart Contract**: Solidity 0.8.0 with dual ID system
- ✅ **API**: Non-blocking with multiple transactions per block support
- ✅ **Docker**: Simple one-command deployment
- ✅ **Performance**: Multiple transactions per block (tested with 67 tx in one block)

## 🎯 **Quick Start**

### **Deploy Contract**
```bash
cd src/
python3 compiler.py
python3 deploy_contract.py
```

### **Run API (Docker)**
```bash
cd src/
./docker_run.sh
```

### **Run API (Local)**
```bash
cd src/
python3 api.py
```

### **Prerequisites for Automated Deployment**
```bash
cd src/
# 1. Make scripts executable
chmod +x *.sh

# 2. Ensure virtual environment is activated
source venv/bin/activate

# 3. Verify solc version
solc --version  # Should show: Version: 0.8.0+commit.c7dfd78e.Darwin.appleclang
```

## 📁 **Project Structure**

- `src/` - Current development version with advanced features
  - Smart contract deployment and interaction scripts
  - REST API server for blockchain operations
  - Data storage client for programmatic access
  - Docker configuration and deployment scripts

## 🛠 **Prerequisites**

### **1. Solidity Compiler Setup**
```bash
# Install solc-select
pip3 install solc-select

# Install and use solc 0.8.0
solc-select install 0.8.0
solc-select use 0.8.0

# Add to PATH (for persistence, add to ~/.zshrc)
export PATH="$(python3 -m site --user-base)/bin:$PATH"

# Verify installation
solc --version  # Should show: Version: 0.8.0+commit.c7dfd78e.Darwin.appleclang
```

### **2. Python Environment**
```bash
cd src/
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### **3. Blockchain Network**
Ensure your blockchain network is running on `localhost:8545`

### **4. Make Scripts Executable**
```bash
cd src/
chmod +x *.sh
```

## 📋 **API Endpoints**

### **Health Check**
```bash
curl http://localhost:8000/health
```

### **Store Data**
```bash
curl -X POST http://localhost:8000/store \
  -H "Content-Type: application/json" \
  -d '{
    "data_id": 987654321,
    "checksum": "a4c0f6f8eed97e8866f7a9d10f8216c3efd6191a4f0bfe88794ec19fef9f35b3"
  }'
```

### **Get Data**
```bash
curl http://localhost:8000/data/42
```

## 🐳 **Docker Commands**

### **Build and Run**
```bash
cd src/
docker-compose up -d
```

### **View Logs**
```bash
docker-compose logs -f
```

### **Stop Container**
```bash
docker-compose down
```

## 🚨 **Troubleshooting**

### **Common Issues**

1. **"solc version mismatch"**
   ```bash
   solc-select use 0.8.0
   export PATH="$(python3 -m site --user-base)/bin:$PATH"
   ```

2. **"InvalidAddress: ENS name: 'CONTRACT_ADDRESS' is invalid"**
   - ✅ **FIXED**: Contract address extraction bug resolved
   - The script now correctly extracts actual addresses

3. **"No response from blockchain"**
   - Ensure blockchain network is running on `localhost:8545`
   - Check if contract is deployed

4. **"Docker build failed"**
   - ✅ **FIXED**: Dependency conflicts resolved
   - All requirements are now compatible

### **Health Checks**
```bash
# Check blockchain
curl -X POST -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
  http://localhost:8545

# Check API
curl http://localhost:8000/health
```

## 📚 **Documentation**

- **Main Guide**: `src/README.md` - Detailed setup and usage instructions
- **Deployment Guide**: `src/DEPLOYMENT.md` - Complete deployment documentation

---

## 🎯 **Key Features**

- **Smart Contract Deployment**: Deploy DIGI4ECO smart contracts to private Besu networks
- **Data Storage**: Store and retrieve data on the blockchain with checksums
- **REST API**: HTTP endpoints for blockchain operations (current version)
- **Docker Containerization**: Production-ready containerized deployment
- **Automated Deployment**: Complete pipeline for compilation, deployment, and verification
- **Client Libraries**: Python client for programmatic access
- **Health Monitoring**: Built-in health checks and monitoring

## 🌐 **Network Configuration**

The system is designed to work with private Besu networks. Ensure your network is properly configured with:
- Validator nodes
- RPC endpoints
- Gas configuration
- Network ID settings

## 🚀 **Setting Up a Besu Network with quorum-dev-quickstart**

You can quickly spin up a local Besu network using the [quorum-dev-quickstart](https://github.com/Consensys/quorum-dev-quickstart) utility. Here's how:

### **1. Prerequisites**
- Docker & Docker Compose v2+
- Node.js (or Yarn)
- (On MacOS: allocate at least 4GB RAM to Docker)

### **2. Run the Quickstart Utility**
```sh
npx quorum-dev-quickstart
```

Use these answers when prompted:
```
Which Ethereum client would you like to run? Default: [1]
  1. Hyperledger Besu
Do you wish to enable support for private transactions? [Y/n]
  n
Do you wish to enable support for logging with Loki, Splunk or ELK (Elasticsearch, Logstash & Kibana)? Default: [1]
  1. Loki
Do you wish to enable support for monitoring your network with Chainlens? [N/y]
  n
Do you wish to enable support for monitoring your network with Blockscout? [N/y]
  n
Where should we create the config files for this network? (Default: ./quorum-test-network)
  [Press Enter or specify your path]
```

### **3. Update the Docker Compose Configuration**

Open the generated `docker-compose.yml` file in your network folder. Find the section like this:

```yaml
x-besu-def:
  &besu-def
  restart: "on-failure"
  image: hyperledger/besu:${BESU_VERSION:-latest}
  env_file:
    - ./config/besu/.env
  entrypoint:
    - /bin/bash
    - -c
    - |
      cp "/config/${BESU_CONS_ALGO:-QBFT}genesis.json" /config/genesis.json
      /opt/besu/bin/besu \
      --config-file=/config/config.toml \
      --p2p-host=$$(hostname -i) \
      --rpc-http-api=EEA,WEB3,ETH,NET,TRACE,DEBUG,ADMIN,TXPOOL,PERM,${BESU_CONS_ALGO:-QBFT} \
      --rpc-ws-api=EEA,WEB3,ETH,NET,TRACE,DEBUG,ADMIN,TXPOOL,PERM,${BESU_CONS_ALGO:-QBFT} ;
```

**Replace it with:**

```yaml
x-besu-def:
  &besu-def
  restart: "on-failure"
  image: hyperledger/besu:${BESU_VERSION:-latest}
  env_file:
    - ./config/besu/.env
  entrypoint:
    - /bin/bash
    - -c
    - |
      /opt/besu/bin/besu \
      --config-file=/config/config.toml \
      --genesis-file=/config/${BESU_CONS_ALGO:-QBFT}genesis.json \
      --p2p-host=$$(hostname -i) \
      --rpc-http-api=EEA,WEB3,ETH,NET,TRACE,DEBUG,ADMIN,TXPOOL,PERM,${BESU_CONS_ALGO:-QBFT} \
      --rpc-ws-api=EEA,WEB3,ETH,NET,TRACE,DEBUG,ADMIN,TXPOOL,PERM,${BESU_CONS_ALGO:-QBFT}
```

### **4. Adjust Block Period (Optional)**

To change the block time, open `config/besu/QBFTgenesis.json` in your network folder. Find:

```json
"blockperiodseconds": 5,
```

Change `5` to your desired number of seconds.

### **5. Start the Network**

From your network directory, run:

```sh
./run.sh
```

Your Besu network should now be up and running with your custom settings!

## 🤝 **Contributing**

1. Follow the existing code structure
2. Update documentation for any changes
3. Test Docker deployment before committing

## 📄 **License**

This project is part of the DIGI4ECO EU initiative for blockchain-based data storage solutions.

---

**References:**
- [quorum-dev-quickstart GitHub](https://github.com/Consensys/quorum-dev-quickstart) 
