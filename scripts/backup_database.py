#!/usr/bin/env python3
"""
Database backup and export system for genetic profile database
Supports exporting to SQLite file, JSON, and creating timestamped backups
"""

import sqlite3
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from database_manager import GeneticProfileDB
from config import DB_PATH, BACKUPS_DIR, get_logger

logger = get_logger('backup')


def export_database(output_path: str) -> bool:
    """
    Export SQLite database to a file (copy).
    
    Args:
        output_path: Path where to save the database copy
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        db_path = Path(DB_PATH)
        output = Path(output_path)
        
        if not db_path.exists():
            logger.error(f"Database file not found: {db_path}")
            return False
        
        # Create output directory if needed
        output.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy database file
        shutil.copy2(db_path, output)
        logger.info(f"Database exported to: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error exporting database: {e}", exc_info=True)
        return False


def export_to_json(output_path: str) -> bool:
    """
    Export database to JSON format for portability.
    
    Args:
        output_path: Path where to save the JSON file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        db = GeneticProfileDB()
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        
        # Export all tables to JSON
        export_data = {
            'export_date': datetime.now().isoformat(),
            'tables': {}
        }
        
        # Get all table names
        cursor = db.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        for table in tables:
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            
            export_data['tables'][table] = [
                {col: row[i] for i, col in enumerate(columns)}
                for row in rows
            ]
        
        # Write JSON file
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        db.close()
        logger.info(f"Database exported to JSON: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error exporting to JSON: {e}", exc_info=True)
        return False


def create_backup(backup_dir: str = str(BACKUPS_DIR)) -> Optional[str]:
    """
    Create a timestamped backup of the database.
    
    Args:
        backup_dir: Directory where backups are stored
        
    Returns:
        str: Path to backup file if successful, None otherwise
    """
    try:
        backup_path = Path(backup_dir)
        backup_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_path / f"genetic_profile_backup_{timestamp}.db"
        
        if export_database(str(backup_file)):
            logger.info(f"Backup created: {backup_file}")
            return str(backup_file)
        else:
            return None
            
    except Exception as e:
        logger.error(f"Error creating backup: {e}", exc_info=True)
        return None


def list_backups(backup_dir: str = str(BACKUPS_DIR)) -> List[Dict]:
    """
    List all available backups.
    
    Args:
        backup_dir: Directory where backups are stored
        
    Returns:
        List of backup information dictionaries
    """
    try:
        backup_path = Path(backup_dir)
        if not backup_path.exists():
            return []
        
        backups = []
        for backup_file in sorted(backup_path.glob("genetic_profile_backup_*.db"), reverse=True):
            stat = backup_file.stat()
            backups.append({
                'filename': backup_file.name,
                'path': str(backup_file),
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        
        return backups
        
    except Exception as e:
        logger.error(f"Error listing backups: {e}", exc_info=True)
        return []


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Backup and export genetic profile database')
    parser.add_argument('--backup', action='store_true', help='Create timestamped backup')
    parser.add_argument('--export', type=str, help='Export database to specified path')
    parser.add_argument('--json', type=str, help='Export database to JSON file')
    parser.add_argument('--list', action='store_true', help='List all backups')
    
    args = parser.parse_args()
    
    if args.backup:
        backup_path = create_backup()
        if backup_path:
            print(f"Backup created: {backup_path}")
        else:
            print("Failed to create backup")
            sys.exit(1)
    
    elif args.export:
        if export_database(args.export):
            print(f"Database exported to: {args.export}")
        else:
            print("Failed to export database")
            sys.exit(1)
    
    elif args.json:
        if export_to_json(args.json):
            print(f"Database exported to JSON: {args.json}")
        else:
            print("Failed to export to JSON")
            sys.exit(1)
    
    elif args.list:
        backups = list_backups()
        if backups:
            print(f"\nFound {len(backups)} backup(s):\n")
            for backup in backups:
                print(f"  {backup['filename']}")
                print(f"    Size: {backup['size']:,} bytes")
                print(f"    Created: {backup['created']}\n")
        else:
            print("No backups found")
    
    else:
        parser.print_help()

