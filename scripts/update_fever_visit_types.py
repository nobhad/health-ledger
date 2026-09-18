#!/usr/bin/env python3
"""
Update visit types for fever temperatures.
If a temperature is a fever (> 100.4°F or > 38°C), it should be tagged as sick_visit.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from database_manager import GeneticProfileDB


def update_fever_visit_types():
    """Update visit types for fevers to sick_visit"""
    db = GeneticProfileDB()
    cursor = db.conn.cursor()
    
    # Find all fevers that aren't tagged as sick_visit
    cursor.execute("""
        SELECT id, metric_value, unit, visit_type, collection_date
        FROM health_metrics
        WHERE metric_type = 'temperature'
        AND metric_value IS NOT NULL
        AND visit_type != 'sick_visit'
        AND (
            (unit = 'F' AND metric_value > 100.4)
            OR (unit = 'C' AND metric_value > 38)
        )
    """)
    
    fevers = cursor.fetchall()
    print(f"Found {len(fevers)} fevers not tagged as sick visits")
    
    updated = 0
    for fever_id, value, unit, current_type, date in fevers:
        # Update to sick_visit
        cursor.execute("""
            UPDATE health_metrics
            SET visit_type = 'sick_visit'
            WHERE id = ?
        """, (fever_id,))
        updated += 1
        
        if updated <= 10:
            print(f"  Updated: {date} - {value}°{unit} ({current_type} -> sick_visit)")
    
    db.conn.commit()
    print(f"\n✅ Updated {updated} fevers to sick_visit")
    
    # Verify
    cursor.execute("""
        SELECT COUNT(*) FROM health_metrics
        WHERE metric_type = 'temperature'
        AND metric_value IS NOT NULL
        AND visit_type = 'sick_visit'
        AND (
            (unit = 'F' AND metric_value > 100.4)
            OR (unit = 'C' AND metric_value > 38)
        )
    """)
    sick_fever_count = cursor.fetchone()[0]
    print(f"✅ Total fevers during sick visits: {sick_fever_count}")
    
    db.close()


if __name__ == "__main__":
    update_fever_visit_types()

