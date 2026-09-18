#!/usr/bin/env python3
"""
Add healthcare summary after a doctor's appointment.
Easy-to-use script for adding visit information to the database.
"""

import sys
from pathlib import Path
from datetime import datetime
import json
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from database_manager import GeneticProfileDB


def prompt_user(prompt: str, default: Optional[str] = None, required: bool = False) -> str:
    """Prompt user for input with optional default"""
    if default:
        full_prompt = f"{prompt} [{default}]: "
    else:
        full_prompt = f"{prompt}: "
    
    while True:
        response = input(full_prompt).strip()
        if response:
            return response
        elif default:
            return default
        elif not required:
            return ""
        else:
            print("   This field is required. Please enter a value.")


def prompt_yes_no(prompt: str, default: bool = True) -> bool:
    """Prompt for yes/no with default"""
    default_str = "Y/n" if default else "y/N"
    response = input(f"{prompt} [{default_str}]: ").strip().lower()
    
    if not response:
        return default
    return response in ['y', 'yes', '1', 'true']


def get_visit_type() -> str:
    """Determine visit type"""
    print("\n📋 Visit Type:")
    print("   1. Sick visit (illness, symptoms, acute issue)")
    print("   2. Routine visit (checkup, follow-up, preventive)")
    print("   3. Emergency visit")
    print("   4. Specialist consultation")
    print("   5. Other")
    
    choice = prompt_user("Select visit type (1-5)", default="1")
    
    type_map = {
        "1": "sick_visit",
        "2": "routine_visit",
        "3": "emergency_visit",
        "4": "specialist_consultation",
        "5": "other_visit"
    }
    
    return type_map.get(choice, "sick_visit")


