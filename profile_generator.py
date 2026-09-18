#!/usr/bin/env python3
"""
Generate full genetic profile HTML from database
"""

import html
from datetime import date
from typing import Dict, List
from database_manager import GeneticProfileDB


def format_citation_numbers(citation_str: str) -> str:
    """Format citation numbers for display: [1] for single, [1+] for multiple"""
    if not citation_str:
        return ""
    
    # Parse citation numbers. Anything that is not a number or a numeric
    # range is skipped rather than aborting the whole profile page.
    citations = []
    for part in str(citation_str).split(','):
        part = part.strip()
        if not part:
            continue
        if '-' in part:
            # Handle range like '21-42'
            start, _, end = part.partition('-')
            if start.strip().isdigit() and end.strip().isdigit():
                citations.extend(range(int(start), int(end) + 1))
        elif part.isdigit():
            citations.append(int(part))
    
    citations = sorted(set(citations))
    if not citations:
        return ""
    
    if len(citations) == 1:
        return f'<sup class="citation">[<a href="#ref-{citations[0]}" class="cite-link"><span class="cite-num">{citations[0]}</span></a>]</sup>'
    else:
        first = citations[0]
        all_nums = ','.join(map(str, citations))
        expanded = ','.join([f'<a href="#ref-{num}" class="cite-link"><span class="cite-num">{num}</span></a>' for num in citations])
        return (f'<sup class="citation expandable" data-citations="{all_nums}">'
                f'<span class="cite-compact">[<a href="#ref-{first}" class="cite-link"><span class="cite-num">{first}+</span></a>]</span>'
                f'<span class="cite-expanded" style="display:none;">[{expanded}]</span>'
                f'</sup>')


