#!/usr/bin/env python3
"""
Standardize all gene sections to have uniform format and structure.
"""

import re
from pathlib import Path

def standardize_gene_sections(markdown_file):
    """Standardize all gene sections in the markdown file"""
    
    with open(markdown_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split into sections
    sections = re.split(r'(## \d+\. [^\n]+)', content)
    
    # Process each section
    result_sections = [sections[0]]  # Keep header/table of contents
    
    for i in range(1, len(sections), 2):
        if i + 1 < len(sections):
            header = sections[i]
            section_content = sections[i + 1]
            
            # Standardize this section
            standardized = standardize_single_section(header, section_content)
            result_sections.append(header)
            result_sections.append(standardized)
    
    return ''.join(result_sections)


def standardize_single_section(header, content):
    """Standardize a single gene section"""
    
    # 1. Fix GWAS Catalog format - remove "Search available at" prefix
    content = re.sub(
        r'- \*\*Gene Associations:\*\* Search available at (<https://[^>]+>)',
        r'- **Gene Associations:** \1',
        content
    )
    
    # 2. Fix SNPedia - standardize SNP/SNPs based on count
    # Count SNPs in SNPedia section
    snpedia_match = re.search(r'\*\*SNPedia:\*\*(.*?)(?=\*\*GWAS Catalog:\*\*|\*\*GTR|\*\*PubMed:|\n### |$)', content, re.DOTALL)
    if snpedia_match:
        snpedia_section = snpedia_match.group(1)
        snp_count = len(re.findall(r'- \*\*SNP[^:]*:\*\*', snpedia_section))
        
        # If multiple SNPs, ensure "SNPs:" is used, otherwise "SNP:"
        if snp_count > 1:
            # Change first occurrence to "SNPs:"
            content = re.sub(
                r'(\*\*SNPedia:\*\*\s*\n\n)- \*\*SNP:\*\*',
                r'\1- **SNPs:**',
                content
            )
            # Change "Link:" to "Links:" if multiple
            if '**Links:**' not in snpedia_section:
                content = re.sub(
                    r'(\*\*SNPedia:\*\*.*?\n)- \*\*Link:\*\*',
                    r'\1- **Links:**',
                    content,
                    flags=re.DOTALL
                )
        else:
            # Ensure "SNP:" (singular) and "Link:" (singular)
            content = re.sub(
                r'(\*\*SNPedia:\*\*\s*\n\n)- \*\*SNPs:\*\*',
                r'\1- **SNP:**',
                content
            )
            content = re.sub(
                r'(\*\*SNPedia:\*\*.*?\n)- \*\*Links:\*\*',
                r'\1- **Link:**',
                content,
                flags=re.DOTALL
            )
    
    # 3. Add Genotype field to SNPedia if missing (except CYP2D6 which uses "Gene Page:")
    if '**Gene Page:**' not in content:
        snpedia_match = re.search(r'(\*\*SNPedia:\*\*\s*\n\n)(.*?)(?=\*\*GWAS Catalog:\*\*|\*\*GTR|\*\*PubMed:|\n### |$)', content, re.DOTALL)
        if snpedia_match:
            snpedia_header = snpedia_match.group(1)
            snpedia_body = snpedia_match.group(2)
            if '**Genotype:**' not in snpedia_body:
                # Extract genotype from header section
                genotype_match = re.search(r'\*\*Genotype:\*\* ([^\n]+)', content)
                if genotype_match:
                    genotype = genotype_match.group(1).strip()
                    # Add Genotype field after SNP/SNPs field
                    snpedia_body = re.sub(
                        r'(- \*\*SNP[^:]*:\*\* [^\n]+\n)',
                        r'\1- **Genotype:** ' + genotype + '\n',
                        snpedia_body,
                        count=1
                    )
                    content = content.replace(snpedia_header + snpedia_match.group(2), snpedia_header + snpedia_body)
    
    # 4. Fix GWAS Catalog Key Information - add citations if missing
    gwas_match = re.search(r'(\*\*GWAS Catalog:\*\*.*?\n- \*\*Key Information:\*\*\s*\n\s*)([^\n]+)(?=\n\n|\*\*GTR|\*\*PubMed:|\n### |$)', content, re.DOTALL)
    if gwas_match:
        key_info = gwas_match.group(2).strip()
        # If no citation brackets, try to find a citation number from context
        if '[' not in key_info and ']' not in key_info:
            # Look for similar citations in the section
            citation_match = re.search(r'\[(\d+)\]', content)
            if citation_match:
                # Use a generic citation or leave as is
                pass  # We'll handle this more carefully
    
    # 5. Fix trait/health condition citation format - standardize to [1,2,3] format
    # Remove descriptive text in brackets before citations
    content = re.sub(
        r'\[([^\]]+)\]\((\d+(?:,\s*\d+)*)\)',
        r'[\2]',
        content
    )
    
    # Fix cases like [intermediate][1,2,3] to just [1,2,3]
    content = re.sub(
        r'\[([^\]]+)\]\[(\d+(?:,\s*\d+)*)\]',
        r'[\2]',
        content
    )
    
    # 6. Ensure section order: Genotype, SNP, Trait Associations, Health Condition Associations, Database Sources, Gene-Gene Interactions, Research Findings
    # This is more complex - we'll need to reorder if needed
    
    return content


def main():
    """Main function"""
    markdown_file = Path('docs/Genetic_Profile_Non_Pharmacogenomic_Corrected.md')
    backup_file = Path('docs/Genetic_Profile_Non_Pharmacogenomic_Corrected.md.backup')
    
    # Create backup
    if not backup_file.exists():
        with open(markdown_file, 'r', encoding='utf-8') as f:
            backup_file.write_text(f.read(), encoding='utf-8')
        print(f"✅ Created backup: {backup_file}")
    
    # Standardize
    print("Standardizing gene sections...")
    standardized_content = standardize_gene_sections(markdown_file)
    
    # Write back
    with open(markdown_file, 'w', encoding='utf-8') as f:
        f.write(standardized_content)
    
    print(f"✅ Standardized: {markdown_file}")
    print("\nNote: Please review the changes and regenerate HTML if needed.")


if __name__ == '__main__':
    main()

