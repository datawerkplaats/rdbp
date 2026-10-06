import csv
import os
import re
import unicodedata
from collections import OrderedDict, defaultdict
from datetime import date, timedelta

DATA      = os.path.dirname(os.path.abspath(__file__)) + os.sep
HA_MSZ_CSV = DATA + "dummydata_HA_MSZ.csv"
VVT_CSV    = DATA + "dummydata_VVT.csv"
HA_MSZ_TTL = DATA + "testdata_HA_MSZ.ttl"
VVT_TTL    = DATA + "testdata_VVT.ttl"

PREFIXES = """\
@prefix dummy:    <http://data.dummyzorg.nl/> .
@prefix onz-g:    <http://purl.org/ozo/onz-g#> .
@prefix onz-zorg: <http://purl.org/ozo/onz-zorg#> .
@prefix onz-org:  <http://purl.org/ozo/onz-org#> .
@prefix ext:      <http://data.dummyzorg.nl/ext#> .
@prefix owl:      <http://www.w3.org/2002/07/owl#> .
@prefix xsd:      <http://www.w3.org/2001/XMLSchema#> .
@prefix rdfs:     <http://www.w3.org/2000/01/rdf-schema#> .\
"""

ONTOLOGIE_INSTANTIES = """
################################
# Ontologie-instanties
################################

onz-zorg:4VV  a onz-zorg:ZorgProfiel .
onz-zorg:5VV  a onz-zorg:ZorgProfiel .
onz-zorg:6VV  a onz-zorg:ZorgProfiel .
onz-zorg:7VV  a onz-zorg:ZorgProfiel .
onz-zorg:8VV  a onz-zorg:ZorgProfiel .
onz-zorg:9BVV a onz-zorg:ZorgProfiel .
onz-zorg:10VV a onz-zorg:ZorgProfiel .

onz-zorg:pgb        a onz-zorg:Leveringsvorm .
onz-zorg:vpt        a onz-zorg:Leveringsvorm .
onz-zorg:mpt        a onz-zorg:Leveringsvorm .
onz-zorg:instelling a onz-zorg:Leveringsvorm .

ext:HACode  a owl:Class ; rdfs:subClassOf ext:ZorgCodering ; rdfs:label "Huisartsenzorg codering" .
ext:MSZCode a owl:Class ; rdfs:subClassOf ext:ZorgCodering ; rdfs:label "Medisch Specialistische Zorg codering" .
ext:VVTCode a owl:Class ; rdfs:subClassOf ext:ZorgCodering ; rdfs:label "VVT codering" .\
"""

INDICATIE_CLASS = {
    'WLZ':                              'onz-zorg:WlzIndicatie',
    'ZVW':                              'onz-zorg:ZvwIndicatie',
    'WMO':                              'onz-zorg:WmoIndicatie',
    'Indicatiebesluit partnerverblijf': 'onz-zorg:IndicatieBesluitPartnerverblijf',
}

LEVERINGSVORM = {
    'PGB':                  'onz-zorg:pgb',
    'VPT':                  'onz-zorg:vpt',
    'MPT':                  'onz-zorg:mpt',
    'Verblijf in instelling': 'onz-zorg:instelling',
}

# Shared location registry so IRIs are consistent across both TTL files
locations: OrderedDict[str, str] = OrderedDict()

