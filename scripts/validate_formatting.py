#!/usr/bin/env python3
"""
Validate document formatting against template standards.
Reports any inconsistencies found.
"""

import re
from pathlib import Path
from collections import defaultdict

class FormatValidator:
    """Validates document formatting consistency."""
    
    def __init__(self, file_path):
        self.file_path = Path(file_path)
        with open(self.file_path, 'r', encoding='utf-8') as f:
            self.content = f.read()
        self.errors = []
        self.warnings = []
    
    def check_citation_format(self):
        """Check that all citations use square brackets."""
        # Split content at References section
        refs_start = self.content.find('## References')
        main_content = self.content[:refs_start] if refs_start > 0 else self.content
        
        # Find citations in parentheses (excluding years 1900-2100)
        paren_citations = []
        for match in re.finditer(r'\(([0-9]+(?:-[0-9]+)?(?:,[0-9]+(?:-[0-9]+)?)*)\)', main_content):
            num_str = match.group(1).split(',')[0].split('-')[0]
            try:
                num = int(num_str)
                # Skip years
                if not (1900 <= num <= 2100):
                    # Skip if it's in a markdown link
                    context = main_content[max(0, match.start()-10):match.end()+10]
                    if '<' not in context:
                        paren_citations.append(match.group(0))
            except ValueError:
                pass
        
        if paren_citations:
            self.errors.append(f"Found {len(paren_citations)} citations using parentheses instead of square brackets")
        
        # Find [description](citation) pattern
        mixed_format = re.findall(r'\[([^\]]+)\]\(([0-9]+)', main_content)
        if mixed_format:
            self.errors.append(f"Found {len(mixed_format)} citations using [text](citation) format - should be [text][citation]")
    
    def check_database_sources(self):
        """Check Database Sources formatting."""
        # Check for "Key Findings" instead of "Key Information"
        key_findings = len(re.findall(r'- \*\*Key Findings:\*\*', self.content))
        if key_findings > 0:
            self.errors.append(f"Found {key_findings} instances of 'Key Findings:' - should be 'Key Information:'")
        
        # Check for inconsistent GWAS format
        search_available = len(re.findall(r'Search available at <', self.content))
        if search_available > 0:
            self.warnings.append(f"Found {search_available} instances of 'Search available at' - consider standardizing to direct links")
    
    def check_section_structure(self):
        """Check that all sections follow the standard structure."""
        # Count gene sections
        gene_sections = re.findall(r'^## \d+\.', self.content, re.MULTILINE)
        self.info = f"Found {len(gene_sections)} gene sections"
    
    def validate_all(self):
        """Run all validation checks."""
        self.check_citation_format()
        self.check_database_sources()
        self.check_section_structure()
        
        return len(self.errors) == 0
    
    def print_report(self):
        """Print validation report."""
        print(f"\n{'='*60}")
        print("FORMATTING VALIDATION REPORT")
        print(f"{'='*60}\n")
        
        if hasattr(self, 'info'):
            print(f"ℹ️  {self.info}\n")
        
        if self.errors:
            print("❌ ERRORS FOUND:")
            for error in self.errors:
                print(f"   • {error}")
            print()
        else:
            print("✅ No errors found!\n")
        
        if self.warnings:
            print("⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"   • {warning}")
            print()
        
        if not self.errors and not self.warnings:
            print("✅ All formatting checks passed!")
        
        print(f"{'='*60}\n")


def main():
    """Main validation function."""
    doc_path = Path(__file__).parent.parent / 'docs' / 'Genetic_Profile_Non_Pharmacogenomic_Corrected.md'
    
    if not doc_path.exists():
        print(f"❌ File not found: {doc_path}")
        return False
    
    validator = FormatValidator(doc_path)
    is_valid = validator.validate_all()
    validator.print_report()
    
    return is_valid


if __name__ == '__main__':
    main()

