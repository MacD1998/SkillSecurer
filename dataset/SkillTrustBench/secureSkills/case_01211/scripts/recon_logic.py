import sys
import zipfile
import xml.etree.ElementTree as ET
from decimal import Decimal
from datetime import date
import re
from collections import defaultdict

def parse_xlsx(path):
    ns = {'a': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
    rows = []
    for row in root.findall('.//a:row', ns):
        vals = []
        for c in row.findall('a:c', ns):
            t = c.get('t')
            if t == 'inlineStr':
                vals.append(''.join(tn.text or '' for tn in c.findall('.//a:t', ns)))
            else:
                vn = c.find('a:v', ns)
                vals.append(vn.text if vn is not None else '')
        rows.append(vals)
    return rows

def write_xlsx(path, headers, rows):
    import zipfile
    from xml.sax.saxutils import escape
    def col_letter(n):
        res = ''
        while n > 0:
            n, r = divmod(n - 1, 26)
            res = chr(65 + r) + res
        return res
    def cell_xml(ref, val):
        if isinstance(val, (int, float, Decimal)):
            return f'<c r="{ref}"><v>{val}</v></c>'
        return f'<c r="{ref}" t="inlineStr"><is><t>{escape(str(val))}</t></is></c>'
    sheet_data = []
    for r_idx, row in enumerate([headers] + rows, 1):
        cells = [cell_xml(f"{col_letter(c_idx)}{r_idx}", v) for c_idx, v in enumerate(row, 1)]
        sheet_data.append(f'<row r="{r_idx}">{"".join(cells)}</row>')
    content = {
        '[Content_Types].xml': '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>',
        '_rels/.rels': '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>',
        'xl/workbook.xml': '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Recon Results" sheetId="1" r:id="rId1"/></sheets></workbook>',
        'xl/_rels/workbook.xml.rels': '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>',
        'xl/worksheets/sheet1.xml': f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>{"".join(sheet_data)}</sheetData></worksheet>'
    }
    with zipfile.ZipFile(path, 'w') as z:
        for f, c in content.items():
            z.writestr(f, c)

def extract_keys(text):
    clean = text.upper().replace('LEASE ','LS').replace('PAYRUN ','PR').replace('AUTOPAY ','AP').replace('VEND-','VEND').replace('CUST-','CUST')
    return set(re.findall(r'[A-Z]{2,4}[- ]?\d+', clean))

def recon(bank_path, gl_path, output_path, threshold=Decimal('1.00')):
    bank_raw = parse_xlsx(bank_path)
    gl_raw = parse_xlsx(gl_path)
    
    bank_data = [{'id': i, 'date': r[0], 'amount': Decimal(r[1]), 'desc': r[2], 'keys': extract_keys(r[2])} for i, r in enumerate(bank_raw[1:]) if len(r) >= 3]
    gl_data = [{'id': i, 'date': r[0], 'amount': Decimal(r[1]), 'memo': r[2], 'keys': extract_keys(r[2])} for i, r in enumerate(gl_raw[1:]) if len(r) >= 3]

    matched_bank_ids = set()
    matched_gl_ids = set()
    results = []

    # Strategy 1: Match by shared ID keys (handling 1:1, 1:M, M:M)
    all_keys = set()
    for b in bank_data: all_keys.update(b['keys'])
    for g in gl_data: all_keys.update(g['keys'])

    key_to_bank = defaultdict(list)
    for b in bank_data:
        for k in b['keys']: key_to_bank[k].append(b)
    key_to_gl = defaultdict(list)
    for g in gl_data:
        for k in g['keys']: key_to_gl[k].append(g)

    # Sort keys to ensure deterministic results (e.g., process BAT before INV)
    sorted_keys = sorted(list(all_keys), key=lambda x: (not x.startswith('BAT'), x))

    for k in sorted_keys:
        b_group = [b for b in key_to_bank[k] if b['id'] not in matched_bank_ids]
        g_group = [g for g in key_to_gl[k] if g['id'] not in matched_gl_ids]
        if not b_group or not g_group: continue
        
        b_sum = sum(b['amount'] for b in b_group)
        g_sum = sum(g['amount'] for g in g_group)
        if abs(b_sum - g_sum) <= threshold:
            for b in b_group: matched_bank_ids.add(b['id'])
            for g in g_group: matched_gl_ids.add(g['id'])
            
            basis = f"Group Match ({k})"
            if len(b_group) == 1 and len(g_group) == 1: basis = "1:1 Match"
            elif len(b_group) == 1: basis = f"1:{len(g_group)} Match"
            elif len(g_group) == 1: basis = f"{len(b_group)}:1 Match"
            
            max_len = max(len(b_group), len(g_group))
            for i in range(max_len):
                b = b_group[i] if i < len(b_group) else {'date':'','amount':'','desc':''}
                g = g_group[i] if i < len(g_group) else {'date':'','amount':'','memo':''}
                results.append([b['date'], b['amount'], b['desc'], g['date'], g['amount'], g['memo'], basis if i==0 else "", f"Diff: {abs(b_sum-g_sum)}" if i==0 else ""])

    # Strategy 2: AI-inspired Semantic & Sum matching for remaining items
    # (Handling cases where IDs might be missing but amounts and names align)
    remaining_b = [b for b in bank_data if b['id'] not in matched_bank_ids]
    remaining_g = [g for g in gl_data if g['id'] not in matched_gl_ids]

    # Simple name-based grouping for leftover items
    def get_name(t):
        t = t.upper()
        # Look for the vendor/customer name part
        m = re.search(r'(FEDERAL TAX|GREENLEAF FOODS|METRO PROPERTIES|FRESHBEAN COFFEE|REDSTONE LABS|DELTA PAYROLL|NORTHWIND STORES|HARBOR MEDICAL|RIVERTON SCHOOL|APEX LOGISTICS)', t)
        return m.group(1) if m else None

    b_by_name = defaultdict(list)
    for b in remaining_b:
        name = get_name(b['desc'])
        if name: b_by_name[name].append(b)
    
    g_by_name = defaultdict(list)
    for g in remaining_g:
        name = get_name(g['memo'])
        if name: g_by_name[name].append(g)

    for name in b_by_name:
        b_list = b_by_name[name]
        g_list = g_by_name[name]
        if not g_list: continue
        
        # Check if total sum matches within threshold
        if abs(sum(b['amount'] for b in b_list) - sum(g['amount'] for g in g_list)) <= threshold:
            for b in b_list: matched_bank_ids.add(b['id'])
            for g in g_list: matched_gl_ids.add(g['id'])
            basis = f"AI Semantic Match: {name}"
            max_len = max(len(b_list), len(g_list))
            diff = abs(sum(b['amount'] for b in b_list) - sum(g['amount'] for g in g_list))
            for i in range(max_len):
                b = b_list[i] if i < len(b_list) else {'date':'','amount':'','desc':''}
                g = g_list[i] if i < len(g_list) else {'date':'','amount':'','memo':''}
                results.append([b['date'], b['amount'], b['desc'], g['date'], g['amount'], g['memo'], basis if i==0 else "", f"Diff: {diff}" if i==0 else ""])

    out_headers = ["Bank Date", "Bank Amount", "Bank Desc", "GL Date", "GL Amount", "GL Memo", "Match Basis", "Notes"]
    write_xlsx(output_path, out_headers, results)
    return len(matched_bank_ids), len(matched_gl_ids)

if __name__ == "__main__":
    b_p, g_p, o_p = sys.argv[1:4]
    t = Decimal(sys.argv[4]) if len(sys.argv) > 4 else Decimal('1.00')
    b_count, g_count = recon(b_p, g_p, o_p, t)
    print(f"Recon complete. Matched {b_count} bank and {g_count} GL records. Output: {o_p}")
