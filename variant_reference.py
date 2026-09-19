"""
Public reference: well-known variants (rs numbers) per gene.

Consumer DNA files list hundreds of thousands of variants by rs number and
nothing else. This table lets an import say which of them fall in genes the
ledger tracks, and what each one is usually called. It is general published
knowledge, holds no personal data, and is deliberately short: the variants a
pharmacogenomic or wellness report is likely to mention, not a catalogue.

Each entry: rs number -> (gene symbol, short description).

How far this has been checked:

- The GENE SYMBOLS were verified against NCBI dbSNP on 2026-09-19; every rs
  number below resolves to the gene it is paired with. Four entries were
  corrected or dropped in that pass.
- The DESCRIPTIONS (star alleles such as "*2, no function", and the
  functional notes) are from general published knowledge and have NOT been
  checked against PharmVar, CPIC or PharmGKB, whose APIs were not reachable.
  Treat them as labels for orientation, not as clinical interpretation, and
  confirm against CPIC or PharmGKB before anyone acts on them.

Re-run the dbSNP check after editing this table:

    python3 scripts/check_variant_reference.py
"""

KNOWN_VARIANTS = {
    # Drug metabolism (cytochrome P450 and friends)
    'rs4244285': ('CYP2C19', '*2, no function'),
    'rs4986893': ('CYP2C19', '*3, no function'),
    'rs12248560': ('CYP2C19', '*17, increased function'),
    'rs1799853': ('CYP2C9', '*2, decreased function'),
    'rs1057910': ('CYP2C9', '*3, no function'),
    'rs3892097': ('CYP2D6', '*4, no function'),
    'rs1065852': ('CYP2D6', '*10, decreased function'),
    'rs28371725': ('CYP2D6', '*41, decreased function'),
    'rs16947': ('CYP2D6', '*2, normal function'),
    'rs762551': ('CYP1A2', '*1F, inducibility'),
    'rs776746': ('CYP3A5', '*3, no function'),
    'rs3745274': ('CYP2B6', '*6, decreased function'),
    'rs9923231': ('VKORC1', '-1639G>A, warfarin sensitivity'),
    'rs4149056': ('SLCO1B1', '*5, decreased function (statins)'),
    'rs1800460': ('TPMT', '*3B'),
    'rs1142345': ('TPMT', '*3C'),
    'rs116855232': ('NUDT15', '*3'),
    'rs3918290': ('DPYD', '*2A, no function'),
    'rs67376798': ('DPYD', 'D949V, decreased function'),
    'rs887829': ('UGT1A1', '*80, linked to *28'),
    'rs1799971': ('OPRM1', 'A118G'),
    'rs4680': ('COMT', 'Val158Met'),
    # Folate, clotting, iron, lipids
    'rs1801133': ('MTHFR', 'C677T'),
    'rs1801131': ('MTHFR', 'A1298C'),
    'rs6025': ('F5', 'Factor V Leiden'),
    'rs1799963': ('F2', 'Prothrombin G20210A'),
    'rs1800562': ('HFE', 'C282Y'),
    'rs1799945': ('HFE', 'H63D'),
    'rs429358': ('APOE', 'e4-defining (with rs7412)'),
    'rs7412': ('APOE', 'e2-defining (with rs429358)'),
    # Common wellness variants
    'rs4988235': ('MCM6', 'lactase persistence; regulates the neighbouring LCT gene'),
    'rs12979860': ('IFNL4', 'interferon lambda response; older papers call this IL28B/IFNL3'),
    'rs1815739': ('ACTN3', 'R577X'),
    'rs1042522': ('TP53', 'P72R'),
    'rs2802292': ('FOXO3', 'longevity association'),
    'rs1800497': ('ANKK1', 'Taq1A (near DRD2)'),
    'rs53576': ('OXTR', 'oxytocin receptor'),
    'rs6265': ('BDNF', 'Val66Met'),
    'rs1544410': ('VDR', 'BsmI'),
    'rs2228570': ('VDR', 'FokI'),
    'rs7903146': ('TCF7L2', 'type 2 diabetes association'),
    'rs9939609': ('FTO', 'obesity association'),
    'rs1801282': ('PPARG', 'Pro12Ala'),
    'rs5443': ('GNB3', 'C825T'),
    'rs1051730': ('CHRNA3', 'nicotine dependence association'),
    'rs4633': ('COMT', 'linked to Val158Met'),
    'rs1800955': ('DRD4', 'promoter'),
    'rs1799990': ('PRNP', 'M129V'),
    'rs334': ('HBB', 'sickle cell (HbS)'),
    'rs1050828': ('G6PD', 'G6PD deficiency (A-)'),
    'rs1801253': ('ADRB1', 'Arg389Gly'),
    'rs1042713': ('ADRB2', 'Arg16Gly'),
    'rs1042714': ('ADRB2', 'Gln27Glu'),
}


def variants_by_gene():
    """{gene symbol: [(rs number, description), ...]} from KNOWN_VARIANTS."""
    grouped = {}
    for rsid, (gene, description) in KNOWN_VARIANTS.items():
        grouped.setdefault(gene, []).append((rsid, description))
    return grouped