def generate_profile_html(db: GeneticProfileDB) -> str:
    """Generate complete profile HTML from database"""
    html_parts = []
    
    # Header. Provider and test date come from the primary_sources table
    # instead of being hardcoded (the old header carried a fixed date).
    test_info = db.get_genetic_test_info() or {}
    header_lines = []
    if test_info.get('provider'):
        header_lines.append(f"<strong>Test Provider:</strong> {html.escape(str(test_info['provider']))}")
    if test_info.get('date'):
        header_lines.append(f"<strong>Test Date:</strong> {html.escape(str(test_info['date']))}")
    header_lines.append(f"<strong>Generated:</strong> {date.today().strftime('%B %d, %Y')}")
    html_parts.append("<h1>Genetic Profile - Non-Pharmacogenomic Traits & Associations</h1>")
    html_parts.append("<p>" + "<br>\n".join(header_lines) + "</p>")
    html_parts.append("<hr>")
    
    # Table of Contents
    genes = db.get_all_genes()
    html_parts.append("<h2>Table of Contents</h2><ol>")
    for i, gene in enumerate(genes, 1):
        gene_slug = gene['gene_symbol'].lower().replace(' ', '-')
        html_parts.append(f'<li><a href="#{i}-{gene_slug}">{gene["gene_symbol"]} - {gene["gene_name"]}</a></li>')
    html_parts.append("</ol><hr>")
    
    # Gene sections
    for i, gene in enumerate(genes, 1):
        gene_id = gene['id']
        gene_slug = gene['gene_symbol'].lower().replace(' ', '-')
        
        # Get all data for this gene
        genotypes = db.get_genotypes_for_gene(gene_id)
        snps = db.get_snps_for_gene(gene_id)
        traits = db.get_trait_associations_for_gene(gene_id)
        conditions = db.get_health_conditions_for_gene(gene_id)
        db_sources = db.get_database_sources_for_gene(gene_id)
        research_findings = db.get_research_findings_for_gene(gene_id)
        interactions = db.get_interacting_genes(gene['gene_symbol'])
        
        # Gene header
        html_parts.append(f'<h2 id="{i}-{gene_slug}">{i}. {gene["gene_symbol"]} - {gene["gene_name"]}</h2>')
        
        # Genotype
        if genotypes:
            genotype = genotypes[0]
            html_parts.append(f'<p><strong>Genotype:</strong> {genotype["genotype"]}')
            if genotype.get('phenotype'):
                html_parts.append(f' ({genotype["phenotype"]})')
            html_parts.append('</p>')
        
        # SNPs
        if snps:
            snp_list = ', '.join([snp['rs_number'] for snp in snps])
            html_parts.append(f'<p><strong>SNP{"s" if len(snps) > 1 else ""}:</strong> {snp_list}</p>')
        
        # Trait Associations (deduplicate by trait name)
        if traits:
            html_parts.append('<h3>Trait Associations</h3><ul>')
            seen_traits = set()
            for trait in traits:
                trait_name = trait["trait_name"]
                if trait_name not in seen_traits:
                    seen_traits.add(trait_name)
                    citation_html = format_citation_numbers(trait.get('citation_numbers', ''))
                    html_parts.append(f'<li>{trait_name}{citation_html}</li>')
            html_parts.append('</ul>')
        
        # Health Condition Associations (deduplicate by condition name)
        if conditions:
            html_parts.append('<h3>Health Condition Associations</h3><ul>')
            seen_conditions = set()
            for condition in conditions:
                condition_name = condition["condition_name"]
                if condition_name not in seen_conditions:
                    seen_conditions.add(condition_name)
                    citation_html = format_citation_numbers(condition.get('citation_numbers', ''))
                    html_parts.append(f'<li>{condition_name}{citation_html}</li>')
            html_parts.append('</ul>')
        
        # Database Sources
        if db_sources:
            html_parts.append('<h3>Database Sources</h3>')
            sources_by_type = {}
            for source in db_sources:
                source_type = source['source_type']
                if source_type not in sources_by_type:
                    sources_by_type[source_type] = []
                sources_by_type[source_type].append(source)
            
            for source_type in ['SNPedia', 'GWAS Catalog', 'GTR (Genetic Testing Registry)', 'PubMed']:
                if source_type in sources_by_type:
                    html_parts.append(f'<p><strong>{source_type}:</strong></p><ul>')
                    for source in sources_by_type[source_type]:
                        if source.get('source_url'):
                            html_parts.append(f'<li><a href="{source["source_url"]}">{source["source_url"]}</a></li>')
                        if source.get('key_information'):
                            html_parts.append(f'<li><strong>Key Information:</strong> {source["key_information"]}</li>')
                    html_parts.append('</ul>')
        
        # Gene-Gene Interactions
        if interactions:
            html_parts.append('<h3>Gene-Gene Interactions</h3>')
            for interaction in interactions:
                html_parts.append(f'<p><strong>Interaction with {interaction.get("interacting_gene_symbol", "")}:</strong>')
                if interaction.get('interaction_description'):
                    html_parts.append(f' {interaction["interaction_description"]}')
                html_parts.append('</p>')
        
        # Research Findings
        if research_findings:
            html_parts.append('<h3>Research Findings</h3>')
            for finding in research_findings:
                if finding.get('finding_title'):
                    html_parts.append(f'<p><strong>{finding["finding_title"]}:</strong></p>')
                if finding.get('finding_text'):
                    citation_html = format_citation_numbers(finding.get('citation_numbers', ''))
                    html_parts.append(f'<p>{finding["finding_text"]}{citation_html}</p>')
        
        html_parts.append('<hr>')
    
    # References section
    references = db.get_all_references()
    if references:
        html_parts.append('<h2>References</h2><ol>')
        for ref in references:
            ref_parts = []
            if ref.get('authors'):
                ref_parts.append(f"{ref['authors']}.")
            if ref.get('year'):
                ref_parts.append(f"({ref['year']})")
            if ref.get('title'):
                ref_parts.append(ref['title'])
            if ref.get('journal'):
                journal_part = f"<em>{ref['journal']}</em>"
                if ref.get('volume'):
                    journal_part += f", {ref['volume']}"
                if ref.get('pages'):
                    journal_part += f", {ref['pages']}"
                ref_parts.append(journal_part)
            if ref.get('doi'):
                ref_parts.append(f'<a href="https://doi.org/{ref["doi"]}">https://doi.org/{ref["doi"]}</a>')
            elif ref.get('url'):
                ref_parts.append(f'<a href="{ref["url"]}">{ref["url"]}</a>')
            elif ref.get('pubmed_id'):
                ref_parts.append(f'<a href="https://pubmed.ncbi.nlm.nih.gov/{ref["pubmed_id"]}">https://pubmed.ncbi.nlm.nih.gov/{ref["pubmed_id"]}</a>')
            
            ref_html = ' '.join(ref_parts)
            html_parts.append(f'<li id="ref-{ref["citation_number"]}">{ref_html}</li>')
        html_parts.append('</ol>')
    
    return '\n'.join(html_parts)

