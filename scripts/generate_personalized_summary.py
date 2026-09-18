#!/usr/bin/env python3
"""
Summary of the most significant findings in the record — built entirely from
what is in the database. Nothing about any particular person is written here:
conditions, traits, genes and interactions come from the tables, and a record
with different contents produces a different summary.

CLI: writes a Markdown summary to OUTPUT_DIR. The web app and the PDF
generator import generate_summary_html().
"""

import sys
from collections import defaultdict
from html import escape
from pathlib import Path

# Add project root to Python path
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from config import OUTPUT_DIR
from database_manager import GeneticProfileDB


def collect_findings(db: GeneticProfileDB) -> dict:
    """Group every association in the database by condition, trait and gene."""
    genes = db.get_all_genes()
    by_condition = defaultdict(list)
    by_trait = defaultdict(list)
    interactions = []
    for gene in genes:
        symbol = gene['gene_symbol']
        for c in db.get_health_conditions_for_gene(gene['id']):
            by_condition[c.get('condition_name', 'Unspecified')].append((symbol, c))
        for t in db.get_trait_associations_for_gene(gene['id']):
            by_trait[t.get('trait_name', 'Unspecified')].append((symbol, t))
        for i in db.get_interacting_genes(symbol):
            interactions.append((symbol, i))
    return {
        'genes': genes,
        'by_condition': dict(sorted(by_condition.items(), key=lambda kv: (-len(kv[1]), kv[0]))),
        'by_trait': dict(sorted(by_trait.items(), key=lambda kv: (-len(kv[1]), kv[0]))),
        'interactions': interactions,
    }


def _note(row: dict) -> str:
    for key in ('notes', 'description', 'association_notes', 'clinical_significance'):
        if row.get(key):
            return str(row[key])
    return ''


def generate_summary_markdown(db: GeneticProfileDB = None) -> str:
    owns_db = db is None
    if owns_db:
        db = GeneticProfileDB()
    f = collect_findings(db)
    out = ["# Genetic Profile - Key Findings Summary\n",
           "*Generated from the record in this Health Ledger database.*\n", "---\n"]
    out.append("## Health conditions with genetic associations\n")
    for condition, rows in f['by_condition'].items():
        out.append(f"### {condition}\n")
        for symbol, row in rows:
            note = _note(row)
            out.append(f"- **{symbol}**" + (f": {note}" if note else ""))
        out.append("")
    out.append("## Traits\n")
    for trait, rows in f['by_trait'].items():
        out.append(f"- **{trait}**: " + ", ".join(sorted({s for s, _ in rows})))
    out.append("")
    if f['interactions']:
        out.append("## Gene-gene interactions\n")
        seen = set()
        for symbol, i in f['interactions']:
            other = i.get('gene_symbol') or i.get('interacting_gene') or i.get('gene2_symbol') or ''
            key = tuple(sorted((symbol, str(other))))
            if key in seen:
                continue
            seen.add(key)
            note = _note(i)
            out.append(f"- **{symbol} + {other}**" + (f": {note}" if note else ""))
        out.append("")
    out.append("---\n*For detail on each gene, see the full genetic profile document.*\n")
    if owns_db:
        db.close()
    return "\n".join(out)


def generate_summary_html(db: GeneticProfileDB = None) -> str:
    """Generate summary HTML from database for web display."""
    owns_db = db is None
    if owns_db:
        db = GeneticProfileDB()
    f = collect_findings(db)
    h = ["<h1>Genetic Profile - Key Findings Summary</h1>",
         "<p><em>Generated from the record in this database.</em></p>", "<hr>"]
    h.append("<h2>Overview</h2><ul>")
    h.append(f"<li><strong>Genes:</strong> {len(f['genes'])} analyzed</li>")
    h.append(f"<li><strong>Health conditions:</strong> {len(f['by_condition'])}</li>")
    h.append(f"<li><strong>Traits:</strong> {len(f['by_trait'])}</li></ul>")
    h.append("<h2>Health conditions with genetic associations</h2>")
    for condition, rows in f['by_condition'].items():
        h.append(f"<h3>{escape(condition)}</h3><ul>")
        for symbol, row in rows:
            note = _note(row)
            h.append(f"<li><strong>{escape(symbol)}</strong>" + (f": {escape(note)}" if note else "") + "</li>")
        h.append("</ul>")
    h.append("<h2>Traits</h2><ul>")
    for trait, rows in f['by_trait'].items():
        h.append(f"<li><strong>{escape(trait)}</strong>: " + escape(", ".join(sorted({s for s, _ in rows}))) + "</li>")
    h.append("</ul>")
    h.append("<p><em>For detailed information, see the full profile.</em></p>")
    if owns_db:
        db.close()
    return "\n".join(h)


if __name__ == "__main__":
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    target = OUTPUT_DIR / "Genetic_Profile_Summary.md"
    target.write_text(generate_summary_markdown(), encoding="utf-8")
    print(f"[OK] Summary generated: {target}")
