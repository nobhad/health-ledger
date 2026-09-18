#!/usr/bin/env python3
"""
Extract and add ALL information from primary sources to the database.
Cross-references health logs with other documents to determine if entries were for sick visits.
"""

import pdfplumber
import json
import re
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from collections import defaultdict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from database_manager import GeneticProfileDB


def extract_pdf_text(pdf_path: str) -> str:
    """Extract text from PDF file"""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
    return text


def extract_metadata_from_filename(pdf_path: Path) -> dict:
    """Extract metadata from PDF filename"""
    pdf_name = pdf_path.stem
    parts = pdf_name.split('_')
    
    # Extract date from filename or parts
    date_str = None
    for part in parts:
        # Look for date patterns: YYYY-MM-DD or YYYYMMDD
        date_match = re.search(r'(\d{4}-\d{2}-\d{2}|\d{4}\d{2}\d{2})', part)
        if date_match:
            date_str = date_match.group(1)
            break
    
    # Determine document type
    doc_type = "unknown"
    if "HealthLogs" in pdf_name:
        doc_type = "health_log"
    elif "HealthIssues" in pdf_name:
        doc_type = "health_issue"
    elif "LabResults" in pdf_name or "PanelResults" in pdf_name:
        doc_type = "lab_result"
    elif "MedicalRecords" in pdf_name:
        doc_type = "medical_record"
    elif "GeneticTesting" in pdf_name:
        doc_type = "test_report"
    elif "NeuropsychologicalEvaluation" in pdf_name:
        doc_type = "evaluation"
    elif any(x in pdf_name for x in ["CT", "MR", "XR", "ECG"]):
        doc_type = "imaging"
    elif "AllergyTest" in pdf_name:
        doc_type = "test_report"
    elif "HealthSummary" in pdf_name:
        doc_type = "health_summary"
    
    # Extract institution
    institution = "Unknown"
    if "TuftsMed" in pdf_name:
        institution = "Tufts Medical Center"
    elif "BILH" in pdf_name:
        institution = "Beth Israel Lahey Health"
    elif "Genesight" in pdf_name or "GeneticTesting" in pdf_name:
        institution = "GeneSight (Myriad Neuroscience)"
    elif "CenterForHumanGenetics" in pdf_name:
        institution = "Center for Human Genetics"
    elif "NovaPsychiatricService" in pdf_name or "PrimeBehavioralHealth" in pdf_name:
        institution = "Nova Psychiatric Service / Prime Behavioral Health"
    elif "MelroseWakefield" in pdf_name:
        institution = "Melrose Wakefield Hospital"
    elif "Shields" in pdf_name:
        institution = "Shields Health Care"
    
    return {
        'filename': pdf_path.name,
        'filepath': str(pdf_path),
        'document_type': doc_type,
        'institution': institution,
        'date': date_str,
        'patient': parts[0] if parts else 'Unknown'
    }


def parse_health_log_entries(text: str) -> List[Dict]:
    """Parse health log text into individual entries"""
    entries = []
    
    # Look for date patterns and entry separators
    # Common patterns: dates, timestamps, entry markers
    date_pattern = r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})'
    
    # Split by potential entry boundaries
    # Look for lines that start with dates or common log patterns
    lines = text.split('\n')
    current_entry = None
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        
        # Check if line starts a new entry (date pattern, or common headers)
        date_match = re.search(date_pattern, line)
        if date_match or any(marker in line.lower() for marker in ['visit', 'appointment', 'symptom', 'complaint', 'chief complaint']):
            # Save previous entry if exists
            if current_entry and current_entry.get('text'):
                entries.append(current_entry)
            
            # Start new entry
            current_entry = {
                'date': date_match.group(1) if date_match else None,
                'text': line,
                'line_number': i
            }
        elif current_entry:
            # Continue current entry
            current_entry['text'] += ' ' + line
    
    # Add last entry
    if current_entry and current_entry.get('text'):
        entries.append(current_entry)
    
    return entries


