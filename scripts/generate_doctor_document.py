#!/usr/bin/env python3
"""
Generate doctor-specific documents
Filters data based on doctor template and generates focused documents
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
from database_manager import GeneticProfileDB
from doctor_templates import get_doctor_template
from config import get_logger, OUTPUT_DIR

logger = get_logger('doctor_document')


def generate_doctor_document_html(db: GeneticProfileDB, specialty: str,
                                  include_medications: bool = True,
                                  include_stats: bool = True) -> str:
    """
    Generate HTML document for a specific doctor specialty.
    
    Args:
        db: Database connection
        specialty: Doctor specialty
        
    Returns:
        HTML string
    """
    template = get_doctor_template(specialty)
    
    html_parts = []
    html_parts.append('<!DOCTYPE html>')
    html_parts.append('<html><head><meta charset="UTF-8">')
    html_parts.append(f'<title>{template["title"]}</title>')
    # Same stylesheets as templates/pdf_base.html; style.css no longer exists.
    html_parts.append('<link rel="stylesheet" href="static/css/pdf.css">')
    html_parts.append('<link rel="stylesheet" href="static/css/print.css">')
    html_parts.append('</head><body>')
    
    html_parts.append(f'<h1>{template["title"]}</h1>')
    
    # Get patient name
    patient_name = db.get_patient_name()
    if patient_name:
        html_parts.append(f'<p><strong>Patient:</strong> {patient_name}</p>')
    
    # Get genetic test information
    test_info = db.get_genetic_test_info()
    if test_info:
        html_parts.append(f'<p><strong>Genetic Test Provider:</strong> {test_info.get("provider", "Unknown")}</p>')
        if test_info.get("date"):
            html_parts.append(f'<p><strong>Test Date:</strong> {test_info.get("date")}</p>')
    
    html_parts.append(f'<p><strong>Specialty:</strong> {specialty.title()}</p>')
    html_parts.append(f'<p><strong>Detail Level:</strong> {template["detail_level"]}</p>')
    html_parts.append('<hr>')
    
    # Get genes to include
    if template['genes'] == 'all':
        genes = db.get_all_genes()
    else:
        genes = [db.get_gene_by_symbol(symbol) for symbol in template['genes']]
        genes = [g for g in genes if g]  # Remove None values
    
    # Generate gene sections
    for gene in genes:
        if not gene:
            continue
        
        html_parts.append(f'<h2>{gene["gene_symbol"]} - {gene["gene_name"]}</h2>')
        
        # Get genotype
        genotypes = db.get_genotypes_for_gene(gene['id'])
        if genotypes:
            html_parts.append(f'<p><strong>Genotype:</strong> {genotypes[0].get("genotype", "Not specified")}</p>')
        
        # Get trait associations if in relevant sections
        if template['sections'] == 'all' or 'traits' in template['sections']:
            traits = db.get_trait_associations_for_gene(gene['id'])
            if traits:
                html_parts.append('<h3>Trait Associations</h3><ul>')
                for trait in traits:
                    html_parts.append(f'<li>{trait["trait_name"]}</li>')
                html_parts.append('</ul>')
        
        # Get health conditions if in relevant sections
        if template['sections'] == 'all' or 'conditions' in template['sections']:
            conditions = db.get_health_conditions_for_gene(gene['id'])
            if conditions:
                html_parts.append('<h3>Health Condition Associations</h3><ul>')
                for condition in conditions:
                    html_parts.append(f'<li>{condition["condition_name"]}</li>')
                html_parts.append('</ul>')
        
        # Get pharmacogenomic data if in relevant sections
        if 'pharmacogenomics' in template['sections'] or template['sections'] == 'all':
            pg_data = db.get_pharmacogenomic_data_for_gene(gene['id'])
            if pg_data:
                html_parts.append('<h3>Pharmacogenomic Information</h3>')
                html_parts.append(f'<p><strong>Metabolism:</strong> {pg_data.get("metabolism_status", "Unknown")}</p>')
                if pg_data.get("genotype_phenotype"):
                    html_parts.append(f'<p><strong>Genotype/Phenotype:</strong> {pg_data.get("genotype_phenotype")}</p>')
                drugs = pg_data.get('affected_medications', [])
                if drugs:
                    html_parts.append('<p><strong>Relevant Drugs:</strong></p><ul>')
                    for drug in drugs:
                        html_parts.append(f'<li>{drug}</li>')
                    html_parts.append('</ul>')
        
        html_parts.append('<hr>')
    
    # Add current medications if requested
    if include_medications:
        medications = db.get_current_medications()
        if medications:
            html_parts.append('<h2>Current Medications</h2>')
            html_parts.append('<ul>')
            for med in medications:
                details = f" - {med.get('details', '')}" if med.get('details') else ''
                date_info = f" (Started: {med.get('start_date', 'Unknown')})" if med.get('start_date') else ''
                html_parts.append(f'<li><strong>{med.get("medication_name", "Unknown")}</strong>{date_info}{details}</li>')
            html_parts.append('</ul>')
            html_parts.append('<hr>')
    
    # Add health statistics if requested
    if include_stats:
        stats = db.get_health_metrics_category_averages()
        if stats:
            html_parts.append('<h2>Average Health Statistics (Routine Visits Only)</h2>')
            html_parts.append('<table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">')
            html_parts.append('<tr style="background-color: #f0f0f0;"><th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Metric Type</th>')
            html_parts.append('<th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Average</th>')
            html_parts.append('<th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Range</th>')
            html_parts.append('<th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Normal Range</th>')
            html_parts.append('<th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Measurements</th></tr>')
            
            for stat in stats:
                metric_type = stat.get('metric_type', 'Unknown').replace('_', ' ').title()
                if stat.get('unit'):
                    metric_type = f"{metric_type} ({stat['unit']})"
                avg = stat.get('category_average')
                min_val = stat.get('category_min')
                max_val = stat.get('category_max')
                normal_min = stat.get('normal_range_min')
                normal_max = stat.get('normal_range_max')
                count = stat.get('total_measurements', 0)
                
                if avg is not None:
                    avg_str = f"{avg:.2f}"
                    range_str = f"{min_val:.2f} - {max_val:.2f}" if min_val is not None and max_val is not None else "N/A"
                    normal_str = f"{normal_min:.2f} - {normal_max:.2f}" if normal_min is not None and normal_max is not None else "N/A"
                    
                    html_parts.append(f'<tr><td style="padding: 8px; border: 1px solid #ddd;">{metric_type}</td>')
                    html_parts.append(f'<td style="padding: 8px; border: 1px solid #ddd;">{avg_str}</td>')
                    html_parts.append(f'<td style="padding: 8px; border: 1px solid #ddd;">{range_str}</td>')
                    html_parts.append(f'<td style="padding: 8px; border: 1px solid #ddd;">{normal_str}</td>')
                    html_parts.append(f'<td style="padding: 8px; border: 1px solid #ddd;">{count}</td></tr>')
            
            html_parts.append('</table>')
            html_parts.append('<hr>')
    
    # Add health metrics if requested (detailed list)
    if 'health_metrics' in template['sections'] or template['sections'] == 'all':
        html_parts.append('<h2>Recent Health Metrics</h2>')
        metrics = db.get_health_metrics(routine_only=True)
        if metrics:
            html_parts.append('<ul>')
            for metric in metrics[:50]:  # Limit to 50 most recent
                html_parts.append(f'<li>{metric.get("metric_name", metric.get("metric_type"))}: '
                                f'{metric.get("metric_value")} {metric.get("unit", "")} '
                                f'({metric.get("collection_date")})</li>')
            html_parts.append('</ul>')
    
    html_parts.append('</body></html>')
    
    return '\n'.join(html_parts)


def generate_doctor_document(db: GeneticProfileDB, specialty: str, 
                            output_format: str = 'pdf') -> Optional[str]:
    """
    Generate doctor-specific document.
    
    Args:
        db: Database connection
        specialty: Doctor specialty
        output_format: Output format ('pdf', 'html', 'markdown')
        
    Returns:
        Path to generated file if successful, None otherwise
    """
    try:
        if output_format == 'html':
            html_content = generate_doctor_document_html(db, specialty)
            output_path = str(OUTPUT_DIR / f'doctor_{specialty}.html')
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"Generated HTML document: {output_path}")
            return output_path
        
        elif output_format == 'pdf':
            from pdf_generator import generate_doctor_pdf
            output_path = str(OUTPUT_DIR / f'doctor_{specialty}.pdf')
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            if generate_doctor_pdf(db, specialty, output_path):
                logger.info(f"Generated PDF document: {output_path}")
                return output_path
            else:
                return None
        
        else:
            logger.error(f"Unsupported output format: {output_format}")
            return None
            
    except Exception as e:
        logger.error(f"Error generating doctor document: {e}", exc_info=True)
        return None


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate doctor-specific document')
    parser.add_argument('specialty', help='Doctor specialty')
    parser.add_argument('--format', choices=['pdf', 'html'], default='pdf',
                       help='Output format')
    
    args = parser.parse_args()
    
    db = GeneticProfileDB()
    try:
        output_path = generate_doctor_document(db, args.specialty, args.format)
        if output_path:
            print(f"Document generated: {output_path}")
        else:
            print("Failed to generate document")
            sys.exit(1)
    finally:
        db.close()

