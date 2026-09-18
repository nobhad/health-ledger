#!/usr/bin/env python3
"""
Doctor-Specific Document Templates
Defines templates for different medical specialties
"""

DOCTOR_TEMPLATES = {
    'cardiologist': {
        'genes': ['ADRA2A', 'COMT', 'CYP2D6', 'VKORC1'],
        'sections': ['cardiovascular', 'medications', 'pharmacogenomics'],
        'detail_level': 'summary',
        'title': 'Genetic Profile for Cardiologist'
    },
    'psychiatrist': {
        'genes': ['HTR2A', 'SLC6A4', 'COMT', 'CYP2D6', 'ADRA2A', 'CYP2C19'],
        'sections': ['mental_health', 'medications', 'pharmacogenomics'],
        'detail_level': 'detailed',
        'title': 'Genetic Profile for Psychiatrist'
    },
    'geneticist': {
        'genes': 'all',
        'sections': 'all',
        'detail_level': 'comprehensive',
        'title': 'Complete Genetic Profile'
    },
    'general_practitioner': {
        'genes': 'all',
        'sections': ['summary', 'health_metrics', 'recent_visits', 'medications'],
        'detail_level': 'summary',
        'title': 'Genetic Profile Summary'
    },
    'neurologist': {
        'genes': ['COMT', 'HTR2A', 'SLC6A4', 'CYP2D6'],
        'sections': ['neurological', 'medications', 'pharmacogenomics'],
        'detail_level': 'detailed',
        'title': 'Genetic Profile for Neurologist'
    },
    'endocrinologist': {
        'genes': ['CYP2D6', 'CYP2C9', 'CYP2C19', 'UGT1A1', 'UGT2B15'],
        'sections': ['metabolic', 'medications', 'pharmacogenomics'],
        'detail_level': 'detailed',
        'title': 'Genetic Profile for Endocrinologist'
    }
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