def extract_dates_from_text(text: str) -> List[str]:
    """Extract all dates mentioned in text"""
    # Multiple date patterns
    patterns = [
        r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
        r'\d{1,2}/\d{1,2}/\d{4}',  # MM/DD/YYYY or M/D/YYYY
        r'\d{1,2}/\d{1,2}/\d{2}',  # MM/DD/YY
        r'\d{1,2}-\d{1,2}-\d{4}',  # MM-DD-YYYY
    ]
    
    dates = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        dates.extend(matches)
    
    return list(set(dates))


def extract_lab_results_info(text: str) -> Dict:
    """Extract ALL structured information from lab results - both normal and abnormal values"""
    info = {
        'test_names': [],
        'dates': extract_dates_from_text(text),
        'abnormal_values': [],
        'normal_values': [],
        'all_values': []  # ALL test values
    }
    
    # Enhanced patterns for test names and values
    # Pattern: Test Name: Value Unit (Reference Range)
    test_value_pattern = r'([A-Z][A-Za-z\s]+?)\s*:?\s*([\d\.]+)\s*([A-Za-z/%]+)?\s*(?:\(([\d\.]+)\s*-\s*([\d\.]+))?\)?'
    matches = re.findall(test_value_pattern, text)
    
    for match in matches:
        test_name = match[0].strip()
        value = match[1]
        unit = match[2] if match[2] else ''
        ref_min = match[3] if match[3] else None
        ref_max = match[4] if match[4] else None
        
        test_info = {
            'test_name': test_name,
            'value': value,
            'unit': unit,
            'ref_min': ref_min,
            'ref_max': ref_max
        }
        info['all_values'].append(test_info)
        
        if test_name not in info['test_names']:
            info['test_names'].append(test_name)
    
    # Look for abnormal values (marked with H, L, *, or "abnormal", "high", "low")
    abnormal_patterns = [
        r'([A-Z][A-Za-z\s]+?)\s*:?\s*([\d\.]+)\s*([HL\*])',
        r'([A-Z][A-Za-z\s]+?)\s*:?\s*([\d\.]+)\s*(?:\([^)]*\))?\s*(abnormal|high|low)',
    ]
    
    for pattern in abnormal_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        info['abnormal_values'].extend(matches)
    
    # Extract normal values (not marked as abnormal)
    for test_info in info['all_values']:
        test_name = test_info['test_name']
        # Check if this test is not in abnormal values
        is_abnormal = any(test_name in str(abn) for abn in info['abnormal_values'])
        if not is_abnormal:
            info['normal_values'].append(test_info)
    
    return info


def is_sick_visit(entry: Dict, cross_reference_data: Dict) -> Tuple[bool, str]:
    """
    Determine if a health log entry was for a sick visit.
    Cross-references with lab results, test results, and other documents.
    
    Returns: (is_sick_visit: bool, reason: str)
    """
    entry_text = entry.get('text', '').lower()
    entry_date = entry.get('date')
    
    # Keywords that suggest sick visit
    sick_keywords = [
        'sick', 'illness', 'symptom', 'pain', 'fever', 'infection',
        'nausea', 'vomiting', 'diarrhea', 'cough', 'cold', 'flu',
        'urgent', 'emergency', 'acute', 'complaint', 'chief complaint',
        'diagnosis', 'diagnosed', 'treatment', 'prescription', 'medication',
        'abnormal', 'elevated', 'decreased', 'test result', 'lab result'
    ]
    
    # Keywords that suggest routine/well visit
    routine_keywords = [
        'annual', 'routine', 'checkup', 'well visit', 'preventive',
        'screening', 'baseline', 'follow-up', 'monitoring', 'stable'
    ]
    
    # Check for sick keywords
    sick_score = sum(1 for keyword in sick_keywords if keyword in entry_text)
    routine_score = sum(1 for keyword in routine_keywords if keyword in entry_text)
    
    # Cross-reference with lab results
    if entry_date:
        # Check if there are lab results around the same date
        for lab_date, lab_info in cross_reference_data.get('lab_results', {}).items():
            if dates_match(entry_date, lab_date, days_threshold=7):
                if lab_info.get('abnormal_values'):
                    sick_score += 2
                    return True, f"Cross-referenced with abnormal lab results on {lab_date}"
    
    # Check for test results around the same time
    if entry_date:
        for test_date, test_info in cross_reference_data.get('test_results', {}).items():
            if dates_match(entry_date, test_date, days_threshold=7):
                if any(keyword in test_info.get('text', '').lower() for keyword in sick_keywords):
                    sick_score += 1
                    return True, f"Cross-referenced with test results on {test_date}"
    
    # Decision logic
    if sick_score > routine_score and sick_score > 0:
        return True, f"Contains sick visit keywords (score: {sick_score})"
    elif routine_score > sick_score:
        return False, f"Routine/well visit keywords (score: {routine_score})"
    elif sick_score > 0:
        return True, f"Contains sick visit indicators"
    else:
        return False, "No clear indicators"


