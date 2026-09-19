#!/usr/bin/env python3
"""
Generate doctor-specific documents
Filters data based on doctor template and generates focused documents
"""

import html
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
from database_manager import GeneticProfileDB
from doctor_templates import get_doctor_template
from config import get_logger, OUTPUT_DIR, DOCUMENT_DISCLAIMER
from variant_reference import VARIANT_CAUTION

logger = get_logger('doctor_document')


def generate_doctor_document_html(db: GeneticProfileDB, specialty: str,
                                  include_medications: bool = True,
                                  include_stats: bool = True,
                                  include_pharmacogenomics: bool = True,
                                  include_variants: bool = True,
                                  include_details: bool = True,
                                  asset_base: str = '',
                                  body_prefix_html: str = '') -> str:
    """
    Generate HTML document for a specific doctor specialty.
    
    Args:
        db: Database connection
        specialty: Doctor specialty
        asset_base: prefix for the stylesheet links. Empty for WeasyPrint,
            which resolves them against the project root; '/' when the
            document is served to a browser.
        body_prefix_html: markup placed at the top of the body (the print
            toolbar of the browser version).
        
    Returns:
        HTML string
    """
    template = get_doctor_template(specialty)
    
    html_parts = []
    html_parts.append('<!DOCTYPE html>')
    html_parts.append('<html><head><meta charset="UTF-8">')
    html_parts.append(f'<title>{template["title"]}</title>')
    # Same stylesheets as templates/pdf_base.html; style.css no longer exists.
    html_parts.append(f'<link rel="stylesheet" href="{asset_base}static/css/pdf.css">')
    html_parts.append(f'<link rel="stylesheet" href="{asset_base}static/css/print.css">')
    html_parts.append('</head><body>')
    if body_prefix_html:
        html_parts.append(body_prefix_html)
    
    html_parts.append(f'<h1>{template["title"]}</h1>')
    
    html_parts.extend(patient_details_html(db, include_details))
    
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
    shown_variant_caution = False
    for gene in genes:
        if not gene:
            continue
        
        html_parts.append(f'<h2>{gene["gene_symbol"]} - {gene["gene_name"]}</h2>')
        
        # Get genotype
        genotypes = db.get_genotypes_for_gene(gene['id'])
        if genotypes:
            html_parts.append(f'<p><strong>Genotype:</strong> {genotypes[0].get("genotype", "Not specified")}</p>')
        
        # What the person's own DNA file called at this gene's well-known
        # variants. Empty until a raw-data file has been imported.
        if include_variants:
            variants = db.get_variant_genotypes_for_gene(gene['gene_symbol'])
            if variants:
                html_parts.extend(variant_table_html(variants, with_caution=not shown_variant_caution))
                shown_variant_caution = True
        
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
        
        # Drug-metabolism findings are the person's choice (a checkbox on the
        # Doctor Docs page), whatever the template lists.
        if include_pharmacogenomics:
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
    
    # The report's own medication guidance, by category, when it has been
    # imported (scripts/import_pharmacogenomics.py).
    if include_pharmacogenomics:
        html_parts.extend(medication_guidance_html(db))

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
    
    html_parts.append(f'<p class="footer-disclaimer">{html.escape(DOCUMENT_DISCLAIMER)}</p>')
    html_parts.append('</body></html>')
    
    return '\n'.join(html_parts)


CATEGORY_HEADINGS = [
    ('significant', 'Significant gene-drug interaction'),
    ('moderate', 'Moderate gene-drug interaction'),
    ('use_as_directed', 'Use as directed'),
]


def variant_table_html(variants: List[Dict], with_caution: bool = True) -> List[str]:
    """
    One gene's variants as the person's DNA file called them: rs number,
    genotype, and what the variant is commonly called.

    The caution belongs in the document a doctor reads, but once, under the
    first such table, rather than under every gene.
    """
    parts = ['<h3>Variants in your DNA file</h3>']
    if with_caution:
        parts.append(f'<p class="note">{html.escape(VARIANT_CAUTION)}</p>')
    parts.append('<table class="variant-table">')
    parts.append('<tr><th>Variant</th><th>Genotype</th><th>Commonly called</th></tr>')
    for variant in variants:
        parts.append('<tr><td>{}</td><td>{}</td><td>{}</td></tr>'.format(
            html.escape(variant.get('rsid', '')),
            html.escape(variant.get('genotype', '')),
            html.escape(variant.get('description', ''))))
    parts.append('</table>')
    return parts


def format_date_of_birth(value: str) -> str:
    """An ISO date as people read it ("May 14, 1980"); other text as typed."""
    try:
        d = datetime.strptime(value.strip(), '%Y-%m-%d')
    except ValueError:
        return value
    return f"{d:%B} {d.day}, {d.year}"


def patient_details_html(db: GeneticProfileDB, include_details: bool = True) -> List[str]:
    """
    The block at the top of a doctor document that says whose it is:
    name, date of birth, address, phone, insurance. Only filled fields print.
    Without saved details, the patient name found in the records is used.
    """
    details = db.get_patient_details() if include_details else {}
    name = details.get('full_name') or db.get_patient_name()
    rows = [('Patient', name)]
    if include_details:
        insurance = ' &middot; '.join(
            html.escape(details[field]) for field in
            ('insurance_provider', 'insurance_member_id', 'insurance_group_number')
            if details.get(field))
        rows += [
            ('Date of birth', details.get('date_of_birth') and format_date_of_birth(details['date_of_birth'])),
            ('Address', details.get('address')),
            ('Phone', details.get('phone')),
        ]
    parts = ['<table class="patient-details">']
    for label, value in rows:
        if value:
            parts.append(f'<tr><th>{label}</th><td>{html.escape(value)}</td></tr>')
    if include_details and insurance:
        parts.append(f'<tr><th>Insurance</th><td>{insurance}</td></tr>')
    parts.append('</table>')
    return parts if len(parts) > 2 else []


def medication_guidance_html(db: GeneticProfileDB) -> List[str]:
    """
    The genetic test report's medication categories as HTML parts, or an
    empty list when none have been imported. Significant and moderate
    interactions are listed one per line; "use as directed" is one
    paragraph, since it is the long list.
    """
    rows = db.get_medication_interactions()
    if not rows:
        return []
    by_category = {}
    for row in rows:
        by_category.setdefault(row['category'], []).append(row)
    source_names = sorted({r['source_name'] for r in rows if r.get('source_name')})
    parts = ['<h2>Medication Guidance from the Genetic Test Report</h2>']
    if source_names:
        parts.append(f'<p><em>As stated in: {", ".join(source_names)}</em></p>')
    for key, heading in CATEGORY_HEADINGS:
        items = by_category.get(key)
        if not items:
            continue
        parts.append(f'<h3>{heading} ({len(items)})</h3>')
        names = []
        for item in items:
            name = item['drug_name']
            if item.get('brand_name'):
                name += f' ({item["brand_name"]})'
            names.append(name)
        if key == 'use_as_directed':
            parts.append('<p>' + ', '.join(names) + '</p>')
        else:
            parts.append('<ul>' + ''.join(f'<li>{n}</li>' for n in names) + '</ul>')
    parts.append('<hr>')
    return parts


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

