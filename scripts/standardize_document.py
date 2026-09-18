#!/usr/bin/env python3
"""
Standardize genetic profile document formatting using reusable templates.
Ensures all sections follow consistent formatting rules.
"""

import re
from pathlib import Path

class DocumentStandardizer:
    """Standardizes document formatting using templates."""
    
    # Citation format: always use square brackets
    CITATION_PATTERN = r'\[([^\]]+)\]\(([0-9]+(?:-[0-9]+)?(?:,[0-9]+(?:-[0-9]+)?)*)\)'
    
    # Database Sources template fields
    DATABASE_FIELDS = {
        'snpedia': {
            'snp_singular': '- **SNP:**',
            'snps_plural': '- **SNPs:**',
            'gene_page': '- **Gene Page:**',
            'link_singular': '- **Link:**',
            'links_plural': '- **Links:**',
            'genotype': '- **Genotype:**',
            'key_info': '- **Key Information:**'
        },
        'gwas': {
            'gene_associations': '- **Gene Associations:**',
            'key_info': '- **Key Information:**'
        },
        'gtr': {
            'gene': '- **Gene:**',
            'link': '- **Link:**',
            'key_info': '- **Key Information:**'
        },
        'pubmed': {
            'description': '-'
        }
    }
    
    def __init__(self, file_path):
        self.file_path = Path(file_path)
        with open(self.file_path, 'r', encoding='utf-8') as f:
            self.content = f.read()
    
    def standardize_citations(self):
        """Convert all citations to square bracket format."""
        # Fix [description](citations) to [description][citations]
        self.content = re.sub(
            r'\[([^\]]+)\]\(([0-9]+(?:-[0-9]+)?(?:,[0-9]+(?:-[0-9]+)?)*)\)',
            r'[\1][\2]',
            self.content
        )
        return self
    
    def standardize_database_sources(self):
        """Standardize Database Sources section formatting."""
        # Ensure all GWAS Catalog use "Key Information" not "Key Findings"
        self.content = re.sub(
            r'- \*\*Key Findings:\*\*',
            r'- **Key Information:**',
            self.content
        )
        
        # Ensure consistent spacing after database source headings
        self.content = re.sub(
            r'(\*\*SNPedia:\*\*)\n\n\n',
            r'\1\n\n',
            self.content
        )
        self.content = re.sub(
            r'(\*\*GWAS Catalog:\*\*)\n\n\n',
            r'\1\n\n',
            self.content
        )
        self.content = re.sub(
            r'(\*\*GTR \(Genetic Testing Registry\):\*\*)\n\n\n',
            r'\1\n\n',
            self.content
        )
        self.content = re.sub(
            r'(\*\*PubMed:\*\*)\n\n\n',
            r'\1\n\n',
            self.content
        )
        
        return self
    
    def standardize_gwas_format(self):
        """Standardize GWAS Catalog format - use direct links consistently."""
        # Convert "Search available at" to direct link format
        self.content = re.sub(
            r'- \*\*Gene Associations:\*\* Search available at <(https://[^>]+)>',
            r'- **Gene Associations:** <\1>',
            self.content
        )
        return self
    
    def standardize_trait_format(self):
        """Ensure trait associations use consistent citation format."""
        # All citations should be [citation] not (citation)
        # This is handled by standardize_citations
        return self
    
    def standardize_section_structure(self):
        """Ensure all gene sections follow the same structure."""
        # Verify section order: Genotype, SNP, Database Sources, Trait Associations, 
        # Health Condition Associations, Gene-Gene Interactions, Research Findings
        
        # This is more of a validation - actual restructuring would be complex
        # For now, we'll just ensure formatting consistency
        return self
    
    def save(self):
        """Save the standardized content."""
        with open(self.file_path, 'w', encoding='utf-8') as f:
            f.write(self.content)
        return self
    
    def standardize_all(self):
        """Run all standardization methods."""
        self.standardize_citations()
        self.standardize_database_sources()
        self.standardize_gwas_format()
        self.standardize_trait_format()
        self.standardize_section_structure()
        return self


def main():
    """Main function to standardize the document."""
    doc_path = Path(__file__).parent.parent / 'docs' / 'Genetic_Profile_Non_Pharmacogenomic_Corrected.md'
    
    if not doc_path.exists():
        print(f"❌ File not found: {doc_path}")
        return False
    
    print(f"📝 Standardizing document: {doc_path}")
    
    standardizer = DocumentStandardizer(doc_path)
    standardizer.standardize_all()
    standardizer.save()
    
    print("✅ Document standardized successfully!")
    return True


if __name__ == '__main__':
    main()

