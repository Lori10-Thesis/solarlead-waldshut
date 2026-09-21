"""Print LGL WFS capabilities relevant to the building importer."""
import os
import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
from download_lgl_buildings import WFS_URL, capabilities

print("Endpoint:", WFS_URL)
names, formats = capabilities()
print("\nFeatureTypes:")
for n in names:
    if any(k in n.lower() for k in ("building", "gebaeude", "gebäude")):
        print(" *", n)
    else:
        print("  ", n)
print("\nOutput-Formate:")
for f in formats:
    print(" -", f)
