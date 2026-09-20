#!/usr/bin/env python3
"""
Centralized Extraction Patterns
Defines patterns for extracting structured data from various document types
Easy to update and extend
"""

import re
from typing import List, Dict, Tuple


# Date Patterns
DATE_PATTERNS = [
    r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
    r'\d{1,2}/\d{1,2}/\d{4}',  # MM/DD/YYYY or M/D/YYYY
    r'\d{1,2}/\d{1,2}/\d{2}',  # MM/DD/YY
    r'\d{1,2}-\d{1,2}-\d{4}',  # MM-DD-YYYY
    r'[A-Z][a-z]+\s+\d{1,2},?\s+\d{4}',  # Month Day, Year
    r'[A-Z][a-z]+\s+\d{1,2},?\s+\d{2}',  # Month Day, YY
]


def extract_dates(text: str) -> List[str]:
    """Extract all dates from text using centralized patterns"""
    dates = []
    for pattern in DATE_PATTERNS:
        matches = re.findall(pattern, text)
        dates.extend(matches)
    return list(set(dates))  # Remove duplicates


# Lab Result Patterns
LAB_TEST_PATTERNS = {
    'test_name_value': r'([A-Z][A-Za-z\s]+?)\s*:?\s*([\d\.]+)\s*([A-Za-z/%]+)?',
    'test_with_range': r'([A-Z][A-Za-z\s]+?)\s*:?\s*([\d\.]+)\s*([A-Za-z/%]+)?\s*\(([\d\.]+)\s*-\s*([\d\.]+)\)',
    'abnormal_marker': r'([HL\*]|abnormal|high|low|elevated|decreased)',
    'test_acronym': r'([A-Z]{2,}(?:\s+[A-Z]+)*)\s*:?\s*[\d\.]+',
}


def extract_lab_values(text: str) -> List[Dict]:
    """
    Extract lab test values from text.
    
    Returns:
        List of dictionaries with test_name, value, unit, ref_min, ref_max
    """
    results = []
    
    # Pattern: Test Name: Value Unit (Reference Range)
    pattern = r'([A-Z][A-Za-z\s]+?)\s*:?\s*([\d\.]+)\s*([A-Za-z/%]+)?\s*(?:\(([\d\.]+)\s*-\s*([\d\.]+))?\)?'
    
    for match in re.finditer(pattern, text):
        test_name = match.group(1).strip()
        value = match.group(2)
        unit = match.group(3) if match.group(3) else ''
        ref_min = match.group(4) if match.group(4) else None
        ref_max = match.group(5) if match.group(5) else None
        
        results.append({
            'test_name': test_name,
            'value': value,
            'unit': unit,
            'ref_min': ref_min,
            'ref_max': ref_max
        })
    
    return results


