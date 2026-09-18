#!/usr/bin/env python3
"""
Extract health metrics (vitals, lab values) from primary sources.
Properly tags visit types to ensure averages exclude sick visits.
"""

import sys
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))
from database_manager import GeneticProfileDB
from scripts.extraction_patterns import (
    extract_blood_pressure_readings, extract_temperature_reading, extract_lab_result_line,
    extract_health_log_table_readings,
)

DATE_IN_LINE = re.compile(r'([A-Za-z]+\s+\d{1,2},?\s+\d{4})')


def parse_date(date_str: str) -> Optional[str]:
    """Parse various date formats and return YYYY-MM-DD"""
    if not date_str:
        return None
    
    formats = [
        '%Y-%m-%d',
        '%m/%d/%Y',
        '%m/%d/%y',
        '%m-%d-%Y',
        '%B %d, %Y',
        '%b %d, %Y',
        '%d %B %Y',
        '%d %b %Y',
    ]
    
    # Clean date string
    date_str = date_str.strip()
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime('%Y-%m-%d')
        except:
            continue
    
    # Try to extract date from strings like "Nov 18, 2019, 8:56 AM"
    match = re.search(r'([A-Za-z]+)\s+(\d+),?\s+(\d{4})', date_str)
    if match:
        month_str, day, year = match.groups()
        try:
            dt = datetime.strptime(f"{month_str} {day} {year}", "%b %d %Y")
            return dt.strftime('%Y-%m-%d')
        except:
            try:
                dt = datetime.strptime(f"{month_str} {day} {year}", "%B %d %Y")
                return dt.strftime('%Y-%m-%d')
            except:
                pass
    
    return None



def extract_blood_pressure(text: str) -> List[Dict]:
    """
    Extract blood pressure readings from text.

    A reading must be labelled ("Blood Pressure 120/70", "BP 118/76") or
    carry its unit ("120/80 mmHg") and be physiologically plausible, so
    dates and dosages such as "8/29/2024" or "1/2 tablet" are not recorded.
    """
    metrics = []
    lines = text.split('\n')
    for i, line in enumerate(lines):
        readings = extract_blood_pressure_readings(line)
        if not readings:
            continue

        # Look for a date in the current or the two previous lines
        date = None
        for check_line in lines[max(0, i-2):i+1]:
            date_match = DATE_IN_LINE.search(check_line)
            if date_match:
                date = parse_date(date_match.group(1))
                break
        if not date:
            continue

        # Determine visit type from context
        line_lower = line.lower()
        if any(word in line_lower for word in ['sick', 'illness', 'symptom', 'pain', 'fever', 'urgent', 'emergency']):
            visit_type = 'sick_visit'
        elif any(word in line_lower for word in ['routine', 'checkup', 'well', 'annual', 'preventive', 'screening']):
            visit_type = 'routine_visit'
        else:
            visit_type = None

        for bp in readings:
            metrics.append({
                'metric_type': 'blood_pressure',
                'metric_name': 'Blood Pressure',
                'metric_value': float(bp['systolic']),  # Store systolic
                'metric_value_text': bp['text'],
                'unit': 'mmHg',
                'collection_date': date,
                'visit_type': visit_type,
                'notes': f"Diastolic: {bp['diastolic']}"
            })

    return metrics



def extract_temperature(text: str) -> List[Dict]:
    """
    Extract temperature readings.

    A reading must be labelled ("Temp 98.6 F") or carry a degree sign
    ("36.8 °C") and fall in a plausible range, so zip codes and other numbers
    followed by an F or C are not recorded.
    """
    metrics = []
    lines = text.split('\n')
    for i, line in enumerate(lines):
        temp = extract_temperature_reading(line)
        if not temp:
            continue

        date = None
        for check_line in lines[max(0, i-2):i+1]:
            date_match = DATE_IN_LINE.search(check_line)
            if date_match:
                date = parse_date(date_match.group(1))
                break
        if not date:
            continue

        visit_type = None
        line_lower = line.lower()
        if any(word in line_lower for word in ['sick', 'fever', 'illness']):
            visit_type = 'sick_visit'
        elif any(word in line_lower for word in ['routine', 'checkup', 'well']):
            visit_type = 'routine_visit'

        metrics.append({
            'metric_type': 'temperature',
            'metric_name': 'Temperature',
            'metric_value': temp['value'],
            'unit': temp['unit'],
            'collection_date': date,
            'visit_type': visit_type
        })

    return metrics



