#!/usr/bin/env python3
"""
Extract metadata and text from DICOM files
Medical imaging format (.dcm files)
"""

import sys
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import get_logger

logger = get_logger('extract_dicom')

try:
    import pydicom
    from pydicom.dataset import Dataset
    DICOM_AVAILABLE = True
except ImportError:
    DICOM_AVAILABLE = False
    logger.warning("pydicom not available. Install with: pip install pydicom")


def extract_dicom_metadata(dicom_path: Path) -> Dict:
    """
    Extract metadata from DICOM file.
    
    Args:
        dicom_path: Path to DICOM file
        
    Returns:
        Dictionary with DICOM metadata
    """
    if not DICOM_AVAILABLE:
        logger.error("pydicom not available. Cannot extract DICOM metadata.")
        return {}
    
    try:
        ds = pydicom.dcmread(str(dicom_path))
        
        metadata = {
            'file_name': dicom_path.name,
            'file_size': dicom_path.stat().st_size,
            'modality': getattr(ds, 'Modality', 'Unknown'),
            'study_date': getattr(ds, 'StudyDate', None),
            'study_time': getattr(ds, 'StudyTime', None),
            'patient_name': str(getattr(ds, 'PatientName', 'Unknown')),
            'patient_id': getattr(ds, 'PatientID', None),
            'patient_birth_date': getattr(ds, 'PatientBirthDate', None),
            'patient_sex': getattr(ds, 'PatientSex', None),
            'study_description': getattr(ds, 'StudyDescription', None),
            'series_description': getattr(ds, 'SeriesDescription', None),
            'institution_name': getattr(ds, 'InstitutionName', None),
            'manufacturer': getattr(ds, 'Manufacturer', None),
            'model_name': getattr(ds, 'ManufacturerModelName', None),
        }
        
        # Extract report text if available
        report_text = None
        if hasattr(ds, 'ImagingReport'):
            report_text = str(ds.ImagingReport)
        elif hasattr(ds, 'Report'):
            report_text = str(ds.Report)
        elif hasattr(ds, 'StudyComments'):
            report_text = str(ds.StudyComments)
        
        if report_text:
            metadata['report_text'] = report_text
        
        # Extract findings/measurements if available
        findings = []
        if hasattr(ds, 'Findings'):
            findings.append(str(ds.Findings))
        if hasattr(ds, 'FindingsFlag'):
            findings.append(f"Findings Flag: {ds.FindingsFlag}")
        
        if findings:
            metadata['findings'] = findings
        
        logger.info(f"Extracted metadata from DICOM: {dicom_path.name}")
        return metadata
        
    except Exception as e:
        logger.error(f"Error extracting DICOM metadata from {dicom_path}: {e}", exc_info=True)
        return {}


def process_dicom_file(dicom_path: Path) -> Dict:
    """
    Process a DICOM file and extract all information.
    
    Args:
        dicom_path: Path to DICOM file
        
    Returns:
        Dictionary with extracted metadata and text
    """
    result = {
        'file_path': str(dicom_path),
        'file_name': dicom_path.name,
        'metadata': extract_dicom_metadata(dicom_path)
    }
    
    # Extract report text if available
    if 'report_text' in result['metadata']:
        result['extracted_text'] = result['metadata']['report_text']
    else:
        result['extracted_text'] = ""
    
    return result


def process_dicomdir(dicomdir_path: Path) -> List[Dict]:
    """
    Process a DICOMDIR file and extract information about all studies.
    
    Args:
        dicomdir_path: Path to DICOMDIR file
        
    Returns:
        List of dictionaries with study information
    """
    if not DICOM_AVAILABLE:
        logger.error("pydicom not available. Cannot process DICOMDIR.")
        return []
    
    try:
        ds = pydicom.dcmread(str(dicomdir_path))
        
        studies = []
        if hasattr(ds, 'DirectoryRecordSequence'):
            for record in ds.DirectoryRecordSequence:
                study_info = {
                    'record_type': getattr(record, 'DirectoryRecordType', 'Unknown'),
                    'study_date': getattr(record, 'StudyDate', None),
                    'study_description': getattr(record, 'StudyDescription', None),
                    'patient_name': str(getattr(record, 'PatientName', 'Unknown')),
                }
                studies.append(study_info)
        
        logger.info(f"Extracted {len(studies)} studies from DICOMDIR")
        return studies
        
    except Exception as e:
        logger.error(f"Error processing DICOMDIR {dicomdir_path}: {e}", exc_info=True)
        return []


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract metadata from DICOM files')
    parser.add_argument('dicom_path', type=str, help='Path to DICOM file or DICOMDIR')
    
    args = parser.parse_args()
    
    dicom_path = Path(args.dicom_path)
    if not dicom_path.exists():
        print(f"Error: DICOM file not found: {dicom_path}")
        sys.exit(1)
    
    if dicom_path.name.upper() == 'DICOMDIR':
        studies = process_dicomdir(dicom_path)
        print(f"Found {len(studies)} studies in DICOMDIR")
        for study in studies:
            print(f"  {study}")
    else:
        result = process_dicom_file(dicom_path)
        print(f"Metadata: {result['metadata']}")
        if result['extracted_text']:
            print(f"\nExtracted text:\n{result['extracted_text']}")

