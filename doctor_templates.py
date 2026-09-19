#!/usr/bin/env python3
"""
Doctor-Specific Document Templates
Defines templates for different medical specialties
"""

# Each template names the genes a specialty prescribes against, drawn from
# the drug-metabolism and HLA panel this ledger holds, and the sections that
# shape the document. Section names that change the output: 'traits',
# 'conditions', 'pharmacogenomics', 'health_metrics' (see
# scripts/generate_doctor_document.py); the rest are descriptive.
DOCTOR_TEMPLATES = {
    'general_practitioner': {
        'genes': 'all',
        'sections': ['summary', 'health_metrics', 'recent_visits', 'medications'],
        'detail_level': 'summary',
        'title': 'Genetic Profile Summary'
    },
    'cardiologist': {
        # Warfarin (VKORC1 with CYP2C9), clopidogrel (CYP2C19), statins and
        # calcium-channel blockers (CYP3A4/5), beta blockers (CYP2D6, ADRA2A).
        'genes': ['VKORC1', 'CYP2C9', 'CYP2C19', 'CYP2D6', 'CYP3A4', 'CYP3A5', 'ADRA2A', 'COMT'],
        'sections': ['cardiovascular', 'conditions', 'medications', 'pharmacogenomics'],
        'detail_level': 'summary',
        'title': 'Genetic Profile for Cardiologist'
    },
    'psychiatrist': {
        # Antidepressants and antipsychotics (CYP2D6, CYP2C19, CYP1A2, CYP3A4),
        # bupropion (CYP2B6), benzodiazepines (UGT2B15), serotonin pathway
        # (HTR2A, SLC6A4), mood stabiliser hypersensitivity (HLA-A, HLA-B).
        'genes': ['CYP2D6', 'CYP2C19', 'CYP1A2', 'CYP2B6', 'CYP3A4', 'UGT2B15',
                  'HTR2A', 'SLC6A4', 'COMT', 'ADRA2A', 'HLA-A', 'HLA-B'],
        'sections': ['mental_health', 'conditions', 'medications', 'pharmacogenomics'],
        'detail_level': 'detailed',
        'title': 'Genetic Profile for Psychiatrist'
    },
    'neurologist': {
        # Anticonvulsants: carbamazepine and phenytoin hypersensitivity (HLA-A,
        # HLA-B), phenytoin metabolism (CYP2C9); migraine and pain (CYP2D6, COMT).
        'genes': ['HLA-A', 'HLA-B', 'CYP2C9', 'CYP2C19', 'CYP2D6', 'CYP3A4', 'COMT', 'HTR2A', 'SLC6A4'],
        'sections': ['neurological', 'conditions', 'medications', 'pharmacogenomics'],
        'detail_level': 'detailed',
        'title': 'Genetic Profile for Neurologist'
    },
    'endocrinologist': {
        'genes': ['CYP2D6', 'CYP2C9', 'CYP2C19', 'CYP3A4', 'UGT1A1', 'UGT2B15'],
        'sections': ['metabolic', 'conditions', 'health_metrics', 'medications', 'pharmacogenomics'],
        'detail_level': 'detailed',
        'title': 'Genetic Profile for Endocrinologist'
    },
    'rheumatologist': {
        # NSAIDs (CYP2C9), tramadol and codeine (CYP2D6), tacrolimus and
        # cyclosporine (CYP3A4/5), allopurinol hypersensitivity (HLA-B), the
        # PPIs prescribed alongside NSAIDs (CYP2C19).
        'genes': ['CYP2C9', 'CYP2D6', 'CYP3A4', 'CYP3A5', 'HLA-B', 'CYP2C19'],
        'sections': ['conditions', 'health_metrics', 'medications', 'pharmacogenomics'],
        'detail_level': 'detailed',
        'title': 'Genetic Profile for Rheumatologist'
    },
    'anesthesiologist': {
        # Pre-surgery: codeine, tramadol, ondansetron (CYP2D6), NSAIDs
        # (CYP2C9), midazolam and fentanyl (CYP3A4/5), methadone (CYP2B6),
        # lorazepam (UGT2B15). Allergies and current medications matter here.
        'genes': ['CYP2D6', 'CYP2C9', 'CYP3A4', 'CYP3A5', 'CYP2B6', 'UGT2B15', 'HLA-A', 'HLA-B'],
        'sections': ['pre_surgery', 'conditions', 'medications', 'pharmacogenomics'],
        'detail_level': 'summary',
        'title': 'Genetic Profile for Anesthesiologist'
    },
    'pain_management': {
        # Opioids (CYP2D6, CYP3A4, CYP2B6), NSAIDs (CYP2C9), pain sensitivity
        # (COMT), benzodiazepines (UGT2B15).
        'genes': ['CYP2D6', 'CYP2C9', 'CYP3A4', 'CYP2B6', 'COMT', 'UGT2B15'],
        'sections': ['pain', 'conditions', 'medications', 'pharmacogenomics'],
        'detail_level': 'detailed',
        'title': 'Genetic Profile for Pain Management'
    },
    'gastroenterologist': {
        # Proton-pump inhibitors (CYP2C19), bilirubin handling and Gilbert's
        # (UGT1A1), immunosuppressants (CYP3A4/5).
        'genes': ['CYP2C19', 'UGT1A1', 'CYP3A4', 'CYP3A5', 'CYP2C9'],
        'sections': ['digestive', 'conditions', 'health_metrics', 'medications', 'pharmacogenomics'],
        'detail_level': 'detailed',
        'title': 'Genetic Profile for Gastroenterologist'
    },
    'allergist_immunologist': {
        'label': 'Allergist / Immunologist',
        # Drug hypersensitivity alleles (HLA-A, HLA-B) beside the recorded
        # allergies and immunizations.
        'genes': ['HLA-A', 'HLA-B', 'CYP2D6', 'CYP2C9'],
        'sections': ['allergies', 'immunizations', 'conditions', 'medications', 'pharmacogenomics'],
        'detail_level': 'detailed',
        'title': 'Genetic Profile for Allergist / Immunologist'
    },
    'pharmacist': {
        # Medication review: every gene, the drug findings, nothing else.
        'genes': 'all',
        'sections': ['medications', 'pharmacogenomics'],
        'detail_level': 'detailed',
        'title': 'Pharmacogenomic Profile for Medication Review'
    },
    'dentist': {
        # Codeine and tramadol (CYP2D6), ibuprofen (CYP2C9), midazolam (CYP3A4).
        'genes': ['CYP2D6', 'CYP2C9', 'CYP3A4'],
        'sections': ['dental', 'medications', 'pharmacogenomics'],
        'detail_level': 'summary',
        'title': 'Genetic Profile for Dentist'
    },
    'geneticist': {
        'genes': 'all',
        'sections': 'all',
        'detail_level': 'comprehensive',
        'title': 'Complete Genetic Profile'
    },
}


def get_doctor_template(specialty: str) -> dict:
    """
    Get template configuration for a doctor specialty.
    
    Args:
        specialty: Doctor specialty name
        
    Returns:
        Template configuration dictionary
    """
    return DOCTOR_TEMPLATES.get(specialty.lower(), DOCTOR_TEMPLATES['general_practitioner'])


def get_available_specialties() -> list:
    """Get list of available doctor specialties"""
    return list(DOCTOR_TEMPLATES.keys())