def extract_abnormal_lab_values(text: str) -> List[Tuple[str, str, str]]:
    """
    Extract abnormal lab values (marked with H, L, *, or keywords).
    
    Returns:
        List of tuples: (test_name, value, flag)
    """
    results = []
    
    patterns = [
        r'([A-Z][A-Za-z\s]+?)\s*:?\s*([\d\.]+)\s*([HL\*])',
        r'([A-Z][A-Za-z\s]+?)\s*:?\s*([\d\.]+)\s*(?:\([^)]*\))?\s*(abnormal|high|low|elevated|decreased)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        results.extend(matches)
    
    return results


# Health Log Entry Patterns
HEALTH_LOG_MARKERS = [
    'visit', 'appointment', 'symptom', 'complaint', 'chief complaint',
    'diagnosis', 'treatment', 'medication', 'follow-up', 'follow up',
    'note:', 'notes:', 'date:', 'seen for', 'presented with'
]


def is_health_log_entry_start(line: str) -> bool:
    """Check if a line starts a new health log entry"""
    line_lower = line.lower().strip()
    
    # Check for date patterns
    for pattern in DATE_PATTERNS:
        if re.search(pattern, line):
            return True
    
    # Check for entry markers
    if any(marker in line_lower for marker in HEALTH_LOG_MARKERS):
        return True
    
    return False


# Visit Type Classification Patterns
SICK_VISIT_KEYWORDS = [
    'sick', 'illness', 'symptom', 'pain', 'fever', 'infection',
    'diagnosis', 'treatment', 'medication', 'prescription',
    'abnormal', 'elevated', 'decreased', 'concern', 'complaint'
]

ROUTINE_VISIT_KEYWORDS = [
    'routine', 'checkup', 'well', 'preventive', 'screening',
    'annual', 'baseline', 'follow-up', 'follow up', 'monitoring'
]


def classify_visit_type(text: str) -> str:
    """
    Classify visit type based on keywords.
    
    Returns:
        'sick_visit', 'routine_visit', or 'unknown'
    """
    text_lower = text.lower()
    
    sick_score = sum(1 for keyword in SICK_VISIT_KEYWORDS if keyword in text_lower)
    routine_score = sum(1 for keyword in ROUTINE_VISIT_KEYWORDS if keyword in text_lower)
    
    if sick_score > routine_score and sick_score > 0:
        return 'sick_visit'
    elif routine_score > 0:
        return 'routine_visit'
    else:
        return 'unknown'


# Medication Patterns
MEDICATION_PATTERNS = {
    'medication_name': r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(\d+(?:\.\d+)?)\s*(mg|mcg|g|ml|tablet|cap|pill)',
    'prescription': r'(?:prescribed|prescription|medication|med):\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
}


def extract_medications(text: str) -> List[Dict]:
    """
    Extract medication information from text.
    
    Returns:
        List of dictionaries with medication_name, dosage, unit
    """
    results = []
    
    pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(\d+(?:\.\d+)?)\s*(mg|mcg|g|ml|tablet|cap|pill)'
    
    for match in re.finditer(pattern, text):
        results.append({
            'medication_name': match.group(1),
            'dosage': match.group(2),
            'unit': match.group(3)
        })
    
    return results


# Gene/SNP Patterns
GENE_PATTERN = r'\b([A-Z][A-Z0-9]+)\b'
SNP_PATTERN = r'rs\d+'


def extract_genes(text: str, known_genes: List[str] = None) -> List[str]:
    """
    Extract gene symbols from text.
    
    Args:
        text: Text to search
        known_genes: Optional list of known gene symbols to filter
        
    Returns:
        List of gene symbols found
    """
    if known_genes:
        found_genes = []
        text_upper = text.upper()
        for gene in known_genes:
            pattern = r'\b' + gene.upper() + r'\b'
            if re.search(pattern, text_upper):
                found_genes.append(gene)
        return found_genes
    else:
        # Extract all potential gene symbols (2-10 uppercase letters/numbers)
        matches = re.findall(r'\b([A-Z][A-Z0-9]{1,9})\b', text)
        return list(set(matches))


def extract_snps(text: str) -> List[str]:
    """Extract SNP rs numbers from text"""
    matches = re.findall(SNP_PATTERN, text)
    return list(set(matches))


# Institution Patterns
INSTITUTION_PATTERNS = {
    'tufts': r'Tufts\s+Medical\s+Center',
    'bilh': r'Beth\s+Israel\s+Lahey\s+Health',
    'genesight': r'GeneSight|Myriad\s+Neuroscience',
    'center_for_human_genetics': r'Center\s+for\s+Human\s+Genetics',
}


def extract_institution(text: str) -> str:
    """Extract institution name from text"""
    for institution, pattern in INSTITUTION_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE):
            return institution.replace('_', ' ').title()
    return 'Unknown'


# Test Result Patterns
TEST_RESULT_PATTERNS = {
    'positive': r'(?:positive|pos|detected|present)',
    'negative': r'(?:negative|neg|not detected|absent)',
    'abnormal': r'(?:abnormal|abn|elevated|decreased|high|low)',
    'normal': r'(?:normal|nl|within normal limits|wnl)',
}


def classify_test_result(text: str) -> str:
    """
    Classify test result based on keywords.
    
    Returns:
        'positive', 'negative', 'abnormal', 'normal', or 'unknown'
    """
    text_lower = text.lower()
    
    if re.search(TEST_RESULT_PATTERNS['positive'], text_lower):
        return 'positive'
    elif re.search(TEST_RESULT_PATTERNS['negative'], text_lower):
        return 'negative'
    elif re.search(TEST_RESULT_PATTERNS['abnormal'], text_lower):
        return 'abnormal'
    elif re.search(TEST_RESULT_PATTERNS['normal'], text_lower):
        return 'normal'
    else:
        return 'unknown'


# Validation Functions
def validate_date(date_str: str) -> bool:
    """Validate date string format"""
    for pattern in DATE_PATTERNS:
        if re.fullmatch(pattern, date_str):
            return True
    return False


def validate_gene_symbol(symbol: str) -> bool:
    """Validate gene symbol format"""
    return bool(re.match(r'^[A-Z][A-Z0-9]{1,9}$', symbol))