def dates_match(date1: str, date2: str, days_threshold: int = 7) -> bool:
    """Check if two date strings are within days_threshold of each other"""
    try:
        # Try to parse dates in various formats
        def parse_date(d):
            for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%m/%d/%y', '%m-%d-%Y']:
                try:
                    return datetime.strptime(d, fmt)
                except:
                    continue
            return None
        
        d1 = parse_date(date1)
        d2 = parse_date(date2)
        
        if d1 and d2:
            diff = abs((d1 - d2).days)
            return diff <= days_threshold
        
        return False
    except:
        return False


def process_file(file_path: Path, db: GeneticProfileDB, cross_ref_data: Dict) -> Optional[int]:
    """Process a single file (any type) and add to database"""
    print(f"\nProcessing: {file_path.name} ({file_path.suffix})")
    
    text = ""
    metadata = {}
    
    # Extract text based on file type
    if file_path.suffix.lower() == '.pdf':
        text = extract_pdf_text(str(file_path))
        metadata = extract_metadata_from_filename(file_path)
    elif file_path.suffix.lower() in ['.tif', '.jpg', '.jpeg', '.png', '.bmp']:
        # Image file - use OCR
        try:
            from scripts.extract_images import process_image_file
            result = process_image_file(file_path)
            text = result.get('extracted_text', '')
            metadata = {
                'filename': file_path.name,
                'filepath': str(file_path),
                'document_type': 'imaging',
                'institution': 'Unknown',
                'date': None,
                'patient': 'Unknown'
            }
            # Merge image metadata
            img_meta = result.get('metadata', {})
            if 'exif_date' in img_meta:
                metadata['date'] = img_meta['exif_date']
        except ImportError:
            print(f"   Warning: OCR not available. Install pytesseract to extract text from images.")
            text = ""
            metadata = {
                'filename': file_path.name,
                'filepath': str(file_path),
                'document_type': 'imaging',
                'institution': 'Unknown',
                'date': None,
                'patient': 'Unknown'
            }
    elif file_path.suffix.lower() in ['.txt', '.log']:
        # Text file
        try:
            from scripts.extract_text_files import process_text_file
            result = process_text_file(file_path)
            text = result.get('extracted_text', '')
            metadata = {
                'filename': file_path.name,
                'filepath': str(file_path),
                'document_type': 'health_log' if file_path.suffix.lower() == '.log' else 'text_file',
                'institution': 'Unknown',
                'date': result.get('dates_found', [None])[0] if result.get('dates_found') else None,
                'patient': 'Unknown'
            }
        except Exception as e:
            print(f"   Error processing text file: {e}")
            text = ""
            metadata = {
                'filename': file_path.name,
                'filepath': str(file_path),
                'document_type': 'text_file',
                'institution': 'Unknown',
                'date': None,
                'patient': 'Unknown'
            }
    elif file_path.suffix.lower() == '.dcm':
        # DICOM file
        try:
            from scripts.extract_dicom import process_dicom_file
            result = process_dicom_file(file_path)
            text = result.get('extracted_text', '')
            dicom_meta = result.get('metadata', {})
            metadata = {
                'filename': file_path.name,
                'filepath': str(file_path),
                'document_type': 'imaging',
                'institution': dicom_meta.get('institution_name', 'Unknown'),
                'date': dicom_meta.get('study_date', None),
                'patient': dicom_meta.get('patient_name', 'Unknown')
            }
        except ImportError:
            print(f"   Warning: pydicom not available. Install pydicom to extract DICOM metadata.")
            text = ""
            metadata = {
                'filename': file_path.name,
                'filepath': str(file_path),
                'document_type': 'imaging',
                'institution': 'Unknown',
                'date': None,
                'patient': 'Unknown'
            }
    else:
        print(f"   Warning: Unsupported file type: {file_path.suffix}")
        return None
    
    if not text or len(text.strip()) < 10:
        print(f"   Warning: Could not extract meaningful text")
        # Still add to database with minimal info
        text = f"File: {file_path.name} (no text extracted)"
    
    # Get next citation number if needed
    cursor = db.conn.cursor()
    cursor.execute("SELECT MAX(citation_number) FROM citations")
    result = cursor.fetchone()
    next_citation = (result[0] if result[0] else 0) + 1
    
    # Add as citation if it's a significant document
    citation_id = None
    if metadata['document_type'] in ['medical_record', 'test_report', 'evaluation', 'health_summary']:
        try:
            year = None
            if metadata.get('date'):
                try:
                    year = int(metadata['date'][:4])
                except:
                    pass
            
            citation_id = db.add_reference(
                citation_number=next_citation,
                authors=metadata['institution'],
                year=year,
                title=metadata['filename'].replace('_', ' ').replace(file_path.suffix, ''),
                url=str(file_path),
                reference_type="primary_source"
            )
            print(f"   Added as citation #{next_citation}")
        except Exception as e:
            print(f"   ⚠️  Could not add citation: {e}")
    
    # Add to primary_sources table
    try:
        source_id = db.add_primary_source(
            source_name=metadata['filename'],
            source_type=metadata['document_type'],
            institution=metadata['institution'],
            patient_name=metadata.get('patient'),
            document_date=metadata.get('date'),
            file_path=str(file_path),
            file_name=metadata['filename'],
            extracted_text=text[:50000] if len(text) > 50000 else text,  # Limit text size
            metadata=json.dumps(metadata),
            citation_id=citation_id
        )
        print(f"   Added to primary_sources (ID: {source_id})")
        
        # Process specific document types
        if metadata['document_type'] == 'health_log':
            process_health_log(source_id, text, db, cross_ref_data)
        elif metadata['document_type'] == 'lab_result':
            process_lab_result(source_id, text, db, cross_ref_data)
        elif metadata['document_type'] in ['test_report', 'imaging', 'evaluation']:
            process_test_result(source_id, text, db, metadata)
        
        return source_id
    except Exception as e:
        print(f"   Error adding to database: {e}")
        import traceback
        traceback.print_exc()
        return None