def slugify(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    s = re.sub(r'[^a-zA-Z0-9]', '_', s.strip())
    return re.sub(r'_+', '_', s).strip('_')

def vestiging(label):
    label = label.strip()
    if label not in locations:
        locations[label] = f"dummy:Vestiging_{slugify(label)}"
    return locations[label]

# Organisatie per vestiging
HZOIJ_VESTIGINGEN = {
    'Huisartsenpost Slingeland (Doetinchem)',
    'Huisartsenpraktijk De Kruisberg (Doetinchem)',
    'Huisartsenpraktijk Didam',
    'Huisartsenpraktijk Overstegen (Doetinchem)',
    'Huisartsenpraktijk Silvolde',
    'Huisartsenpraktijk Terborg',
    'Huisartsenpraktijk Ulft',
    'Huisartsenpraktijk Varsseveld',
    'Huisartsenpraktijk Zelhem',
    'Medisch Centrum Wehl',
}

def organisatie(label):
    if label in HZOIJ_VESTIGINGEN:
        return 'HZOIJ'
    for org in ('Sensire', 'Marga Klompé', 'Slingeland'):
        if label.startswith(org):
            return org
    return None

def to_iso(s):
    s = s.strip()
    if not s or s == '-':
        return None
    d, m, y = s.split('-')
    return f"{y}-{m.zfill(2)}-{d.zfill(2)}"

MSZ_WORDS = {'Ziekenhuis', 'Academisch', 'Diakonessenhuis', 'St.', 'Slingeland', 'SEH', 'poli'}

CODE_LABEL = {'ext:HACode': 'HA', 'ext:MSZCode': 'MSZ', 'ext:VVTCode': 'VVT'}
SECTOR_CODE = {label: code for code, label in CODE_LABEL.items()}

def code_type(locatie):
    if any(w in locatie for w in ('Huisartsenpraktijk', 'Huisartsenpost', 'Spoedpost')):
        return 'ext:HACode'
    if any(w in locatie for w in MSZ_WORDS):
        return 'ext:MSZCode'
    return 'ext:VVTCode'

def read_csv(path):
    with open(path, newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

# ── HA/MSZ ───────────────────────────────────────────────────────────────────

rows_ha_msz = read_csv(HA_MSZ_CSV)

# Group and sort contacts per client
clients_ha_msz: dict[str, list] = defaultdict(list)
for r in rows_ha_msz:
    clients_ha_msz[r['clientnummer']].append(r)
for rows in clients_ha_msz.values():
    rows.sort(key=lambda r: date(*reversed([int(x) for x in r['startdatum'].split('-')])))

ha_msz_lines = [PREFIXES, ONTOLOGIE_INSTANTIES, '']

# Collect vestigingen first (needed at top of file, but built during client loop)
client_blocks_ha = []

for clientnr, rows in clients_ha_msz.items():
    naam = rows[0]['naam']
    human_iri = f"dummy:Human_{clientnr}"
    block = [f"# --- {naam} ({clientnr}) ---", '']
    dood = next((to_iso(r['overlijdensdatum']) for r in rows if (r.get('overlijdensdatum') or '').strip()), None)
    if dood:
        block.append(f'{human_iri} a onz-g:Human ;')
        block.append(f'    rdfs:label           "{naam}" ;')
        block.append(f'    onz-g:hasDateOfDeath "{dood}"^^xsd:date .')
    else:
        block.append(f'{human_iri} a onz-g:Human ; rdfs:label "{naam}" .')
    block.append('')

    for i, r in enumerate(rows, 1):
        iso      = to_iso(r['startdatum'])
        ves_iri  = vestiging(r['locatie'])
        cont_iri = f"dummy:Contact_{clientnr}_{i}"
        code_iri = f"dummy:Code_{clientnr}_{i}"
        ind_raw  = r['indicatie'].strip()
        ind_cls  = INDICATIE_CLASS.get(ind_raw)
        ind_iri  = f"dummy:Indicatie_{clientnr}_{i}"
        ctype    = SECTOR_CODE.get((r.get('sector') or '').strip()) or code_type(r['locatie'])

        block.append(f"{cont_iri} a onz-zorg:ZorgProces ;")
        block.append(f"    onz-g:hasParticipant       {human_iri} ;")
        block.append(f"    onz-g:startDatum           \"{iso}\"^^xsd:date ;")
        block.append(f"    onz-g:hasPerdurantLocation {ves_iri} ;")
        block.append(f"    onz-g:definedBy            {code_iri}" + (" ;" if ind_cls else " ."))
        if ind_cls:
            block.append(f"    onz-g:definedBy            {ind_iri} .")
        block.append('')

        block.append(f"{code_iri} a {ctype} ; rdfs:label \"{CODE_LABEL[ctype]}\" .")
        block.append('')

        if ind_cls:
            block.append(f"{ind_iri} a {ind_cls} ;")
            block.append(f"    onz-g:isAbout {human_iri} .")
            block.append('')

    client_blocks_ha.append('\n'.join(block))

# ── VVT ──────────────────────────────────────────────────────────────────────

rows_vvt = read_csv(VVT_CSV)

clients_vvt: dict[str, list] = defaultdict(list)
for r in rows_vvt:
    clients_vvt[r['clientnummer']].append(r)

vvt_lines = [PREFIXES, ONTOLOGIE_INSTANTIES, '']
client_blocks_vvt = []

for clientnr, rows in clients_vvt.items():
    persoon = rows[0]['persoon']
    human_iri = f"dummy:Human_{clientnr}"
    block = [f"# --- {persoon} ({clientnr}) ---", '']
    dood = next((to_iso(r['overlijdensdatum']) for r in rows if r.get('overlijdensdatum', '').strip()), None)
    if dood:
        block.append(f'{human_iri} a onz-g:Human ;')
        block.append(f'    rdfs:label           "{persoon}" ;')
        block.append(f'    onz-g:hasDateOfDeath "{dood}"^^xsd:date .')
    else:
        block.append(f'{human_iri} a onz-g:Human ; rdfs:label "{persoon}" .')
    block.append('')

    for i, r in enumerate(rows, 1):
        start    = to_iso(r['startDatum'])
        eind     = to_iso(r['einddatum'])
        ves_iri  = vestiging(r['locatie'])
        zp_iri   = f"onz-zorg:{r['zorgprofiel'].strip()}"
        lv_iri   = LEVERINGSVORM.get(r['leveringsvorm'].strip())
        ind_iri  = f"dummy:Indicatie_WLZ_{clientnr}_{i}"
        np_iri   = f"dummy:NursingProcess_{clientnr}_{i}"

        # WlzIndicatie
        ind_props = [
            f"    onz-g:isAbout    {human_iri}",
            f"    onz-g:startDatum \"{start}\"^^xsd:date",
        ]
        if eind:
            ind_props.append(f"    onz-g:eindDatum  \"{eind}\"^^xsd:date")
        ind_props.append(f"    onz-g:hasPart    {zp_iri}")
        if lv_iri:
            ind_props.append(f"    onz-g:hasPart    {lv_iri}")

        block.append(f"{ind_iri} a onz-zorg:WlzIndicatie ;")
        for j, prop in enumerate(ind_props):
            block.append(prop + (' ;' if j < len(ind_props) - 1 else ' .'))
        block.append('')

        # NursingProcess
        np_props = [
            f"    onz-g:hasParticipant          {human_iri}",
            f"    onz-g:definedBy               {ind_iri}",
            f"    onz-g:startDatum              \"{start}\"^^xsd:date",
        ]
        if eind:
            np_props.append(f"    onz-g:eindDatum               \"{eind}\"^^xsd:date")
        np_props.append(f"    onz-g:hasPerdurantLocation    {ves_iri}")

        block.append(f"{np_iri} a onz-zorg:NursingProcess ;")
        for j, prop in enumerate(np_props):
            block.append(prop + (' ;' if j < len(np_props) - 1 else ' .'))
        block.append('')

    client_blocks_vvt.append('\n'.join(block))

# ── Write ─────────────────────────────────────────────────────────────────────

def vestiging_block():
    lines = ['################################', '# Organisaties', '################################', '']
    orgs = OrderedDict((o, f"dummy:Organisatie_{slugify(o)}")
                       for o in map(organisatie, locations) if o)
    for label, iri in orgs.items():
        lines.append(f'{iri} a onz-g:Business ; rdfs:label "{label}" .')
        lines.append('')
    lines += ['################################', '# Vestigingen', '################################', '']
    for label, iri in locations.items():
        org = organisatie(label)
        if org:
            lines.append(f'{iri} a onz-org:Vestiging ;')
            lines.append(f'    rdfs:label          "{label}" ;')
            lines.append(f'    onz-org:vestigingVan {orgs[org]} .')
        else:
            lines.append(f'{iri} a onz-org:Vestiging ; rdfs:label "{label}" .')
        lines.append('')
    return lines

# HA/MSZ TTL — vestigingen collected after both loops, so write after VVT loop
ha_msz_lines += vestiging_block()
ha_msz_lines += ['################################', '# HA/MSZ contacten', '################################', '']
ha_msz_lines += client_blocks_ha

vvt_lines += vestiging_block()
vvt_lines += ['################################', '# VVT zorgperioden', '################################', '']
vvt_lines += client_blocks_vvt

with open(HA_MSZ_TTL, 'w', encoding='utf-8') as f:
    f.write('\n'.join(ha_msz_lines))

with open(VVT_TTL, 'w', encoding='utf-8') as f:
    f.write('\n'.join(vvt_lines))

print(f"HA/MSZ: {len(clients_ha_msz)} clients, {len(rows_ha_msz)} contacts → {HA_MSZ_TTL}")
print(f"VVT:    {len(clients_vvt)} clients, {len(rows_vvt)} periods   → {VVT_TTL}")
print(f"Shared vestigingen: {len(locations)}")
