#!/usr/bin/env python3
"""
Auto-Sync Service for Survey Data

Automatically detects and imports new spreadsheet data when changes are detected.
Can be run as a standalone service or integrated into the Flask application.
"""

import os
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from survey_normalizer import SurveyNormalizer
import sqlite3


class AutoSyncService:
    """Service for automatically syncing survey data."""
    
    def __init__(self, 
                 source_db: str = "surveyor_data_improved.db",
                 target_db: str = "survey_normalized.db",
                 check_interval: int = 300):  # 5 minutes default
        self.source_db = source_db
        self.target_db = target_db
        self.check_interval = check_interval
        self.normalizer = SurveyNormalizer(source_db, target_db)
        self.running = False
        self.thread = None
        self.last_check = None
        self.sync_stats = {
            'total_syncs': 0,
            'successful_syncs': 0,
            'failed_syncs': 0,
            'last_sync_time': None,
            'last_error': None
        }
    
    def start(self):
        """Start the auto-sync service."""
        if self.running:
            print("⚠️  Auto-sync service is already running")
            return
        
        print(f"🚀 Starting auto-sync service (checking every {self.check_interval} seconds)")
        self.running = True
        self.thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop the auto-sync service."""
        if not self.running:
            print("⚠️  Auto-sync service is not running")
            return
        
        print("🛑 Stopping auto-sync service...")
        self.running = False
        if self.thread:
            self.thread.join(timeout=10)
        print("✅ Auto-sync service stopped")
    
    def _sync_loop(self):
        """Main sync loop that runs in a separate thread."""
        while self.running:
            try:
                self._perform_sync_check()
                time.sleep(self.check_interval)
            except Exception as e:
                print(f"❌ Error in sync loop: {e}")
                self.sync_stats['failed_syncs'] += 1
                self.sync_stats['last_error'] = str(e)
                time.sleep(self.check_interval)
    
    def _perform_sync_check(self):
        """Perform a single sync check."""
        self.last_check = datetime.now()
        
        # Check if source database exists
        if not os.path.exists(self.source_db):
            return
        
        # Ensure target database exists
        if not os.path.exists(self.target_db):
            print("📊 Creating normalized database structure...")
            self.normalizer.create_normalized_schema()
        
        try:
            # Check for new data
            changes = self.normalizer.check_for_new_data()
            
            if changes['total_changes'] > 0:
                print(f"🔄 Auto-sync detected {changes['total_changes']} changes")
                result = self.normalizer.auto_import_new_data()
                
                self.sync_stats['total_syncs'] += 1
                if result['total_processed'] > 0:
                    self.sync_stats['successful_syncs'] += 1
                    self.sync_stats['last_sync_time'] = datetime.now()
                    print(f"✅ Auto-sync completed: {result['message']}")
                else:
                    print(f"ℹ️  Auto-sync: {result['message']}")
            
        except Exception as e:
            self.sync_stats['failed_syncs'] += 1
            self.sync_stats['last_error'] = str(e)
            print(f"❌ Auto-sync failed: {e}")
    
    def force_sync(self) -> Dict[str, Any]:
        """Force an immediate sync check."""
        print("🔄 Forcing immediate sync check...")
        try:
            self._perform_sync_check()
            return {
                'success': True,
                'message': 'Sync check completed',
                'stats': self.get_stats()
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Sync failed: {e}',
                'stats': self.get_stats()
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get sync service statistics."""
        return {
            'running': self.running,
            'check_interval': self.check_interval,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'sync_stats': self.sync_stats.copy(),
            'next_check': (self.last_check + timedelta(seconds=self.check_interval)).isoformat() 
                         if self.last_check else None
        }
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status for dashboard display."""
        try:
            changes = self.normalizer.check_for_new_data()
            
            # Get sync tracking info
            conn = sqlite3.connect(self.target_db)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_tracked,
                    COUNT(CASE WHEN sync_status = 'completed' THEN 1 END) as completed,
                    COUNT(CASE WHEN sync_status = 'failed' THEN 1 END) as failed,
                    MAX(last_sync_timestamp) as last_sync
                FROM sync_tracking
            ''')
            
            tracking_stats = cursor.fetchone()
            conn.close()
            
            return {
                'pending_changes': changes['total_changes'],
                'new_spreadsheets': len(changes['new_data']),
                'updated_spreadsheets': len(changes['updated_data']),
                'total_tracked': tracking_stats[0] if tracking_stats else 0,
                'completed_syncs': tracking_stats[1] if tracking_stats else 0,
                'failed_syncs': tracking_stats[2] if tracking_stats else 0,
                'last_sync': tracking_stats[3] if tracking_stats else None,
                'service_stats': self.get_stats()
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'service_stats': self.get_stats()
            }


# Global auto-sync service instance
_auto_sync_service = None


def get_auto_sync_service() -> AutoSyncService:
    """Get the global auto-sync service instance."""
    global _auto_sync_service
    if _auto_sync_service is None:
        _auto_sync_service = AutoSyncService()
    return _auto_sync_service


def start_auto_sync(check_interval: int = 300):
    """Start the auto-sync service with specified interval."""
    service = get_auto_sync_service()
    service.check_interval = check_interval
    service.start()
    return service


def stop_auto_sync():
    """Stop the auto-sync service."""
    service = get_auto_sync_service()
    service.stop()


def main():
    """Run the auto-sync service as a standalone application."""
    import sys
    import signal
    
    # Parse command line arguments
    check_interval = 300  # 5 minutes default
    
    if len(sys.argv) > 1:
        try:
            check_interval = int(sys.argv[1])
        except ValueError:
            print("Usage: python auto_sync_service.py [check_interval_seconds]")
            return 1
    
    print("🔄 Survey Auto-Sync Service")
    print("=" * 50)
    print(f"📊 Source DB: surveyor_data_improved.db")
    print(f"💾 Target DB: survey_normalized.db")
    print(f"⏱️  Check interval: {check_interval} seconds")
    print()
    
    # Create and start service
    service = AutoSyncService(check_interval=check_interval)
    
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        print("\n🛑 Received interrupt signal")
        service.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start the service
    service.start()
    
    try:
        # Keep the main thread alive
        while service.running:
            time.sleep(1)
    except KeyboardInterrupt:
        service.stop()
    
    return 0


if __name__ == "__main__":
    exit(main())