def process_health_log(source_id: int, text: str, db: GeneticProfileDB, cross_ref_data: Dict):
    """Process health log entries and determine if they were sick visits"""
    print(f"   📝 Processing health log entries...")
    
    entries = parse_health_log_entries(text)
    print(f"   Found {len(entries)} potential entries")
    
    for i, entry in enumerate(entries):
        is_sick, reason = is_sick_visit(entry, cross_ref_data)
        
        finding_type = "sick_visit" if is_sick else "routine_visit"
        
        try:
            finding_id = db.add_primary_source_finding(
                primary_source_id=source_id,
                finding_text=entry['text'][:2000],  # Limit length
                finding_type=finding_type,
                finding_date=entry.get('date'),
                notes=f"Visit type: {'Sick visit' if is_sick else 'Routine visit'}. {reason}"
            )
            
            if i < 5:  # Show first 5 entries
                status = "🏥 SICK VISIT" if is_sick else "✅ Routine"
                print(f"      {status}: {entry.get('date', 'No date')} - {entry['text'][:80]}...")
        except Exception as e:
            print(f"      ⚠️  Error adding finding: {e}")


def process_lab_result(source_id: int, text: str, db: GeneticProfileDB, cross_ref_data: Dict):
    """Process lab results and add to cross-reference data"""
    print(f"   🧪 Processing lab results...")
    
    lab_info = extract_lab_results_info(text)
    dates = lab_info.get('dates', [])
    
    # Add to cross-reference data
    for date in dates:
        if date not in cross_ref_data['lab_results']:
            cross_ref_data['lab_results'][date] = lab_info
    
    # Add findings for ALL values (both normal and abnormal)
    # This ensures we capture everything, not just abnormal values
    if lab_info.get('all_values'):
        for test_info in lab_info['all_values']:
            test_name = test_info.get('test_name', 'Unknown')
            value = test_info.get('value', '')
            unit = test_info.get('unit', '')
            ref_range = ""
            if test_info.get('ref_min') and test_info.get('ref_max'):
                ref_range = f" (Ref: {test_info['ref_min']}-{test_info['ref_max']})"
            
            finding_text = f"{test_name}: {value} {unit}{ref_range}"
            finding_type = "lab_result"
            
            # Check if abnormal
            is_abnormal = any(
                test_name in str(abn[0]) for abn in lab_info.get('abnormal_values', [])
            )
            if is_abnormal:
                finding_type = "abnormal_lab_result"
            
            try:
                db.add_primary_source_finding(
                    primary_source_id=source_id,
                    finding_text=finding_text,
                    finding_type=finding_type,
                    notes=f"Lab test value - {'Abnormal' if is_abnormal else 'Normal'}"
                )
            except Exception as e:
                print(f"      Warning: Error adding lab finding: {e}")
    
    # Also add abnormal values specifically for easy filtering
    if lab_info.get('abnormal_values'):
        for abnormal in lab_info['abnormal_values']:
            if len(abnormal) >= 2:
                test_name = str(abnormal[0])
                value = str(abnormal[1])
                flag = str(abnormal[2]) if len(abnormal) > 2 else ''
                try:
                    db.add_primary_source_finding(
                        primary_source_id=source_id,
                        finding_text=f"{test_name}: {value} ({flag})",
                        finding_type="abnormal_lab_result",
                        notes="Abnormal lab value - flagged"
                    )
                except Exception as e:
                    pass