def format_date(date_str: str) -> Optional[str]:
    """Try to format date string to YYYY-MM-DD"""
    if not date_str:
        return None
    
    # Try various formats
    formats = [
        '%Y-%m-%d',
        '%m/%d/%Y',
        '%m/%d/%y',
        '%m-%d-%Y',
        '%m-%d-%y',
        '%Y/%m/%d'
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime('%Y-%m-%d')
        except:
            continue
    
    # If can't parse, return as-is
    return date_str


def add_healthcare_summary():
    """Interactive script to add healthcare summary"""
    db = GeneticProfileDB()
    
    print("=" * 80)
    print("ADD HEALTHCARE SUMMARY")
    print("=" * 80)
    print("\nThis script helps you add a summary of your doctor's appointment.")
    print("You can add visit details, symptoms, diagnoses, treatments, and more.\n")
    
    # Get basic information
    visit_date = prompt_user("Visit date (YYYY-MM-DD or MM/DD/YYYY)", 
                            default=datetime.now().strftime('%Y-%m-%d'))
    visit_date = format_date(visit_date)
    
    doctor_name = prompt_user("Doctor/Provider name", required=True)
    institution = prompt_user("Institution/Clinic name", default="")
    
    visit_type = get_visit_type()
    
    # Get visit details
    print("\n📝 Visit Details:")
    chief_complaint = prompt_user("Chief complaint / Reason for visit")
    symptoms = prompt_user("Symptoms (if any)")
    diagnosis = prompt_user("Diagnosis / Assessment")
    treatment = prompt_user("Treatment / Plan")
    medications = prompt_user("Medications prescribed/changed")
    follow_up = prompt_user("Follow-up instructions")
    notes = prompt_user("Additional notes")
    
    # Ask about related documents
    print("\n📎 Related Documents:")
    has_lab_results = prompt_yes_no("Were lab results ordered/received?", default=False)
    lab_result_file = None
    if has_lab_results:
        lab_result_file = prompt_user("Lab result file path (if available)")
    
    has_test_results = prompt_yes_no("Were tests/scans ordered?", default=False)
    test_result_file = None
    if has_test_results:
        test_result_file = prompt_user("Test/scan file path (if available)")
    
    # Create summary text
    summary_parts = []
    if chief_complaint:
        summary_parts.append(f"Chief Complaint: {chief_complaint}")
    if symptoms:
        summary_parts.append(f"Symptoms: {symptoms}")
    if diagnosis:
        summary_parts.append(f"Diagnosis: {diagnosis}")
    if treatment:
        summary_parts.append(f"Treatment: {treatment}")
    if medications:
        summary_parts.append(f"Medications: {medications}")
    if follow_up:
        summary_parts.append(f"Follow-up: {follow_up}")
    if notes:
        summary_parts.append(f"Notes: {notes}")
    
    summary_text = "\n\n".join(summary_parts)
    
    # Create source name
    source_name = f"Healthcare Summary - {doctor_name} - {visit_date}"
    
    # Prepare metadata
    metadata = {
        'doctor': doctor_name,
        'institution': institution,
        'visit_type': visit_type,
        'chief_complaint': chief_complaint,
        'diagnosis': diagnosis,
        'treatment': treatment,
        'medications': medications,
        'lab_result_file': lab_result_file,
        'test_result_file': test_result_file
    }
    
    # Add to database
    print("\n" + "=" * 80)
    print("ADDING TO DATABASE...")
    print("=" * 80)
    
    try:
        # Add as primary source
        source_id = db.add_primary_source(
            source_name=source_name,
            source_type="healthcare_summary",
            institution=institution,
            patient_name=None,
            document_date=visit_date,
            file_path=None,
            file_name=None,
            extracted_text=summary_text,
            metadata=json.dumps(metadata),
            citation_id=None
        )
        
        print(f"✅ Added primary source (ID: {source_id})")
        
        # Add main finding
        finding_text = f"Visit with {doctor_name} at {institution}"
        if chief_complaint:
            finding_text += f"\nChief Complaint: {chief_complaint}"
        if diagnosis:
            finding_text += f"\nDiagnosis: {diagnosis}"
        
        finding_id = db.add_primary_source_finding(
            primary_source_id=source_id,
            finding_text=finding_text,
            finding_type=visit_type,
            finding_date=visit_date,
            related_condition=diagnosis if diagnosis else None,
            notes=f"Doctor: {doctor_name}. Institution: {institution}."
        )
        
        print(f"✅ Added finding (ID: {finding_id})")
        
        # Add additional findings for key information
        if symptoms:
            db.add_primary_source_finding(
                primary_source_id=source_id,
                finding_text=f"Symptoms: {symptoms}",
                finding_type="symptom",
                finding_date=visit_date
            )
        
        if treatment:
            db.add_primary_source_finding(
                primary_source_id=source_id,
                finding_text=f"Treatment/Plan: {treatment}",
                finding_type="treatment",
                finding_date=visit_date
            )
        
        if medications:
            db.add_primary_source_finding(
                primary_source_id=source_id,
                finding_text=f"Medications: {medications}",
                finding_type="medication",
                finding_date=visit_date
            )
        
        if follow_up:
            db.add_primary_source_finding(
                primary_source_id=source_id,
                finding_text=f"Follow-up: {follow_up}",
                finding_type="follow_up",
                finding_date=visit_date
            )
        
        print("\n" + "=" * 80)
        print("✅ HEALTHCARE SUMMARY ADDED SUCCESSFULLY")
        print("=" * 80)
        print(f"\nSummary:")
        print(f"   Date: {visit_date}")
        print(f"   Doctor: {doctor_name}")
        print(f"   Institution: {institution}")
        print(f"   Visit Type: {visit_type.replace('_', ' ').title()}")
        if diagnosis:
            print(f"   Diagnosis: {diagnosis}")
        
        # Ask if they want to link to lab/test results
        if lab_result_file or test_result_file:
            link_docs = prompt_yes_no("\nLink to lab/test result files?", default=True)
            if link_docs:
                # This could be enhanced to actually process the files
                print("   Note: File linking feature can be enhanced to automatically")
                print("   extract and cross-reference data from lab/test result files.")
        
    except Exception as e:
        print(f"\n❌ Error adding to database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


def quick_add_summary(date: str, doctor: str, complaint: str, diagnosis: str = "", 
                     institution: str = "", visit_type: str = "sick_visit"):
    """
    Quick function to add summary programmatically (for automation/scripts)
    
    Args:
        date: Visit date (YYYY-MM-DD)
        doctor: Doctor name
        complaint: Chief complaint
        diagnosis: Diagnosis (optional)
        institution: Institution name
        visit_type: Type of visit (sick_visit, routine_visit, etc.)
    """
    db = GeneticProfileDB()
    
    source_name = f"Healthcare Summary - {doctor} - {date}"
    summary_text = f"Chief Complaint: {complaint}"
    if diagnosis:
        summary_text += f"\nDiagnosis: {diagnosis}"
    
    metadata = {
        'doctor': doctor,
        'institution': institution,
        'visit_type': visit_type,
        'chief_complaint': complaint,
        'diagnosis': diagnosis
    }
    
    try:
        source_id = db.add_primary_source(
            source_name=source_name,
            source_type="healthcare_summary",
            institution=institution,
            patient_name=None,
            document_date=date,
            extracted_text=summary_text,
            metadata=json.dumps(metadata),
            citation_id=None
        )
        
        db.add_primary_source_finding(
            primary_source_id=source_id,
            finding_text=f"Visit with {doctor}: {complaint}",
            finding_type=visit_type,
            finding_date=date,
            related_condition=diagnosis if diagnosis else None
        )
        
        return source_id
    finally:
        db.close()


if __name__ == "__main__":
    # Check for command-line arguments for quick add
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        if len(sys.argv) < 5:
            print("Usage: add_healthcare_summary.py --quick <date> <doctor> <complaint> [diagnosis]")
            sys.exit(1)
        
        date = sys.argv[2]
        doctor = sys.argv[3]
        complaint = sys.argv[4]
        diagnosis = sys.argv[5] if len(sys.argv) > 5 else ""
        
        source_id = quick_add_summary(date, doctor, complaint, diagnosis)
        print(f"✅ Added summary (ID: {source_id})")
    else:
        # Interactive mode
        add_healthcare_summary()

