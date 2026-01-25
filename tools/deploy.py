import subprocess
import sys
import os
import datetime

def run_command(command, error_msg):
    print(f"\n> {command}")
    try:
        result = subprocess.run(command, shell=True, check=True, text=True)
        return True
    except subprocess.CalledProcessError:
        print(f"\n❌ {error_msg}")
        return False

def main():
    print("🚀 Starting Deployment Process...")
    
    # 1. Run Sync
    print("\n--- 1. Syncing Data ---")
    if not run_command(f"{sys.executable} tools/sync.py", "Sync failed. Aborting deployment."):
        sys.exit(1)
        
    # 2. Git Operations
    print("\n--- 2. Pushing to GitHub ---")
    
    # Add all changes
    if not run_command("git add .", "Failed to add files."):
        sys.exit(1)
        
    # Commit
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    commit_msg = f"Update pool data {timestamp}"
    if not run_command(f'git commit -m "{commit_msg}"', "Commit failed (maybe nothing to commit). Continuing to push..."):
        pass # It's okay if commit fails if there's nothing to commit, we still try to push just in case
        
    # Push
    if not run_command("git push", "Git push failed. Check your internet connection or git credentials."):
        sys.exit(1)
        
    print("\n✅ Deployment Complete! Vercel should update within minutes.")

if __name__ == "__main__":
    # Ensure we run from project root
    file_path = os.path.abspath(__file__)
    project_root = os.path.dirname(os.path.dirname(file_path))
    os.chdir(project_root)
    
    main()
