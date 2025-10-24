#!/usr/bin/env python3
"""BACKUP SYSTEM"""
import shutil
from pathlib import Path
from datetime import datetime
import json

class BackupSystem:
    def __init__(self):
        self.backup_dir = Path('/home/eth_trader/ETH_Options_Backups')
        self.backup_dir.mkdir(exist_ok=True)
        
        print("✅ Backup System initialized")
        print(f"   Backup dir: {self.backup_dir}")
    
    def backup_data(self):
        """Backup all important data"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = self.backup_dir / f"backup_{timestamp}"
        backup_path.mkdir(exist_ok=True)
        
        source = Path('/home/eth_trader/ETH_Options_System')
        
        # Backup configs
        if (source / 'config').exists():
            shutil.copytree(source / 'config', backup_path / 'config')
        
        # Backup results
        for ext in ['*.json', '*.csv']:
            for file in source.glob(f'**/{ext}'):
                if 'raw' not in str(file):  # Skip raw data
                    dest = backup_path / file.relative_to(source)
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(file, dest)
        
        # Create manifest
        manifest = {
            'timestamp': timestamp,
            'files_backed_up': len(list(backup_path.rglob('*'))),
            'source': str(source)
        }
        
        with open(backup_path / 'manifest.json', 'w') as f:
            json.dump(manifest, f, indent=2)
        
        print(f"\n✅ Backup created: {backup_path}")
        print(f"   Files: {manifest['files_backed_up']}")
        
        return backup_path
    
    def list_backups(self):
        """List all backups"""
        backups = sorted(self.backup_dir.glob('backup_*'))
        
        print("\n" + "="*60)
        print("AVAILABLE BACKUPS")
        print("="*60)
        
        for backup in backups:
            manifest_file = backup / 'manifest.json'
            
            if manifest_file.exists():
                with open(manifest_file) as f:
                    manifest = json.load(f)
                
                print(f"\n{backup.name}")
                print(f"  Files: {manifest['files_backed_up']}")
                print(f"  Time: {manifest['timestamp']}")

if __name__ == "__main__":
    backup = BackupSystem()
    
    # Create backup
    backup.backup_data()
    
    # List all
    backup.list_backups()
