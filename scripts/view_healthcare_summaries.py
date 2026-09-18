#!/usr/bin/env python3
"""
View healthcare summaries from the database.
Shows all appointments and allows filtering by date, doctor, visit type, etc.
"""

import sys
from pathlib import Path
from datetime import datetime
import json
from typing import List, Dict, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from database_manager import GeneticProfileDB


def format_date(date_str: Optional[str]) -> str:
    """Format date string for display"""
    if not date_str:
        return "No date"
    
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        return dt.strftime('%B %d, %Y')
    except:
        return date_str


def display_summary(source: Dict, findings: List[Dict]):
    """Display a healthcare summary"""
    print("\n" + "=" * 80)
    print(f"📋 {source['source_name']}")
    print("=" * 80)
    
    metadata = json.loads(source.get('metadata', '{}'))
    
    print(f"Date: {format_date(source.get('document_date'))}")
    print(f"Institution: {source.get('institution', 'Unknown')}")
    if metadata.get('doctor'):
        print(f"Doctor: {metadata.get('doctor')}")
    if metadata.get('visit_type'):
        visit_type = metadata.get('visit_type', '').replace('_', ' ').title()
        print(f"Visit Type: {visit_type}")
    
    print("\nFindings:")
    for finding in findings:
        finding_type = finding.get('finding_type', '').replace('_', ' ').title()
        print(f"\n  [{finding_type}]")
        print(f"  {finding.get('finding_text', '')}")
        if finding.get('related_condition'):
            print(f"  Related Condition: {finding.get('related_condition')}")
        if finding.get('notes'):
            print(f"  Notes: {finding.get('notes')}")


def list_summaries(db: GeneticProfileDB, limit: Optional[int] = None, 
                   visit_type: Optional[str] = None, 
                   start_date: Optional[str] = None,
                   end_date: Optional[str] = None):
    """List all healthcare summaries with optional filters"""
    
    sources = db.get_all_primary_sources()
    
    # Filter by type
    healthcare_summaries = [s for s in sources if s.get('source_type') == 'healthcare_summary']
    
    # Apply filters
    if visit_type:
        filtered = []
        for s in healthcare_summaries:
            metadata = json.loads(s.get('metadata', '{}'))
            if metadata.get('visit_type') == visit_type:
                filtered.append(s)
        healthcare_summaries = filtered
    
    if start_date:
        healthcare_summaries = [s for s in healthcare_summaries 
                               if s.get('document_date') and s.get('document_date') >= start_date]
    
    if end_date:
        healthcare_summaries = [s for s in healthcare_summaries 
                               if s.get('document_date') and s.get('document_date') <= end_date]
    
    # Sort by date (newest first)
    healthcare_summaries.sort(key=lambda x: x.get('document_date', ''), reverse=True)
    
    # Apply limit
    if limit:
        healthcare_summaries = healthcare_summaries[:limit]
    
    print("=" * 80)
    print(f"HEALTHCARE SUMMARIES ({len(healthcare_summaries)} found)")
    print("=" * 80)
    
    if not healthcare_summaries:
        print("\nNo healthcare summaries found.")
        return
    
    for source in healthcare_summaries:
        findings = db.get_primary_source_findings(source['id'])
        display_summary(source, findings)
    
    # Summary statistics
    print("\n" + "=" * 80)
    print("STATISTICS")
    print("=" * 80)
    
    visit_types = {}
    for s in healthcare_summaries:
        metadata = json.loads(s.get('metadata', '{}'))
        vtype = metadata.get('visit_type', 'unknown')
        visit_types[vtype] = visit_types.get(vtype, 0) + 1
    
    for vtype, count in sorted(visit_types.items()):
        print(f"  {vtype.replace('_', ' ').title()}: {count}")


def main():
    """Main function"""
    db = GeneticProfileDB()
    
    # Check for command-line arguments
    limit = None
    visit_type = None
    start_date = None
    end_date = None
    
    if len(sys.argv) > 1:
        for i, arg in enumerate(sys.argv[1:], 1):
            if arg == '--limit' and i + 1 < len(sys.argv):
                limit = int(sys.argv[i + 1])
            elif arg == '--type' and i + 1 < len(sys.argv):
                visit_type = sys.argv[i + 1]
            elif arg == '--start' and i + 1 < len(sys.argv):
                start_date = sys.argv[i + 1]
            elif arg == '--end' and i + 1 < len(sys.argv):
                end_date = sys.argv[i + 1]
            elif arg == '--sick':
                visit_type = 'sick_visit'
            elif arg == '--routine':
                visit_type = 'routine_visit'
    
    list_summaries(db, limit=limit, visit_type=visit_type, 
                   start_date=start_date, end_date=end_date)
    
    db.close()


if __name__ == "__main__":
    main()

