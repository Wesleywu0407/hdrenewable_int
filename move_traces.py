import sys

with open("scripts/08_generate_infrastructure_charts.py", "r") as f:
    lines = f.readlines()

start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if "# -- Renewable Energy Zone polygon overlays" in line:
        start_idx = i
    if "Failed to load {tx_path.name}" in line and start_idx != -1:
        end_idx = i + 1
        break

if start_idx == -1 or end_idx == -1:
    print("Could not find block")
    sys.exit(1)

block = lines[start_idx:end_idx]
del lines[start_idx:end_idx]

# Modify opacity in block
for i, line in enumerate(block):
    if "fillcolor='rgba(154, 160, 166, 0.2)'" in line:
        block[i] = line.replace("0.2", "0.1")
    elif "line=dict(color='#9AA0A6', width=2)" in line:
        block[i] = line.replace("'#9AA0A6'", "'rgba(154, 160, 166, 0.4)'")
    elif "line=dict(color='rgba(64, 160, 255, 0.6)', width=1.5)" in line:
        block[i] = line.replace("0.6", "0.3")

# Find insert point: "# -- BESS trace"
insert_idx = -1
for i, line in enumerate(lines):
    if "# -- BESS trace" in line:
        insert_idx = i
        break

if insert_idx == -1:
    print("Could not find insert idx")
    sys.exit(1)

lines = lines[:insert_idx] + block + ["\n"] + lines[insert_idx:]

with open("scripts/08_generate_infrastructure_charts.py", "w") as f:
    f.writelines(lines)

print("Moved block and reduced opacity successfully")