def process_test_result(source_id: int, text: str, db: GeneticProfileDB, metadata: Dict):
    """Process test results and evaluations"""
    print(f"   🔬 Processing test results...")
    
    # Extract key findings
    sentences = re.split(r'[.!?]+', text)
    key_findings = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 30 and len(sentence) < 500:
            # Look for diagnostic language
            if any(term in sentence.lower() for term in ['diagnosis', 'finding', 'result', 'abnormal', 'normal', 'positive', 'negative']):
                key_findings.append(sentence)
    
    # Add up to 10 key findings
    for finding in key_findings[:10]:
        try:
            db.add_primary_source_finding(
                primary_source_id=source_id,
                finding_text=finding,
                finding_type="test_result",
                notes=f"From {metadata['document_type']}"
            )
        except:
            pass


def main():
    """Main function to process all primary sources - ALL FILE TYPES"""
    db = GeneticProfileDB()
    
    primary_sources_dir = Path("primary_sources")
    if not primary_sources_dir.exists():
        print(f"Error: {primary_sources_dir} directory not found")
        return
    
    # Get ALL file types (not just PDFs)
    all_files = []
    all_files.extend(primary_sources_dir.glob("*.pdf"))
    all_files.extend(primary_sources_dir.glob("*.tif"))
    all_files.extend(primary_sources_dir.glob("*.TIF"))
    all_files.extend(primary_sources_dir.glob("*.jpg"))
    all_files.extend(primary_sources_dir.glob("*.jpeg"))
    all_files.extend(primary_sources_dir.glob("*.png"))
    all_files.extend(primary_sources_dir.glob("*.txt"))
    all_files.extend(primary_sources_dir.glob("*.log"))
    all_files.extend(primary_sources_dir.glob("*.dcm"))
    all_files.extend(primary_sources_dir.glob("*.DCM"))
    
    # Remove directories from list
    all_files = [f for f in all_files if f.is_file()]
    all_files.sort()
    
    print("=" * 80)
    print("EXTRACTING ALL PRIMARY SOURCES - ALL FILE TYPES")
    print("=" * 80)
    print(f"\nFound {len(all_files)} files to process")
    
    # Count by type
    pdf_count = len([f for f in all_files if f.suffix.lower() == '.pdf'])
    image_count = len([f for f in all_files if f.suffix.lower() in ['.tif', '.jpg', '.jpeg', '.png']])
    text_count = len([f for f in all_files if f.suffix.lower() in ['.txt', '.log']])
    dicom_count = len([f for f in all_files if f.suffix.lower() == '.dcm'])
    print(f"  PDF files: {pdf_count}")
    print(f"  Image files: {image_count}")
    print(f"  Text files: {text_count}")
    print(f"  DICOM files: {dicom_count}")
    
    # Cross-reference data structure
    cross_ref_data = {
        'lab_results': {},
        'test_results': {},
        'visit_dates': []
    }
    
    # First pass: Extract lab results and test results for cross-referencing
    print("\n" + "=" * 80)
    print("PASS 1: Extracting lab results and test data for cross-referencing")
    print("=" * 80)
    
    for file_path in all_files:
        if file_path.suffix.lower() == '.pdf':
            metadata = extract_metadata_from_filename(file_path)
            if metadata['document_type'] in ['lab_result', 'test_report', 'imaging']:
                text = extract_pdf_text(str(file_path))
                if text:
                    if metadata['document_type'] == 'lab_result':
                        lab_info = extract_lab_results_info(text)
                        dates = lab_info.get('dates', [])
                        for date in dates:
                            cross_ref_data['lab_results'][date] = lab_info
                    else:
                        dates = extract_dates_from_text(text)
                        for date in dates:
                            cross_ref_data['test_results'][date] = {'text': text[:500]}
    
    print(f"   Extracted {len(cross_ref_data['lab_results'])} lab result dates")
    print(f"   Extracted {len(cross_ref_data['test_results'])} test result dates")
    
    # Second pass: Process ALL files
    print("\n" + "=" * 80)
    print("PASS 2: Processing all primary sources (ALL FILE TYPES)")
    print("=" * 80)
    
    processed_count = 0
    for file_path in all_files:
        source_id = process_file(file_path, db, cross_ref_data)
        if source_id:
            processed_count += 1
    
    print("\n" + "=" * 80)
    print("PROCESSING COMPLETE")
    print("=" * 80)
    print(f"   ✅ Processed {processed_count} of {len(pdf_files)} files")
    
    # Show summary
    cursor = db.conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM primary_sources")
    total_sources = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM primary_source_findings")
    total_findings = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM primary_source_findings WHERE finding_type = 'sick_visit'")
    sick_visits = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM primary_source_findings WHERE finding_type = 'routine_visit'")
    routine_visits = cursor.fetchone()[0]
    
    print(f"\n📊 Database Summary:")
    print(f"   Primary Sources: {total_sources}")
    print(f"   Total Findings: {total_findings}")
    print(f"   Sick Visits: {sick_visits}")
    print(f"   Routine Visits: {routine_visits}")
    
    db.close()


if __name__ == "__main__":
    main()

