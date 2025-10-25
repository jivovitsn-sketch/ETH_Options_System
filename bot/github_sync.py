#!/usr/bin/env python3
"""GITHUB AUTO-SYNC - автоматическая синхронизация"""
import subprocess
from datetime import datetime
from pathlib import Path
from discord_multi_channel import DiscordMultiChannel

class GitHubSync:
    def __init__(self):
        self.discord = DiscordMultiChannel()
        self.repo_path = Path(__file__).parent.parent
        
        print("✅ GitHub Sync initialized")
    
    def sync(self, message=None):
        """Синхронизация с GitHub"""
        
        if message is None:
            message = f"Auto-sync: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        try:
            # Git commands
            subprocess.run(['git', 'add', '.'], cwd=self.repo_path, check=True)
            
            result = subprocess.run(
                ['git', 'commit', '-m', message],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            if 'nothing to commit' in result.stdout:
                print("Nothing to commit")
                return False
            
            subprocess.run(['git', 'push', 'origin', 'main'], cwd=self.repo_path, check=True)
            
            # Count files
            files_result = subprocess.run(
                ['git', 'diff', '--name-only', 'HEAD~1', 'HEAD'],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            files_changed = len(files_result.stdout.strip().split('\n')) if files_result.stdout else 0
            
            print(f"✅ Synced to GitHub: {files_changed} files")
            
            # Discord notification
            self.discord.admin_github_sync({
                'commit': message,
                'files': files_changed
            })
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Git error: {e}")
            self.discord.admin_error(f"GitHub sync failed: {e}")
            return False

if __name__ == "__main__":
    sync = GitHubSync()
    sync.sync("Manual sync test")
