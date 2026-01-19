import subprocess
import json
import sys

def compile_contract(sol_file):
    # Run solc with the --combined-json flag to output ABI and binary
    # Use system solc 0.8.0 (not venv) for Apple Silicon compatibility
    import os
    
    # Check solc version first
    env = os.environ.copy()
    extra_paths = ["/usr/local/bin", "/opt/homebrew/bin"]
    path_parts = [p for p in env.get("PATH", "").split(os.pathsep) if p]
    for extra_path in extra_paths:
        if extra_path not in path_parts:
            path_parts.insert(0, extra_path)
    env["PATH"] = os.pathsep.join(path_parts)

    try:
        version_result = subprocess.run(
            ["solc", "--version"],
            capture_output=True,
            text=True,
            env=env
        )
        if "0.8.0" not in version_result.stdout:
            print(f"⚠️  Warning: solc version might not be 0.8.0")
            print(f"   Current: {version_result.stdout.split('Version:')[1].split()[0] if 'Version:' in version_result.stdout else 'unknown'}")
    except:
        pass
    
    try:
        result = subprocess.run(
            ["solc", "--combined-json", "abi,bin", sol_file],
            capture_output=True,
            text=True,
            check=True,
            env=env
        )
    except subprocess.CalledProcessError as e:
        print("Error during compilation:")
        print(e.stderr)
        sys.exit(1)
    return result.stdout

def parse_output(output):
    try:
        json_output = json.loads(output)
    except json.JSONDecodeError as e:
        print("Failed to decode solc JSON output:", e)
        sys.exit(1)
    
    contracts = json_output.get("contracts")
    if not contracts:
        print("No contracts found in solc output.")
        sys.exit(1)
    
    # Get the first contract entry (if you have multiple, adjust accordingly)
    contract_key, contract_data = next(iter(contracts.items()))
    abi = contract_data.get("abi")
    bytecode = contract_data.get("bin")
    
    if not abi or not bytecode:
        print("Missing ABI or bytecode for contract:", contract_key)
        sys.exit(1)
    
    # Sometimes the ABI is returned as a JSON string. Ensure it is loaded.
    if isinstance(abi, str):
        try:
            abi = json.loads(abi)
        except json.JSONDecodeError as e:
            print("Failed to decode ABI JSON string:", e)
            sys.exit(1)
    
    return abi, bytecode

def main():
    sol_file = "DIGI4ECO.sol"
    print(f"Compiling {sol_file}...")
    output = compile_contract(sol_file)
    
    abi, bytecode = parse_output(output)
    
    # Write the ABI and bytecode to files
    with open("sc_abi.json", "w") as abi_file:
        json.dump(abi, abi_file, indent=4)
    with open("sc_bytecode.bin", "w") as bin_file:
        bin_file.write(bytecode)
    
    print("Compilation successful!")
    print("ABI saved to 'sc_abi.json' and bytecode saved to 'sc_bytecode.bin'.")

if __name__ == "__main__":
    main()