#!/usr/bin/env python3
"""
Example queries for the genetic profile database
"""

from database_manager import GeneticProfileDB


def example_queries():
    """Run example queries"""
    db = GeneticProfileDB()
    
    print("=" * 60)
    print("GENETIC PROFILE DATABASE - EXAMPLE QUERIES")
    print("=" * 60)
    
    # 0. Get gene summaries
    print("\n0. Gene Summaries:")
    print("-" * 60)
    summaries = db.get_all_gene_summaries()
    for summary in summaries[:5]:
        print(f"  {summary['gene_symbol']}: {summary['trait_count']} traits, {summary['condition_count']} conditions, {summary['snp_count']} SNPs")
    
    # 1. Get all genes
    print("\n1. All Genes in Database:")
    print("-" * 60)
    genes = db.get_all_genes()
    for gene in genes:
        print(f"  {gene['gene_symbol']}: {gene['gene_name']}")
    
    # 2. Get trait associations for a specific gene
    print("\n2. Trait Associations for ADRA2A:")
    print("-" * 60)
    gene = db.get_gene_by_symbol("ADRA2A")
    if gene:
        traits = db.get_trait_associations_for_gene(gene['id'])
        for trait in traits:
            citations = trait.get('citation_numbers', '')
            print(f"  • {trait['trait_name']}")
            if trait.get('association_direction'):
                print(f"    Direction: {trait['association_direction']}")
            if citations:
                print(f"    Citations: {citations}")
    
    # 3. Search for traits
    print("\n3. Search for 'anxiety' traits:")
    print("-" * 60)
    anxiety_traits = db.search_traits("anxiety")
    for trait in anxiety_traits:
        print(f"  {trait['gene_symbol']}: {trait['trait_name']}")
    
    # 4. Search for health conditions
    print("\n4. Search for 'depression' health conditions:")
    print("-" * 60)
    depression_conditions = db.search_health_conditions("depression")
    for condition in depression_conditions:
        print(f"  {condition['gene_symbol']}: {condition['condition_name']}")
    
    # 5. Get all references
    print("\n5. All References (first 10):")
    print("-" * 60)
    references = db.get_all_references()
    for ref in references[:10]:
        print(f"  [{ref['citation_number']}] {ref.get('authors', 'Unknown')} ({ref.get('year', 'N/A')})")
        if ref.get('title'):
            print(f"      {ref['title'][:60]}...")
    
    # 6. Get references for a specific gene
    print("\n6. References for COMT:")
    print("-" * 60)
    gene = db.get_gene_by_symbol("COMT")
    if gene:
        refs = db.get_references_for_gene(gene['id'])
        for ref in refs[:5]:
            print(f"  [{ref['citation_number']}] {ref.get('authors', 'Unknown')} ({ref.get('year', 'N/A')})")
    
    # 7. Get health conditions for a gene
    print("\n7. Health Conditions for SLC6A4:")
    print("-" * 60)
    gene = db.get_gene_by_symbol("SLC6A4")
    if gene:
        conditions = db.get_health_conditions_for_gene(gene['id'])
        for condition in conditions:
            citations = condition.get('citation_numbers', '')
            print(f"  • {condition['condition_name']}")
            if condition.get('association_type'):
                print(f"    Type: {condition['association_type']}")
            if citations:
                print(f"    Citations: {citations}")
    
    # 8. Find genes associated with a trait
    print("\n8. Genes Associated with 'anxiety':")
    print("-" * 60)
    anxiety_genes = db.get_genes_with_trait("anxiety")
    for gene_info in anxiety_genes[:5]:
        print(f"  {gene_info['gene_symbol']}: {gene_info.get('trait_name', 'N/A')}")
    
    # 9. Find genes associated with a condition
    print("\n9. Genes Associated with 'depression':")
    print("-" * 60)
    depression_genes = db.get_genes_with_condition("depression")
    for gene_info in depression_genes[:5]:
        print(f"  {gene_info['gene_symbol']}: {gene_info.get('condition_name', 'N/A')}")
    
    # 10. Find genes that interact with a given gene
    print("\n10. Genes that Interact with COMT:")
    print("-" * 60)
    interacting = db.get_interacting_genes("COMT")
    for interaction in interacting:
        print(f"  {interaction['interacting_gene_symbol']}: {interaction['interacting_gene_name']}")
        if interaction.get('interaction_description'):
            desc = interaction['interaction_description'][:60]
            print(f"    {desc}...")
    
    # 11. Get comprehensive gene summary
    print("\n11. Comprehensive Summary for ADRA2A:")
    print("-" * 60)
    summary = db.get_gene_summary("ADRA2A")
    if summary:
        print(f"  Gene: {summary['gene_symbol']} - {summary.get('gene_name', 'N/A')}")
        print(f"  Traits: {summary.get('trait_count', 0)}")
        print(f"  Conditions: {summary.get('condition_count', 0)}")
        print(f"  SNPs: {summary.get('snp_count', 0)}")
        print(f"  Interactions: {summary.get('interaction_count', 0)}")
    
    db.close()


def export_to_json(filename: str = "genetic_profile_export.json"):
    """Export all data to JSON"""
    db = GeneticProfileDB()
    
    data = {
        "genes": [],
        "export_date": str(datetime.now())
    }
    
    genes = db.get_all_genes()
    for gene in genes:
        gene_data = dict(gene)
        gene_data['snps'] = []
        gene_data['genotypes'] = []
        gene_data['trait_associations'] = db.get_trait_associations_for_gene(gene['id'])
        gene_data['health_condition_associations'] = db.get_health_conditions_for_gene(gene['id'])
        gene_data['references'] = db.get_references_for_gene(gene['id'])
        data["genes"].append(gene_data)
    
    import json
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    
    print(f"\nData exported to {filename}")
    db.close()


if __name__ == "__main__":
    example_queries()
    # Uncomment to export data
    # export_to_json()

