#!/usr/bin/env python3
"""
Citation Overhaul Script
Fixes citation numbering, deduplicates references, and creates a new document with correct citations
"""

import re
import json
from collections import OrderedDict
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from database_manager import GeneticProfileDB


class CitationOverhaul:
    """Handles citation overhaul and database integration"""
    
    def __init__(self, input_file: str, output_file: str, db_path: str = "genetic_profile.db"):
        self.input_file = Path(input_file)
        self.output_file = Path(output_file)
        self.db = GeneticProfileDB(db_path)
        self.references = OrderedDict()  # citation_number -> reference_data
        self.citation_map = {}  # old_citation -> new_citation
        self.next_citation = 1
        
    def parse_reference(self, line: str) -> Optional[Dict]:
        """Parse a reference line and extract citation data"""
        # Pattern: number. Author (year). Title. Journal, volume, pages. URL
        patterns = [
            # Pattern 1: Number. Author (year). Title. Journal, volume, pages. URL
            re.compile(r'^(\d+)\.\s+(.+?)\s+\((\d{4})\)\.\s+(.+?)\s+<(.+?)>$'),
            # Pattern 2: Number. Author (year). Title. URL
            re.compile(r'^(\d+)\.\s+(.+?)\s+\((\d{4})\)\.\s+(.+?)\s+<(.+?)>$'),
            # Pattern 3: Number. Author. (year). Title. Retrieved from URL
            re.compile(r'^(\d+)\.\s+(.+?)\.\s+\((\d{4})\)\.\s+(.+?)\s+Retrieved from\s+<(.+?)>$'),
            # Pattern 4: Number. Author. Title. [incomplete]
            re.compile(r'^(\d+)\.\s+(.+?)\.\s+(.+?)\s+\[(.+?)\]$'),
        ]
        
        for pattern in patterns:
            match = pattern.match(line.strip())
            if match:
                groups = match.groups()
                citation_num = int(groups[0])
                
                # Extract DOI or PubMed ID from URL
                url = groups[-1] if len(groups) > 4 else None
                doi = None
                pubmed_id = None
                
                if url:
                    doi_match = re.search(r'doi\.org/([^\s<>]+)', url)
                    if doi_match:
                        doi = doi_match.group(1)
                    pubmed_match = re.search(r'pubmed\.ncbi\.nlm\.nih\.gov/(\d+)', url)
                    if pubmed_match:
                        pubmed_id = pubmed_match.group(1)
                
                # Determine reference type
                ref_type = "journal"
                if url and any(x in url.lower() for x in ['genesight', 'genomind', 'snpedia', 'ncbi.nlm.nih.gov/gtr', 'medlineplus']):
                    ref_type = "website"
                elif url and 'pubmed' in url.lower():
                    ref_type = "journal"
                
                # Extract journal from title if it contains italicized journal name
                journal = None
                title = groups[3] if len(groups) > 3 else groups[2]
                
                # Check for italicized journal name (e.g., *Journal Name*)
                journal_match = re.search(r'\*([^*]+)\*', title)
                if journal_match:
                    journal = journal_match.group(1)
                    title = title.replace(f'*{journal}*', '').strip()
                
                # Extract volume and pages
                volume = None
                pages = None
                if journal:
                    # Look for volume, pages pattern after journal
                    vol_pages_match = re.search(r',\s*(\d+)(?:\((\d+)\))?,\s*([\d-]+)', title)
                    if vol_pages_match:
                        volume = vol_pages_match.group(1)
                        pages = vol_pages_match.group(3)
                
                return {
                    'citation_number': citation_num,
                    'authors': groups[1],
                    'year': int(groups[2]) if len(groups) > 2 and groups[2].isdigit() else None,
                    'title': title,
                    'journal': journal,
                    'volume': volume,
                    'pages': pages,
                    'doi': doi,
                    'pubmed_id': pubmed_id,
                    'url': url,
                    'reference_type': ref_type,
                    'raw_line': line.strip()
                }
        
        return None
    
    def extract_all_references(self) -> Dict[int, Dict]:
        """Extract all references from the document"""
        with open(self.input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the References section
        ref_section_match = re.search(r'^## References\s*$', content, re.MULTILINE)
        if not ref_section_match:
            print("Warning: Could not find References section")
            return {}
        
        ref_section_start = ref_section_match.end()
        ref_section = content[ref_section_start:]
        
        # Split into lines and parse
        lines = ref_section.split('\n')
        references = {}
        current_ref = None
        current_text = []
        
        for line in lines:
            # Check if this is a new reference (starts with number.)
            ref_match = re.match(r'^(\d+)\.\s+(.+)$', line.strip())
            if ref_match:
                # Save previous reference if exists
                if current_ref:
                    ref_data = self.parse_reference('\n'.join(current_text))
                    if ref_data:
                        references[ref_data['citation_number']] = ref_data
                
                # Start new reference
                current_ref = int(ref_match.group(1))
                current_text = [line.strip()]
            elif current_ref and line.strip():
                # Continuation of current reference
                current_text.append(line.strip())
        
        # Don't forget the last reference
        if current_ref:
            ref_data = self.parse_reference('\n'.join(current_text))
            if ref_data:
                references[ref_data['citation_number']] = ref_data
        
        return references
    
    def deduplicate_references(self, references: Dict[int, Dict]) -> Dict[int, Dict]:
        """Deduplicate references based on content"""
        seen = {}
        deduplicated = OrderedDict()
        citation_remap = {}
        
        for old_num, ref_data in sorted(references.items()):
            # Create a unique key based on content
            key_parts = [
                ref_data.get('authors', ''),
                ref_data.get('year', ''),
                ref_data.get('title', '')[:50],  # First 50 chars of title
                ref_data.get('url', '')
            ]
            key = '|'.join(str(p) for p in key_parts if p)
            
            if key in seen:
                # This is a duplicate
                citation_remap[old_num] = seen[key]
            else:
                # New unique reference
                new_num = len(deduplicated) + 1
                ref_data['citation_number'] = new_num
                deduplicated[new_num] = ref_data
                seen[key] = new_num
                citation_remap[old_num] = new_num
        
        self.citation_map = citation_remap
        return deduplicated
    
    def format_reference_apa(self, ref_data: Dict) -> str:
        """Format a reference in APA style"""
        parts = []
        
        # Authors
        authors = ref_data.get('authors', 'Unknown')
        parts.append(f"{authors}.")
        
        # Year
        year = ref_data.get('year')
        if year:
            parts.append(f"({year})")
        
        # Title
        title = ref_data.get('title', '')
        if title:
            # Remove journal name if embedded
            title = re.sub(r'\*[^*]+\*', '', title).strip()
            if title:
                parts.append(title)
        
        # Journal
        journal = ref_data.get('journal')
        volume = ref_data.get('volume')
        pages = ref_data.get('pages')
        
        if journal:
            journal_part = f"*{journal}*"
            if volume:
                journal_part += f", {volume}"
            if pages:
                journal_part += f", {pages}"
            parts.append(journal_part)
        
        # URL/DOI
        url = ref_data.get('url')
        doi = ref_data.get('doi')
        
        if doi:
            parts.append(f"<https://doi.org/{doi}>")
        elif url:
            parts.append(f"<{url}>")
        
        # Combine
        citation_num = ref_data.get('citation_number', '?')
        return f"{citation_num}. {' '.join(parts)}"
    
    def update_citations_in_text(self, text: str) -> str:
        """Update all citation numbers in the text"""
        # Pattern: [1,2,3] or [1] or [1, 2, 3]
        def replace_citation(match):
            old_citations = [int(x.strip()) for x in match.group(1).split(',')]
            new_citations = [self.citation_map.get(old, old) for old in old_citations]
            # Remove duplicates and sort
            new_citations = sorted(set(new_citations))
            return f"[{','.join(map(str, new_citations))}]"
        
        pattern = r'\[(\d+(?:\s*,\s*\d+)*)\]'
        return re.sub(pattern, replace_citation, text)
    
    def process_document(self):
        """Process the entire document"""
        print("Reading input file...")
        with open(self.input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("Extracting references...")
        all_refs = self.extract_all_references()
        print(f"Found {len(all_refs)} references")
        
        print("Deduplicating references...")
        deduplicated = self.deduplicate_references(all_refs)
        print(f"After deduplication: {len(deduplicated)} unique references")
        
        print("Updating citations in text...")
        updated_content = self.update_citations_in_text(content)
        
        print("Replacing References section...")
        # Find and replace the References section
        ref_section_match = re.search(r'^## References\s*$', updated_content, re.MULTILINE)
        if ref_section_match:
            ref_start = ref_section_match.start()
            # Find where References section ends (before Research Resources or end of file)
            remaining = updated_content[ref_start:]
            next_section_match = re.search(r'^## [^R]', remaining, re.MULTILINE)
            if next_section_match:
                ref_end = ref_start + next_section_match.start()
            else:
                ref_end = len(updated_content)
            
            # Build new References section
            new_refs_section = "## References\n\n"
            for ref_num in sorted(deduplicated.keys()):
                ref_data = deduplicated[ref_num]
                new_refs_section += self.format_reference_apa(ref_data) + "\n\n"
            
            # Replace
            updated_content = updated_content[:ref_start] + new_refs_section + updated_content[ref_end:]
        
        print(f"Writing to {self.output_file}...")
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print("✅ Citation overhaul complete!")
        print(f"   Input: {len(all_refs)} references")
        print(f"   Output: {len(deduplicated)} unique references")
        
        # Save to database
        print("\nSaving to database...")
        self.save_to_database(deduplicated)
        print("✅ Database updated!")
    
    def save_to_database(self, references: Dict[int, Dict]):
        """Save references to database"""
        for ref_num, ref_data in references.items():
            try:
                self.db.add_reference(
                    citation_number=ref_num,
                    authors=ref_data.get('authors'),
                    year=ref_data.get('year'),
                    title=ref_data.get('title'),
                    journal=ref_data.get('journal'),
                    volume=ref_data.get('volume'),
                    pages=ref_data.get('pages'),
                    doi=ref_data.get('doi'),
                    pubmed_id=ref_data.get('pubmed_id'),
                    url=ref_data.get('url'),
                    reference_type=ref_data.get('reference_type', 'journal')
                )
            except Exception as e:
                print(f"Warning: Could not add reference {ref_num}: {e}")


if __name__ == "__main__":
    input_file = "Genetic_Profile_Non_Pharmacogenomic_Consolidated.md"
    output_file = "Genetic_Profile_Non_Pharmacogenomic_Corrected.md"
    
    overhaul = CitationOverhaul(input_file, output_file)
    overhaul.process_document()
    overhaul.db.close()