def validate_snp_rs_number(rs_number: str) -> bool:
    """Validate SNP rs number format"""
    return bool(re.match(r'^rs\d+$', rs_number))


# Pattern Testing Utilities
def test_pattern(pattern: str, test_strings: List[str]) -> Dict:
    """
    Test a pattern against multiple test strings.
    
    Returns:
        Dictionary with test results
    """
    results = {
        'pattern': pattern,
        'matches': [],
        'non_matches': []
    }
    
    for test_str in test_strings:
        if re.search(pattern, test_str):
            results['matches'].append(test_str)
        else:
            results['non_matches'].append(test_str)
    
    return results



# ---------------------------------------------------------------------------
# Vital signs and lab values with plausibility checks
#
# The earlier vitals regexes in extract_health_summary.py / extract_health_metrics.py
# matched any "n/n" (dates such as 8/29/2024 became blood pressure 8/29) and any
# number followed by an F or C (zip codes, "2445 Fenway"), which filled
# health_metrics with thousands of nonsense rows. These extractors require the
# reading's label or unit and reject values outside a physiological range.
# ---------------------------------------------------------------------------

# (min, max) inclusive plausible ranges
BLOOD_PRESSURE_SYSTOLIC_RANGE = (60, 260)
BLOOD_PRESSURE_DIASTOLIC_RANGE = (30, 160)
TEMPERATURE_RANGES = {'F': (90.0, 110.0), 'C': (32.0, 44.0)}

# "Blood Pressure 120/70", "BP: 118/76", "120/80 mmHg". A date like 8/29/2024
# never matches: the keyword form needs the label, the bare form needs "mmHg".
BLOOD_PRESSURE_PATTERN = re.compile(
    r'(?:\b(?:blood\s+pressure|bp)\b\s*:?\s*(?P<s1>\d{2,3})\s*/\s*(?P<d1>\d{2,3})'
    r'|(?<![\d/])(?P<s2>\d{2,3})\s*/\s*(?P<d2>\d{2,3})\s*mmHg)',
    re.IGNORECASE,
)

# "Temperature 36.8 °C (98.3 °F)", "Temp: 98.6 F", "Fever 101.2F", "99.1°F".
# A bare number followed by a letter only counts when the degree sign is
# present. "Fever" is a label people write in their own logs, and a reading
# labelled that way is the one most worth keeping.
TEMPERATURE_PATTERN = re.compile(
    r'(?:\b(?:temperature|temp|fever)\b\s*:?\s*(?:of\s+)?(?P<v1>\d{2,3}(?:\.\d+)?)\s*°?\s*(?P<u1>[FC])\b'
    r'|(?P<v2>\d{2,3}(?:\.\d+)?)\s*°\s*(?P<u2>[FC])\b)',
    re.IGNORECASE,
)

# Other labelled vitals as they appear in patient-portal summaries:
# "Pulse 93", "Respiratory Rate 16", "Oxygen Saturation 100%",
# "Weight 53.1 kg (117 lb)", "Height 162.6 cm (5' 4")".
VITAL_SIGN_PATTERNS = {
    'heart_rate': (re.compile(r'\b(?:pulse|heart\s+rate)\b\s*:?\s*(\d{2,3})\b(?!\s*/)', re.I), 'bpm', (30, 250)),
    'respiratory_rate': (re.compile(r'\brespiratory\s+rate\b\s*:?\s*(\d{1,2})\b', re.I), 'breaths/min', (4, 60)),
    'oxygen_saturation': (re.compile(r'\b(?:oxygen\s+saturation|spo2)\b\s*:?\s*(\d{2,3})\s*%', re.I), '%', (50, 100)),
    'weight': (re.compile(r'\bweight\b\s*:?\s*(\d{2,3}(?:\.\d+)?)\s*kg\b', re.I), 'kg', (2, 400)),
    'height': (re.compile(r'\bheight\b\s*:?\s*(\d{2,3}(?:\.\d+)?)\s*cm\b', re.I), 'cm', (30, 260)),
}

# Units a lab result line must carry to be recorded. Anything else
# ("Suite", "Washington", "minutes") is prose or an address, not a result.
LAB_UNITS = {
    'mg/dl', 'g/dl', 'ug/dl', 'mcg/dl', 'ng/dl', 'ng/ml', 'pg/ml', 'ug/l', 'ng/l',
    'mmol/l', 'umol/l', 'nmol/l', 'pmol/l', 'meq/l', 'mmol/mol',
    'u/l', 'iu/l', 'miu/l', 'miu/ml', 'uiu/ml', 'u/ml',
    'k/ul', 'k/mm3', '10*3/ul', 'x10^3/ul', '/ul', 'cells/ul',
    'm/ul', '10*6/ul', 'x10^6/ul',
    'fl', 'pg', 'g/l', 'mg/l', '%', 'mm/hr', 'sec', 'ratio',
    '/hpf', '/lpf', 'cfu/ml',
}