def extract_lab_values(text: str, source_date: Optional[str] = None) -> List[Dict]:
    """
    Extract lab test values from text.

    Only "NAME VALUE UNIT [LOW-HIGH]" lines with a recognised lab unit are
    recorded (see extraction_patterns.extract_lab_result_line).
    """
    metrics = []
    current_date = source_date

    for line in text.split('\n'):
        date_match = DATE_IN_LINE.search(line)
        if date_match:
            current_date = parse_date(date_match.group(1)) or current_date

        lab = extract_lab_result_line(line)
        if not lab or not current_date:
            continue

        metrics.append({
            'metric_type': 'lab_value',
            'metric_name': lab['name'],
            'metric_value': lab['value'],
            'metric_value_text': lab['value_text'],
            'unit': lab['unit'],
            'collection_date': current_date,
            'visit_type': None,  # NULL lets the routine-only view classify by date
            'is_abnormal': lab['is_abnormal'],
            'normal_range_min': lab['normal_min'],
            'normal_range_max': lab['normal_max']
        })

    return metrics


def extract_health_log_entries(text: str) -> List[Dict]:
    """Extract individual entries from health log with dates and visit types"""
    entries = []
    
    # Look for date patterns followed by entry content
    # Pattern: Date, then entry details
    date_pattern = r'([A-Za-z]+\s+\d{1,2},?\s+\d{4}(?:\s*,\s*\d{1,2}:\d{2}\s*[AP]M)?)'
    
    lines = text.split('\n')
    current_entry = None
    current_date = None
    
    for line in lines:
        # Check for date
        date_match = re.search(date_pattern, line)
        if date_match:
            date_str = date_match.group(1)
            current_date = parse_date(date_str)
            
            # Start new entry
            if current_entry:
                entries.append(current_entry)
            
            current_entry = {
                'date': current_date,
                'text': line,
                'visit_type': None
            }
        elif current_entry:
            current_entry['text'] += '\n' + line
        
        # Determine visit type from entry text
        if current_entry:
            text_lower = current_entry['text'].lower()
            if any(word in text_lower for word in ['sick', 'illness', 'symptom', 'pain', 'fever', 'diagnosis', 'urgent', 'emergency']):
                current_entry['visit_type'] = 'sick_visit'
            elif any(word in text_lower for word in ['routine', 'checkup', 'well visit', 'annual', 'preventive', 'screening']):
                current_entry['visit_type'] = 'routine_visit'
    
    if current_entry:
        entries.append(current_entry)
    
    return entries


