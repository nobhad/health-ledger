#!/usr/bin/env python3
"""
Import genetic profile data from markdown document into database
"""

import re
import sys
from pathlib import Path
from typing import List, Dict, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database_manager import GeneticProfileDB


class MarkdownImporter:
    """Import data from markdown to database"""
    
    def __init__(self, markdown_file: str, db_path: str = "genetic_profile.db"):
        self.markdown_file = Path(markdown_file)
        self.db = GeneticProfileDB(db_path)
        self.gene_map = {}  # gene_symbol -> gene_id
        self.citation_map = {}  # citation_number -> citation_id
        
    def parse_gene_section(self, content: str) -> List[Dict]:
        """Parse all gene sections from markdown"""
        # Pattern: ## N. GENE_SYMBOL - Gene Name
        gene_pattern = re.compile(r'^##\s+\d+\.\s+([A-Z0-9]+)\s+-\s+(.+?)$', re.MULTILINE)
        
        genes = []
        for match in gene_pattern.finditer(content):
            gene_symbol = match.group(1)
            gene_name = match.group(2)
            
            # Find the section content
            start = match.end()
            next_section = re.search(r'^##\s+\d+\.', content[start:], re.MULTILINE)
            if next_section:
                section_content = content[start:start+next_section.start()]
            else:
                section_content = content[start:]
            
            genes.append({
                'symbol': gene_symbol,
                'name': gene_name,
                'content': section_content
            })
        
        return genes
    
    def extract_genotype(self, content: str) -> Optional[str]:
        """Extract genotype from gene section"""
        # Look for **Genotype:** pattern
        match = re.search(r'\*\*Genotype:\*\*\s+([^\n]+)', content, re.MULTILINE)
        if match:
            genotype = match.group(1).strip()
            # Clean up: remove parenthetical descriptions like "(Heterozygous)"
            genotype = re.sub(r'\s*\([^)]+\)\s*$', '', genotype)
            # Also handle cases like "*A/*A (rs71647871)" - extract just the genotype part
            if '(' in genotype and 'rs' in genotype:
                genotype = genotype.split('(')[0].strip()
            return genotype
        return None
    
    def extract_snps(self, content: str) -> List[str]:
        """Extract SNP rs numbers from gene section"""
        # Pattern: **SNP:** rs123456 or **SNPs:** rs123456, rs789012
        snp_pattern = re.compile(r'\*\*SNP[s]?:\*\*\s+([^\n]+)')
        matches = snp_pattern.findall(content)
        snps = []
        for match in matches:
            # Extract rs numbers (rs followed by digits)
            rs_numbers = re.findall(r'rs\d+', match)
            snps.extend(rs_numbers)
            # Also check for other SNP identifiers like "5-HTTLPR" or special cases
            # For now, we'll focus on rs numbers as they're the standard
        # Remove duplicates while preserving order
        seen = set()
        unique_snps = []
        for snp in snps:
            if snp not in seen:
                seen.add(snp)
                unique_snps.append(snp)
        return unique_snps
    
    def extract_trait_associations(self, content: str) -> List[Dict]:
        """Extract trait associations from gene section"""
        # Find Trait Associations section - stop at next ### or ## section
        trait_section_match = re.search(r'^### Trait Associations\s*$(.+?)(?=^### |^## |\Z)', content, re.MULTILINE | re.DOTALL)
        if not trait_section_match:
            return []
        
        trait_section = trait_section_match.group(1)
        traits = []
        
        # Pattern: - Trait name[citations] - handle both with and without bold markers
        # Match lines starting with "- " followed by optional bold, then trait name, then citations
        trait_pattern = re.compile(r'^-\s+(?:\*\*)?(.+?)(?:\*\*)?\[(\d+(?:,\s*\d+)*)\]', re.MULTILINE)
        for match in trait_pattern.finditer(trait_section):
            trait_name = match.group(1).strip()
            citations_str = match.group(2)
            citations = [int(x.strip()) for x in citations_str.split(',')]
            
            # Clean trait name - remove any remaining markdown formatting
            trait_name = re.sub(r'\*\*', '', trait_name).strip()
            
            # Extract direction if present (e.g., "[increased]", "[HIGHER]", "[intermediate]")
            # Look for direction keywords in brackets within the trait name
            direction_match = re.search(r'\s*\[(intermediate|balanced|moderate|increased|decreased|protective|higher|lower|high|low)\]', trait_name, re.IGNORECASE)
            if direction_match:
                direction = direction_match.group(1).lower()
                # Remove direction from trait name
                trait_name = re.sub(r'\s*\[(intermediate|balanced|moderate|increased|decreased|protective|higher|lower|high|low)\]', '', trait_name, flags=re.IGNORECASE).strip()
            else:
                direction = None
            
            traits.append({
                'name': trait_name,
                'citations': citations,
                'direction': direction
            })
        
        return traits
    
    def extract_health_conditions(self, content: str) -> List[Dict]:
        """Extract health condition associations from gene section"""
        # Find Health Condition Associations section - stop at next ### or ## section
        health_section_match = re.search(r'^### Health Condition Associations\s*$(.+?)(?=^### |^## |\Z)', content, re.MULTILINE | re.DOTALL)
        if not health_section_match:
            return []
        
        health_section = health_section_match.group(1)
        conditions = []
        
        # Pattern: - Condition name[citations] - handle both with and without bold markers
        condition_pattern = re.compile(r'^-\s+(?:\*\*)?(.+?)(?:\*\*)?\[(\d+(?:,\s*\d+)*)\]', re.MULTILINE)
        for match in condition_pattern.finditer(health_section):
            condition_name = match.group(1).strip()
            citations_str = match.group(2)
            citations = [int(x.strip()) for x in citations_str.split(',')]
            
            # Clean condition name - remove any remaining markdown formatting
            condition_name = re.sub(r'\*\*', '', condition_name).strip()
            
            # Extract association type if present (e.g., "risk", "susceptibility")
            # Look for type keywords in the condition name
            type_match = re.search(r'\b(risk|protection|susceptibility|protective|diagnosis|features)\b', condition_name, re.IGNORECASE)
            if type_match:
                assoc_type = type_match.group(1).lower()
                # Normalize to standard types
                if assoc_type in ['protection', 'protective']:
                    assoc_type = 'protective'
                elif assoc_type in ['risk', 'susceptibility']:
                    assoc_type = 'susceptibility'
                else:
                    assoc_type = None
            else:
                assoc_type = None
            
            conditions.append({
                'name': condition_name,
                'citations': citations,
                'type': assoc_type
            })
        
        return conditions
    
    def extract_gene_interactions(self, content: str, current_gene_symbol: str) -> List[Dict]:
        """Extract gene-gene interactions from gene section"""
        # Find Gene-Gene Interactions section - stop at next ### or ## section
        interaction_section_match = re.search(r'^### Gene-Gene Interactions\s*$(.+?)(?=^### |^## |\Z)', content, re.MULTILINE | re.DOTALL)
        if not interaction_section_match:
            return []
        
        interaction_section = interaction_section_match.group(1)
        interactions = []
        
        # Pattern: **Interaction with [GENE (Section N)](link):** description
        # Handle markdown links: [COMT (Section 3)](#3-comt---catechol-o-methyltransferase)
        # Split by interaction markers
        parts = re.split(r'\*\*Interaction with \[', interaction_section)
        
        for part in parts[1:]:  # Skip first empty part
            # Extract gene symbol - format: COMT (Section 3)](#link):**
            # Match gene symbol at start before (
            gene_match = re.match(r'^([A-Z0-9]+)\s*\(', part)
            if not gene_match:
                continue
            
            interacting_gene_symbol = gene_match.group(1).strip()
            
            # Skip if it's the same gene
            if interacting_gene_symbol == current_gene_symbol:
                continue
            
            # Get description - everything after ]:** or ]:**
            # Handle both with and without markdown links
            desc_match = re.search(r'\)\]\([^)]+\):\*\*\s*(.+?)(?=\*\*Interaction with |\Z)', part, re.DOTALL)
            if not desc_match:
                # Try without link: ]:**
                desc_match = re.search(r'\)\]:\*\*\s*(.+?)(?=\*\*Interaction with |\Z)', part, re.DOTALL)
            
            if not desc_match:
                continue
            
            description = desc_match.group(1).strip()
            
            # Clean up description (remove extra whitespace, citations, markdown)
            description = re.sub(r'\s+', ' ', description).strip()
            description = re.sub(r'\[\d+(?:,\s*\d+)*\]', '', description).strip()  # Remove citations
            description = re.sub(r'\*\*', '', description).strip()  # Remove bold markers
            description = re.sub(r'\n+', ' ', description).strip()  # Remove newlines
            
            if description and len(description) > 10:  # Only add if we have meaningful description
                interactions.append({
                    'interacting_gene': interacting_gene_symbol,
                    'description': description
                })
        
        return interactions
    
    def load_citations_from_db(self):
        """Load existing citations from database to map citation numbers to IDs"""
        refs = self.db.get_all_references()
        for ref in refs:
            self.citation_map[ref['citation_number']] = ref['id']
    
    def import_gene(self, gene_data: Dict):
        """Import a single gene and its data"""
        gene_symbol = gene_data['symbol']
        gene_name = gene_data['name']
        content = gene_data['content']
        
        print(f"\nImporting {gene_symbol}...")
        
        # Get or add gene
        if gene_symbol not in self.gene_map:
            try:
                gene_id = self.db.add_gene(gene_symbol, gene_name)
                self.gene_map[gene_symbol] = gene_id
                print(f"  Added gene: {gene_symbol}")
            except Exception as e:
                # Gene already exists, get its ID
                gene = self.db.get_gene_by_symbol(gene_symbol)
                if gene:
                    gene_id = gene['id']
                    self.gene_map[gene_symbol] = gene_id
                    print(f"  Gene already exists: {gene_symbol} (ID: {gene_id})")
                else:
                    print(f"  ERROR: Could not add or find gene {gene_symbol}: {e}")
                    return
        else:
            gene_id = self.gene_map[gene_symbol]
            print(f"  Using existing gene mapping: {gene_symbol} (ID: {gene_id})")
        
        # Extract and add SNPs
        snps = self.extract_snps(content)
        if snps:
            for rs_number in snps:
                try:
                    self.db.add_snp(rs_number, gene_id)
                    print(f"  Added SNP: {rs_number}")
                except Exception as e:
                    # Check if it's a duplicate error
                    if 'UNIQUE' in str(e) or 'duplicate' in str(e).lower() or 'already exists' in str(e).lower():
                        print(f"  SNP already exists: {rs_number}")
                    else:
                        print(f"  Warning: Could not add SNP {rs_number}: {e}")
        else:
            print(f"  No SNPs found for {gene_symbol}")
        
        # Extract and add genotype
        genotype = self.extract_genotype(content)
        if genotype:
            # Check if genotype already exists for this gene
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT id FROM genotypes WHERE gene_id = ? AND genotype = ?", (gene_id, genotype))
            existing = cursor.fetchone()
            if existing:
                print(f"  Genotype already exists: {genotype}")
            else:
                try:
                    self.db.add_genotype(gene_id, genotype)
                    print(f"  Added genotype: {genotype}")
                except Exception as e:
                    print(f"  Warning: Could not add genotype: {e}")
        else:
            print(f"  No genotype found for {gene_symbol}")
        
        # Extract and add trait associations
        traits = self.extract_trait_associations(content)
        if traits:
            print(f"  Found {len(traits)} trait associations")
            for trait in traits:
                citation_ids = [self.citation_map.get(c, None) for c in trait['citations']]
                citation_ids = [c for c in citation_ids if c is not None]
                
                try:
                    self.db.add_trait_association(
                        gene_id=gene_id,
                        trait_name=trait['name'],
                        association_direction=trait.get('direction'),
                        reference_ids=citation_ids if citation_ids else None
                    )
                    print(f"  Added trait: {trait['name']}")
                except Exception as e:
                    # Check if it's a duplicate error
                    if 'UNIQUE' in str(e) or 'duplicate' in str(e).lower() or 'already exists' in str(e).lower():
                        print(f"  Trait already exists: {trait['name']}")
                    else:
                        print(f"  Warning: Could not add trait {trait['name']}: {e}")
        else:
            print(f"  No trait associations found for {gene_symbol}")
        
        # Extract and add health conditions
        conditions = self.extract_health_conditions(content)
        if conditions:
            print(f"  Found {len(conditions)} health condition associations")
            for condition in conditions:
                citation_ids = [self.citation_map.get(c, None) for c in condition['citations']]
                citation_ids = [c for c in citation_ids if c is not None]
                
                try:
                    self.db.add_health_condition_association(
                        gene_id=gene_id,
                        condition_name=condition['name'],
                        association_type=condition.get('type'),
                        reference_ids=citation_ids if citation_ids else None
                    )
                    print(f"  Added condition: {condition['name']}")
                except Exception as e:
                    # Check if it's a duplicate error
                    if 'UNIQUE' in str(e) or 'duplicate' in str(e).lower() or 'already exists' in str(e).lower():
                        print(f"  Condition already exists: {condition['name']}")
                    else:
                        print(f"  Warning: Could not add condition {condition['name']}: {e}")
        else:
            print(f"  No health condition associations found for {gene_symbol}")
        
        # Extract and add gene-gene interactions
        interactions = self.extract_gene_interactions(content, gene_symbol)
        if interactions:
            print(f"  Found {len(interactions)} gene-gene interactions")
            for interaction in interactions:
                interacting_gene = self.db.get_gene_by_symbol(interaction['interacting_gene'])
                if interacting_gene:
                    # Check if interaction already exists (in either direction)
                    cursor = self.db.conn.cursor()
                    cursor.execute("""
                        SELECT id FROM gene_gene_interactions 
                        WHERE (gene1_id = ? AND gene2_id = ?) 
                           OR (gene1_id = ? AND gene2_id = ?)
                    """, (gene_id, interacting_gene['id'], interacting_gene['id'], gene_id))
                    existing = cursor.fetchone()
                    if existing:
                        print(f"  Interaction already exists: {gene_symbol} ↔ {interaction['interacting_gene']}")
                    else:
                        try:
                            self.db.add_gene_gene_interaction(
                                gene1_id=gene_id,
                                gene2_id=interacting_gene['id'],
                                interaction_description=interaction['description']
                            )
                            print(f"  Added interaction: {gene_symbol} ↔ {interaction['interacting_gene']}")
                        except Exception as e:
                            print(f"  Warning: Could not add interaction {gene_symbol} ↔ {interaction['interacting_gene']}: {e}")
                else:
                    print(f"  Warning: Interacting gene {interaction['interacting_gene']} not found in database")
        else:
            print(f"  No gene-gene interactions found for {gene_symbol}")
    
    def import_all(self):
        """Import all data from markdown file"""
        print("Reading markdown file...")
        with open(self.markdown_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("Loading citations from database...")
        self.load_citations_from_db()
        print(f"  Loaded {len(self.citation_map)} citations")
        
        print("\nParsing gene sections...")
        genes = self.parse_gene_section(content)
        print(f"  Found {len(genes)} genes")
        
        print("\nImporting genes...")
        for gene_data in genes:
            try:
                self.import_gene(gene_data)
            except Exception as e:
                print(f"  Error importing {gene_data['symbol']}: {e}")
        
        print("\n[OK] Import complete!")
        print(f"   Genes imported: {len(self.gene_map)}")
        
        self.db.close()


if __name__ == "__main__":
    # Import from the corrected markdown file
    import sys
    from pathlib import Path
    
    # Try multiple possible locations
    possible_files = [
        Path("docs/Genetic_Profile_Non_Pharmacogenomic_Corrected.md"),
        Path("docs/Genetic_Profile_Non_Pharmacogenomic.md"),
        Path("Genetic_Profile_Non_Pharmacogenomic_Corrected.md"),
        Path("Genetic_Profile_Non_Pharmacogenomic.md"),
    ]
    
    md_file = None
    for path in possible_files:
        if path.exists():
            md_file = path
            break
    
    if not md_file:
        print(f"ERROR: Markdown file not found!")
        print(f"  Tried:")
        for path in possible_files:
            print(f"    {path}")
        sys.exit(1)
    
    print(f"Importing from: {md_file}")
    importer = MarkdownImporter(str(md_file))
    importer.import_all()

