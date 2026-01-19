# DIGI4ECO Deployment Guide

Complete guide for deploying the DIGI4ECO blockchain data storage system with Docker and automation.

## 🚀 **Latest Updates**

### ✅ **Recent Fixes:**
- **Contract Address Extraction**: Fixed regex pattern to correctly extract contract addresses
- **Docker Container Startup**: Resolved `InvalidAddress` errors in container initialization
- **Dependency Conflicts**: Fixed `eth-utils` version compatibility with `web3==7.8.0`
- **Docker Compose**: Removed obsolete version warning

### 🔧 **Current Status:**
- ✅ **All scripts working**: No known issues
- ✅ **Docker deployment**: Fully functional
- ✅ **Automation**: Complete pipeline operational
- ✅ **Documentation**: Up to date

## 📋 **Prerequisites**

### **1. Solidity Compiler Setup**
```bash
# Install solc-select
pip3 install solc-select

# Install and use solc 0.8.0
solc-select install 0.8.0
solc-select use 0.8.0

# Add to PATH (for persistence, add to ~/.zshrc)
export PATH="$(python3 -m site --user-base)/bin:$PATH"

# Verify
solc --version  # Should show: Version: 0.8.0+commit.c7dfd78e.Darwin.appleclang
```

### **2. Python Environment**
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### **3. Blockchain Network**
Ensure your blockchain network is running on `localhost:8545`

### **4. Make Scripts Executable**
```bash
chmod +x *.sh
```

## 🎯 **Deployment Options**

### **Option 1: Docker Deployment (Recommended)**
```bash
./docker_run.sh
```
**What it does:**
- Builds Docker image
- Starts container with health checks
- Automatically configures the API

### **Option 2: Manual Deployment**
```bash
# 1. Compile contract
python3 compiler.py

# 2. Deploy contract
python3 deploy_contract.py

# 3. Update contract address in api.py
# 4. Build Docker image
docker build -t digi4eco-api .

# 5. Run container
docker-compose up -d
```

## 🔧 **Script Details**

### **docker_run.sh**
**Purpose**: Docker deployment script
**Steps**:
1. Stop any existing containers
2. Build Docker image
3. Start container
4. Perform health checks

## 🐳 **Docker Configuration**

### **Dockerfile**
```dockerfile
FROM python:3.9-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y curl

# Install solc-select and solc 0.8.0
RUN pip install solc-select
RUN solc-select install 0.8.0
RUN solc-select use 0.8.0

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p /app/logs

# Expose port
EXPOSE 8000

# Start API
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### **docker-compose.yml**
```yaml
services:
  digi4eco-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - PROVIDER_URL=http://host.docker.internal:8545
      - CONTRACT_ADDRESS=${CONTRACT_ADDRESS:-0x0000000000000000000000000000000000000000}
    volumes:
      - ./logs:/app/logs
      - ./private_key.txt:/app/private_key.txt:ro
    networks:
      - digi4eco-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

networks:
  digi4eco-network:
    driver: bridge
```

## 📊 **Logs and Monitoring**

### **Log Locations**
- **Deployment History**: `logs/deployments.json`
- **Test Results**: `logs/test_results.json`
- **Container Logs**: `docker-compose logs -f`

### **Health Checks**
```bash
# API Health
curl http://localhost:8000/health

# Blockchain Health
curl -X POST -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
  http://localhost:8545

# Container Status
docker-compose ps
```

## 🚨 **Troubleshooting**

### **Common Issues**

#### **1. "solc version mismatch"**
```bash
solc-select use 0.8.0
export PATH="$(python3 -m site --user-base)/bin:$PATH"
```

#### **2. "InvalidAddress: ENS name: 'CONTRACT_ADDRESS' is invalid"**
- ✅ **FIXED**: Contract address extraction bug resolved
- The script now correctly extracts actual addresses

#### **3. "No response from blockchain"**
```bash
# Check if blockchain is running
curl -X POST -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
  http://localhost:8545
```

#### **4. "Docker build failed"**
- ✅ **FIXED**: Dependency conflicts resolved
- All requirements are now compatible

#### **5. "Permission denied"**
```bash
chmod +x *.sh
```

### **Debug Commands**
```bash
# Check container logs
docker-compose logs -f

# Check container status
docker-compose ps

# Restart container
docker-compose restart

# Rebuild and restart
docker-compose down
docker-compose up --build -d
```

## 🔄 **Maintenance**

### **Update Contract Address**
The system automatically detects and uses the deployed contract address. If you need to manually update:

1. **In api.py**:
   ```python
   CONTRACT_ADDRESS = os.getenv('CONTRACT_ADDRESS', '0xYOUR_NEW_ADDRESS')
   ```

2. **Environment variable**:
   ```bash
   export CONTRACT_ADDRESS=0xYOUR_NEW_ADDRESS
   ```

### **Update Dependencies**
```bash
# Update requirements.txt
pip freeze > requirements.txt

# Rebuild Docker image
docker-compose down
docker-compose up --build -d
```

### **Clean Up**
```bash
# Stop containers
docker-compose down

# Remove images
docker rmi digi4eco-api

# Clean logs (optional)
rm -rf logs/*
```

## 📚 **API Testing**

### **Test Store Endpoint**
```bash
curl -X POST http://localhost:8000/store \
  -H "Content-Type: application/json" \
  -d '{
    "data_id": 987654321,
    "checksum": "a4c0f6f8eed97e8866f7a9d10f8216c3efd6191a4f0bfe88794ec19fef9f35b3"
  }'
```

### **Test Get Endpoint**
```bash
curl http://localhost:8000/data/42
```

### **Test Health Endpoint**
```bash
curl http://localhost:8000/health
```

## 🎯 **Best Practices**

1. **Always use virtual environment** for development
2. **Test deployment** before production
3. **Monitor logs** for issues
4. **Use health checks** to verify system status
5. **Keep dependencies updated**
6. **Backup contract addresses** and private keys
7. **Use environment variables** for configuration

## 📞 **Support**

For issues or questions:
1. Check the troubleshooting section
2. Review container logs: `docker-compose logs -f`
3. Verify blockchain connectivity
4. Ensure all prerequisites are met
5. Check the main README.md for additional information 