# "TSH 1.68 mIU/L 0.40-4.50 LAB", "UROBILINOGEN UR 0.2 mg/dL 0.2-1.0 WINCHESTER",
# "CRP <0.30 mg/dL". The name is 1-6 words of letters/digits (no sentence prose),
# followed by the value, a whitelisted unit and an optional low-high range.
LAB_RESULT_LINE_PATTERN = re.compile(
    r'^(?P<name>[A-Za-z][A-Za-z0-9\-\.,()]*(?:\s+[A-Za-z0-9\-\.,()/%]+){0,5}?)'
    r'\s+(?P<value>[<>]?\d+(?:\.\d+)?)'
    r'\s*(?P<unit>%|[A-Za-z*^/0-9\.]+/?[A-Za-z0-9^*]*)'
    r'(?:\s+(?P<low>\d+(?:\.\d+)?)\s*-\s*(?P<high>\d+(?:\.\d+)?))?'
    r'(?:\s|$)'
)

# Names that read as sentences rather than analytes
_LAB_NAME_STOPWORDS = re.compile(
    r'\b(?:the|is|are|was|were|for|with|and|has|had|her|his|she|he|in|of|to|at|on|'
    r'take|apply|inhale|do|not|every|last|past|within|suite|room|street|avenue|ave|st)\b',
    re.IGNORECASE,
)


_VITAL_LABELS = re.compile(
    r'^(?:pulse|heart\s+rate|respiratory\s+rate|oxygen\s+saturation|spo2|weight|height|'
    r'temperature|temp|blood\s+pressure|bp|bmi|body\s+mass\s+index)$',
    re.IGNORECASE,
)


def _in_range(value: float, bounds: Tuple[float, float]) -> bool:
    low, high = bounds
    return low <= value <= high


def extract_blood_pressure_readings(line: str) -> List[Dict]:
    """
    Blood pressure readings on one line as
    [{'systolic': int, 'diastolic': int, 'text': '120/70'}].
    """
    readings = []
    for match in BLOOD_PRESSURE_PATTERN.finditer(line):
        systolic = int(match.group('s1') or match.group('s2'))
        diastolic = int(match.group('d1') or match.group('d2'))
        if (_in_range(systolic, BLOOD_PRESSURE_SYSTOLIC_RANGE)
                and _in_range(diastolic, BLOOD_PRESSURE_DIASTOLIC_RANGE)
                and systolic > diastolic):
            readings.append({'systolic': systolic, 'diastolic': diastolic,
                             'text': f"{systolic}/{diastolic}"})
    return readings


def extract_temperature_reading(line: str) -> Dict:
    """
    The first plausible temperature on a line as {'value': float, 'unit': 'F'|'C'},
    or {} if there is none. A line such as "36.8 °C (98.3 °F)" is one reading,
    so only the first match is returned.
    """
    for match in TEMPERATURE_PATTERN.finditer(line):
        value = float(match.group('v1') or match.group('v2'))
        unit = (match.group('u1') or match.group('u2')).upper()
        if _in_range(value, TEMPERATURE_RANGES[unit]):
            return {'value': value, 'unit': unit}
    return {}


def extract_vital_sign_readings(line: str) -> List[Dict]:
    """
    Labelled vitals other than BP and temperature, as
    [{'metric_type': 'heart_rate', 'value': 93.0, 'unit': 'bpm'}, ...].
    """
    readings = []
    for metric_type, (pattern, unit, bounds) in VITAL_SIGN_PATTERNS.items():
        match = pattern.search(line)
        if not match:
            continue
        value = float(match.group(1))
        if _in_range(value, bounds):
            readings.append({'metric_type': metric_type, 'value': value, 'unit': unit})
    return readings


