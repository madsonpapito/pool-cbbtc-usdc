import subprocess
import time
import sys

def run_script(script_name):
    print(f"--- Running {script_name} ---")
    try:
        # Using sys.executable to ensure we use the same python interpreter
        result = subprocess.run([sys.executable, f"tools/{script_name}"], check=True, text=True)
        print(f"--- {script_name} completed successfully ---")
        return True
    except subprocess.CalledProcessError as e:
        print(f"!!! Error running {script_name}: {e}")
        return False

def main():
    start_time = time.time()
    
    steps = [
        "fetch_pool_data.py",
        "update_history.py",
        "dashboard_gen_v3.py"
    ]
    
    for script in steps:
        if not run_script(script):
            print("Sync aborted due to error.")
            sys.exit(1)
            
    elapsed = time.time() - start_time
    print(f"\nSync completed in {elapsed:.2f} seconds.")

if __name__ == "__main__":
    main()
