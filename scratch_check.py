import json

nb = json.load(open(r'd:\private\multimedia database system\src\services\histograms\histogram_custom.ipynb', encoding='utf-8'))

for i, c in enumerate(nb['cells']):
    cell_id = c.get('id', '?')
    cell_type = c['cell_type']
    source_text = ''.join(c['source'])
    
    if 'samsample' in source_text.lower():
        print(f"FOUND 'samsample' in Cell {i} (id={cell_id}, type={cell_type})")
        print(source_text[:500])
        print("---")
    
    if 'sample_path' in source_text:
        print(f"Cell {i} (id={cell_id}, type={cell_type}) uses 'sample_path'")

print("\nCell index -> id mapping (code cells only):")
code_idx = 0
for i, c in enumerate(nb['cells']):
    if c['cell_type'] == 'code':
        print(f"  code_cell[{code_idx}] = notebook_cell[{i}], id={c.get('id','?')}")
        code_idx += 1
