#!/usr/bin/env python3
"""
Public reference: which medications each pharmacogene is known to affect.

This is general knowledge, not anyone's record. The lists follow the
gene-drug pairs with CPIC or FDA prescribing guidance, plus a few well
documented substrates where a panel commonly reports the gene; each entry
says which. The import script pairs a gene's phenotype from a person's test
report with this list, so a doctor's document can say "this gene affects
these drugs" without the report having to spell it out.

Keep drug names lower-case generic names. Add a gene when a report names
one that is missing; never put a person's result here.
"""

# evidence: 'guideline' = CPIC/FDA prescribing guidance exists for the pair;
# 'substrate' = well documented metabolic pathway, no formal guideline;
# 'limited' = association reported by panels, evidence still developing.
GENE_DRUGS = {
    'CYP2D6': {
        'evidence': 'guideline',
        'drugs': ['codeine', 'tramadol', 'hydrocodone', 'oxycodone', 'tamoxifen',
                  'ondansetron', 'tropisetron', 'atomoxetine', 'amitriptyline',
                  'nortriptyline', 'imipramine', 'desipramine', 'clomipramine',
                  'doxepin', 'trimipramine', 'paroxetine', 'fluvoxamine',
                  'venlafaxine', 'vortioxetine', 'aripiprazole', 'brexpiprazole',
                  'risperidone', 'haloperidol', 'pimozide', 'metoprolol',
                  'carvedilol', 'propafenone', 'flecainide', 'dextromethorphan',
                  'eliglustat', 'pitolisant'],
    },
    'CYP2C19': {
        'evidence': 'guideline',
        'drugs': ['clopidogrel', 'citalopram', 'escitalopram', 'sertraline',
                  'amitriptyline', 'clomipramine', 'imipramine', 'doxepin',
                  'trimipramine', 'omeprazole', 'lansoprazole', 'pantoprazole',
                  'dexlansoprazole', 'voriconazole', 'clobazam', 'brivaracetam',
                  'diazepam'],
    },
    'CYP2C9': {
        'evidence': 'guideline',
        'drugs': ['warfarin', 'phenytoin', 'fosphenytoin', 'celecoxib',
                  'flurbiprofen', 'ibuprofen', 'lornoxicam', 'meloxicam',
                  'piroxicam', 'tenoxicam', 'siponimod', 'dronabinol'],
    },
    'VKORC1': {
        'evidence': 'guideline',
        'drugs': ['warfarin'],
    },
    'CYP3A5': {
        'evidence': 'guideline',
        'drugs': ['tacrolimus'],
    },
    'CYP3A4': {
        'evidence': 'substrate',
        'drugs': ['tacrolimus', 'cyclosporine', 'midazolam', 'alprazolam',
                  'quetiapine', 'atorvastatin', 'simvastatin', 'amlodipine',
                  'fentanyl', 'methadone'],
    },
    'CYP1A2': {
        'evidence': 'substrate',
        'drugs': ['clozapine', 'olanzapine', 'duloxetine', 'fluvoxamine',
                  'theophylline', 'tizanidine', 'caffeine'],
    },
    'CYP2B6': {
        'evidence': 'guideline',
        'drugs': ['efavirenz', 'sertraline', 'bupropion', 'methadone', 'ketamine'],
    },
    'UGT1A1': {
        'evidence': 'guideline',
        'drugs': ['irinotecan', 'atazanavir', 'belinostat', 'nilotinib', 'pazopanib'],
    },
    'UGT1A4': {
        'evidence': 'substrate',
        'drugs': ['lamotrigine'],
    },
    'UGT2B15': {
        'evidence': 'substrate',
        'drugs': ['lorazepam', 'oxazepam'],
    },
    'HLA-A': {
        'evidence': 'guideline',
        'drugs': ['carbamazepine'],
    },
    'HLA-B': {
        'evidence': 'guideline',
        'drugs': ['carbamazepine', 'oxcarbazepine', 'phenytoin', 'fosphenytoin',
                  'abacavir', 'allopurinol', 'flucloxacillin'],
    },
    'SLCO1B1': {
        'evidence': 'guideline',
        'drugs': ['simvastatin', 'atorvastatin', 'rosuvastatin', 'pravastatin',
                  'lovastatin', 'fluvastatin', 'pitavastatin'],
    },
    'TPMT': {
        'evidence': 'guideline',
        'drugs': ['azathioprine', 'mercaptopurine', 'thioguanine'],
    },
    'NUDT15': {
        'evidence': 'guideline',
        'drugs': ['azathioprine', 'mercaptopurine', 'thioguanine'],
    },
    'DPYD': {
        'evidence': 'guideline',
        'drugs': ['fluorouracil', 'capecitabine'],
    },
    'CES1A1': {
        'evidence': 'substrate',
        'drugs': ['methylphenidate', 'oseltamivir', 'dabigatran', 'enalapril'],
    },
    'SLC6A4': {
        'evidence': 'limited',
        'drugs': ['citalopram', 'escitalopram', 'sertraline', 'fluoxetine', 'paroxetine'],
    },
    'HTR2A': {
        'evidence': 'limited',
        'drugs': ['citalopram', 'escitalopram', 'sertraline', 'fluoxetine', 'paroxetine'],
    },
    'COMT': {
        'evidence': 'limited',
        'drugs': ['methylphenidate', 'amphetamine'],
    },
    'ADRA2A': {
        'evidence': 'limited',
        'drugs': ['methylphenidate', 'clonidine', 'guanfacine'],
    },
    'OPRM1': {
        'evidence': 'limited',
        'drugs': ['naltrexone', 'morphine', 'fentanyl'],
    },
    'MTHFR': {
        'evidence': 'limited',
        'drugs': ['methotrexate', 'folic acid'],
    },
    'F5': {
        'evidence': 'guideline',
        'drugs': ['estrogen-containing contraceptives', 'hormone replacement therapy'],
    },
    'F2': {
        'evidence': 'guideline',
        'drugs': ['estrogen-containing contraceptives', 'hormone replacement therapy'],
    },
}

EVIDENCE_LABELS = {
    'guideline': 'prescribing guideline (CPIC/FDA)',
    'substrate': 'documented metabolic pathway',
    'limited': 'reported association, evidence still developing',
}


def drugs_for_gene(gene_symbol: str) -> list:
    entry = GENE_DRUGS.get(gene_symbol.upper())
    return list(entry['drugs']) if entry else []


def evidence_for_gene(gene_symbol: str) -> str:
    entry = GENE_DRUGS.get(gene_symbol.upper())
    return entry['evidence'] if entry else ''