def extract_lab_result_line(line: str) -> Dict:
    """
    Parse one "NAME VALUE UNIT [LOW-HIGH]" lab result line.

    Returns {'name', 'value' (float or None), 'value_text', 'unit',
    'normal_min', 'normal_max', 'is_abnormal'} or {} when the line is not a
    lab result (unknown unit, prose-like name, or no numeric value).
    """
    match = LAB_RESULT_LINE_PATTERN.match(line.strip())
    if not match:
        return {}
    unit = match.group('unit')
    if unit.lower() not in LAB_UNITS:
        return {}
    name = match.group('name').strip(' :')
    if len(name) > 40 or _LAB_NAME_STOPWORDS.search(name):
        return {}
    # "ketoconazole (NIZOral) 2 %" is a medication strength, not a result,
    # and labelled vitals are handled by extract_vital_sign_readings.
    if '(' in name or _VITAL_LABELS.search(name):
        return {}
    value_text = match.group('value')
    value = None if value_text[0] in '<>' else float(value_text)
    normal_min = float(match.group('low')) if match.group('low') else None
    normal_max = float(match.group('high')) if match.group('high') else None
    is_abnormal = False
    if value is not None and normal_min is not None and normal_max is not None:
        is_abnormal = value < normal_min or value > normal_max
    return {
        'name': name,
        'value': value,
        'value_text': value_text,
        'unit': unit,
        'normal_min': normal_min,
        'normal_max': normal_max,
        'is_abnormal': is_abnormal,
    }


# Patient-portal "health log" exports list each vital as a table:
#
#   Blood Pressure
#   All readings
#   Date Value (mmHg) Entry type
#   Nov 18, 2019, 8:56 AM 110/70 Clinic
#
# The value carries no label of its own, so the section heading decides
# what a row means.
HEALTH_LOG_SECTIONS = {
    'blood pressure': 'blood_pressure',
    'pulse': 'heart_rate',
    'heart rate': 'heart_rate',
    'temperature': 'temperature',
    'weight': 'weight',
    'height': 'height',
    'oxygen saturation': 'oxygen_saturation',
    'respiratory rate': 'respiratory_rate',
}

HEALTH_LOG_ROW_PATTERN = re.compile(
    r'^(?P<date>[A-Za-z]{3,9}\s+\d{1,2},\s+\d{4})(?:,\s*(?P<time>\d{1,2}:\d{2}\s*[AP]M))?'
    r'\s+(?P<value>\d{2,3}\s*/\s*\d{2,3}|\d+(?:\.\d+)?)\s*(?P<unit>°?[FC]\b|kg|lb|cm|%)?'
    r'(?:\s+(?P<entry>[A-Za-z ]+))?\s*$'
)

_HEALTH_LOG_ROW_RANGES = {
    'heart_rate': (30, 250),
    'weight': (2, 400),
    'height': (30, 260),
    'oxygen_saturation': (50, 100),
    'respiratory_rate': (4, 60),
}


def extract_health_log_table_readings(text: str) -> List[Dict]:
    """
    Readings from a sectioned health-log export, as
    [{'metric_type', 'date_text', 'time_text', 'value', 'value_text', 'unit', 'notes', 'entry_type'}].

    date_text is the raw "Nov 18, 2019" string; the caller parses it.
    """
    readings = []
    section = None
    for raw in text.split('\n'):
        line = raw.strip()
        if not line:
            continue
        heading = HEALTH_LOG_SECTIONS.get(line.lower())
        if heading:
            section = heading
            continue
        if not section:
            continue
        match = HEALTH_LOG_ROW_PATTERN.match(line)
        if not match:
            continue
        value_text = match.group('value').replace(' ', '')
        unit = (match.group('unit') or '').lstrip('°')
        reading = {
            'metric_type': section,
            'date_text': match.group('date'),
            'time_text': match.group('time'),
            'value_text': value_text,
            'entry_type': match.group('entry'),
            'notes': None,
        }
        if section == 'blood_pressure':
            bp = extract_blood_pressure_readings(f"BP {value_text}")
            if not bp:
                continue
            reading.update(value=float(bp[0]['systolic']), unit='mmHg',
                           notes=f"Diastolic: {bp[0]['diastolic']}")
        elif section == 'temperature':
            temp = extract_temperature_reading(f"Temp {value_text} {unit or 'F'}")
            if not temp:
                continue
            reading.update(value=temp['value'], unit=temp['unit'])
        else:
            if '/' in value_text:
                continue
            value = float(value_text)
            if not _in_range(value, _HEALTH_LOG_ROW_RANGES[section]):
                continue
            default_unit = {'heart_rate': 'bpm', 'weight': 'kg', 'height': 'cm',
                            'oxygen_saturation': '%', 'respiratory_rate': 'breaths/min'}[section]
            reading.update(value=value, unit=unit or default_unit)
        readings.append(reading)
    return readings
