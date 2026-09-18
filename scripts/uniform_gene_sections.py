#!/usr/bin/env python3
"""
Make all gene sections uniform in structure and format.
Standardizes:
1. Section order
2. Field names (SNP vs SNPs, Link vs Links)
3. GWAS Catalog format
4. Citation format
"""

import re
from pathlib import Path

def extract_genotype(section):
    """Extract genotype from section header"""
    match = re.search(r'\*\*Genotype:\*\* ([^\n]+)', section)
    return match.group(1).strip() if match else None

def extract_snp_info(section):
    """Extract SNP information from section"""
    match = re.search(r'\*\*SNP[^:]*:\*\* ([^\n]+)', section)
    return match.group(1).strip() if match else None

def reorder_section(section_content):
    """Reorder section to standard format"""
    # Standard order:
    # 1. Genotype
    # 2. SNP/SNPs
    # 3. Trait Associations
    # 4. Health Condition Associations
    # 5. Database Sources
    # 6. Gene-Gene Interactions
    # 7. Research Findings
    
    genotype_match = re.search(r'\*\*Genotype:\*\* ([^\n]+)', section_content)
    snp_match = re.search(r'\*\*SNP[^:]*:\*\* ([^\n]+)', section_content)
    trait_match = re.search(r'(### Trait Associations.*?)(?=### |$)', section_content, re.DOTALL)
    health_match = re.search(r'(### Health Condition Associations.*?)(?=### |$)', section_content, re.DOTALL)
    database_match = re.search(r'(### Database Sources.*?)(?=### |$)', section_content, re.DOTALL)
    interactions_match = re.search(r'(### Gene-Gene Interactions.*?)(?=### |$)', section_content, re.DOTALL)
    research_match = re.search(r'(### Research Findings.*?)(?=### |$)', section_content, re.DOTALL)
    
    # Build new section in correct order
    parts = []
    
    # Genotype
    if genotype_match:
        parts.append(f"**Genotype:** {genotype_match.group(1)}\n")
    
    # SNP
    if snp_match:
        snp_text = snp_match.group(1)
        # Determine if should be SNP or SNPs based on content
        if ',' in snp_text or 'and' in snp_text.lower():
            parts.append(f"**SNPs:** {snp_text}\n")
        else:
            parts.append(f"**SNP:** {snp_text}\n")
    
    parts.append("\n")
    
    # Trait Associations
    if trait_match:
        parts.append(trait_match.group(1).rstrip() + "\n\n")
    
    # Health Condition Associations
    if health_match:
        parts.append(health_match.group(1).rstrip() + "\n\n")
    
    # Database Sources
    if database_match:
        db_section = standardize_database_section(database_match.group(1), genotype_match.group(1) if genotype_match else None)
        parts.append(db_section.rstrip() + "\n\n")
    
    # Gene-Gene Interactions
    if interactions_match:
        parts.append(interactions_match.group(1).rstrip() + "\n\n")
    
    # Research Findings
    if research_match:
        parts.append(research_match.group(1).rstrip() + "\n")
    
    return ''.join(parts)

def standardize_database_section(db_section, genotype):
    """Standardize Database Sources section"""
    # Fix SNPedia
    # Count SNPs
    snp_count = len(re.findall(r'- \*\*SNP[^:]*:\*\*', db_section))
    
    if snp_count > 1:
        db_section = re.sub(r'(\*\*SNPedia:\*\*\s*\n\n)- \*\*SNP:\*\*', r'\1- **SNPs:**', db_section)
        db_section = re.sub(r'(\*\*SNPedia:\*\*.*?\n)- \*\*Link:\*\*', r'\1- **Links:**', db_section, flags=re.DOTALL)
    else:
        db_section = re.sub(r'(\*\*SNPedia:\*\*\s*\n\n)- \*\*SNPs:\*\*', r'\1- **SNP:**', db_section)
        db_section = re.sub(r'(\*\*SNPedia:\*\*.*?\n)- \*\*Links:\*\*', r'\1- **Link:**', db_section, flags=re.DOTALL)
    
    # Add Genotype field to SNPedia if missing (unless it's CYP2D6 with Gene Page)
    if '**Gene Page:**' not in db_section and genotype:
        snpedia_match = re.search(r'(\*\*SNPedia:\*\*\s*\n\n)(.*?)(?=\*\*GWAS Catalog:\*\*|\*\*GTR|\*\*PubMed:|\n### |$)', db_section, re.DOTALL)
        if snpedia_match and '**Genotype:**' not in snpedia_match.group(2):
            # Add after SNP/SNPs field
            snpedia_body = snpedia_match.group(2)
            snpedia_body = re.sub(
                r'(- \*\*SNP[^:]*:\*\* [^\n]+\n)',
                r'\1- **Genotype:** ' + genotype + '\n',
                snpedia_body,
                count=1
            )
            db_section = db_section.replace(snpedia_match.group(0), snpedia_match.group(1) + snpedia_body)
    
    # Fix GWAS Catalog - remove "Search available at"
    db_section = re.sub(
        r'- \*\*Gene Associations:\*\* Search available at (<https://[^>]+>)',
        r'- **Gene Associations:** \1',
        db_section
    )
    
    return db_section

def main():
    """Main function"""
    md_file = Path('docs/Genetic_Profile_Non_Pharmacogenomic_Corrected.md')
    
    # Create backup
    backup = md_file.with_suffix('.md.backup')
    if not backup.exists():
        backup.write_text(md_file.read_text(encoding='utf-8'), encoding='utf-8')
        print(f"✅ Created backup: {backup}")
    
    # Read content
    content = md_file.read_text(encoding='utf-8')
    
    # Split into sections
    sections = re.split(r'(## \d+\. [^\n]+)', content)
    result = [sections[0]]  # Keep header/table of contents
    
    # Process each gene section
    for i in range(1, len(sections), 2):
        if i + 1 < len(sections):
            header = sections[i]
            section_content = sections[i + 1]
            
            # Reorder and standardize
            standardized = reorder_section(section_content)
            
            result.append(header)
            result.append("\n" + standardized)
    
    # Fix citation format globally
    final_content = ''.join(result)
    final_content = re.sub(r'\[([^\]]+)\]\((\d+(?:,\s*\d+)*)\)', r'[\2]', final_content)
    final_content = re.sub(r'\[([^\]]+)\]\[(\d+(?:,\s*\d+)*)\]', r'[\2]', final_content)
    
    # Write back
    md_file.write_text(final_content, encoding='utf-8')
    print(f"✅ Standardized all gene sections in: {md_file}")
    print("\nNote: Please review and regenerate HTML.")

if __name__ == '__main__':
    main()