def process_health_log_metrics(source_id: int, text: str, db: GeneticProfileDB, dry_run: bool = False):
    """Process health log and extract all metrics with proper visit type tagging"""
    print(f"   📊 Extracting health metrics from health log...")
    if not dry_run:
        db.delete_health_metrics_for_source(source_id)
    
    total_metrics = 0
    
    # Tabular exports ("Blood Pressure" heading, then one dated row per reading)
    for reading in extract_health_log_table_readings(text):
        date = parse_date(reading['date_text'])
        if not date:
            continue
        metric = {
            'metric_type': reading['metric_type'],
            'metric_name': reading['metric_type'].replace('_', ' ').title(),
            'metric_value': reading['value'],
            'metric_value_text': reading['value_text'],
            'unit': reading['unit'],
            'collection_date': date,
            'collection_time': reading['time_text'],
            'visit_type': None,
            'notes': reading['notes'],
        }
        try:
            if not dry_run:
                db.add_health_metric(primary_source_id=source_id, **metric)
            total_metrics += 1
        except Exception as e:
            print(f"      ⚠️  Error adding table metric: {e}")
    print(f"   Found {total_metrics} tabular readings")
    
    # Extract entries
    entries = extract_health_log_entries(text)
    print(f"   Found {len(entries)} entries")
    
    # Extract metrics from each entry
    for entry in entries:
        entry_text = entry.get('text', '')
        entry_date = entry.get('date')
        visit_type = entry.get('visit_type')
        
        # Extract blood pressure
        bp_metrics = extract_blood_pressure(entry_text)
        for metric in bp_metrics:
            metric['collection_date'] = entry_date or metric.get('collection_date')
            metric['visit_type'] = visit_type or metric.get('visit_type')
            try:
                if not dry_run:
                    db.add_health_metric(primary_source_id=source_id, **metric)
                total_metrics += 1
            except Exception as e:
                print(f"      ⚠️  Error adding BP metric: {e}")
        
        # Extract temperature
        temp_metrics = extract_temperature(entry_text)
        for metric in temp_metrics:
            metric['collection_date'] = entry_date or metric.get('collection_date')
            metric['visit_type'] = visit_type or metric.get('visit_type')
            try:
                if not dry_run:
                    db.add_health_metric(primary_source_id=source_id, **metric)
                total_metrics += 1
            except Exception as e:
                print(f"      ⚠️  Error adding temp metric: {e}")
    
    print(f"   ✅ Extracted {total_metrics} health metrics")


def process_lab_results_metrics(source_id: int, text: str, db: GeneticProfileDB,
                                source_date: Optional[str] = None, dry_run: bool = False):
    """Process lab results and extract all values"""
    print(f"   🧪 Extracting lab values...")
    if not dry_run:
        db.delete_health_metrics_for_source(source_id)
    
    lab_metrics = extract_lab_values(text, source_date)
    
    # Determine visit type from context
    text_lower = text.lower()
    visit_type = None
    if any(word in text_lower for word in ['sick', 'illness', 'symptom', 'abnormal', 'urgent']):
        visit_type = 'sick_visit'
    elif any(word in text_lower for word in ['routine', 'checkup', 'well', 'annual', 'screening']):
        visit_type = 'routine_visit'
    
    # Add all lab metrics
    for metric in lab_metrics:
        metric['visit_type'] = visit_type
        try:
            if not dry_run:
                db.add_health_metric(primary_source_id=source_id, **metric)
        except Exception as e:
            print(f"      ⚠️  Error adding lab metric: {e}")
    
    print(f"   ✅ Extracted {len(lab_metrics)} lab values")


def main(dry_run: bool = False):
    """
    Process all primary sources and extract health metrics.

    Metrics for each processed source are replaced, so re-running does not
    duplicate rows. With dry_run=True nothing is written.
    """
    db = GeneticProfileDB()
    
    # Get all primary sources
    sources = db.get_all_primary_sources()
    
    print("=" * 80)
    print("EXTRACTING HEALTH METRICS")
    print("=" * 80)
    
    for source in sources:
        source_id = source['id']
        source_type = source['source_type']
        text = source.get('extracted_text', '')
        source_date = source.get('document_date')
        
        if not text or len(text) < 50:
            continue
        
        print(f"\n📄 Processing: {source['source_name']}")
        
        if source_type == 'health_log':
            process_health_log_metrics(source_id, text, db, dry_run=dry_run)
        elif source_type == 'lab_result':
            process_lab_results_metrics(source_id, text, db, source_date, dry_run=dry_run)
    
    # Show summary
    cursor = db.conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM health_metrics")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM health_metrics WHERE visit_type = 'routine_visit'")
    routine = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM health_metrics WHERE visit_type = 'sick_visit'")
    sick = cursor.fetchone()[0]
    
    print("\n" + "=" * 80)
    print("EXTRACTION COMPLETE")
    print("=" * 80)
    print(f"Total metrics: {total}")
    print(f"Routine visits: {routine}")
    print(f"Sick visits: {sick}")
    print(f"Unknown: {total - routine - sick}")
    
    db.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Extract health metrics from primary sources')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be extracted without writing to the database')
    args = parser.parse_args()
    main(dry_run=args.dry_run)

