"""Download the official Destatis Zensus 2022 grid dataset used by SolarLead.

Dataset: Gebäude mit Wohnraum nach Anzahl der Wohnungen im Gebäude.
Official source URL is published by Destatis on the Zensus 2022 page.

The script only downloads and extracts the official ZIP. It does not modify data.
"""
from __future__ import annotations

import argparse
import shutil
import urllib.request
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
RAW = BASE / "data" / "raw" / "zensus"
URL = "https://www.destatis.de/static/DE/zensus/gitterdaten/Gebaeude_nach_Anzahl_der_Wohnungen_im_Gebaeude.zip"
ZIP_PATH = RAW / "Gebaeude_nach_Anzahl_der_Wohnungen_im_Gebaeude.zip"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Vorhandenen Download ersetzen")
    args = parser.parse_args()

    RAW.mkdir(parents=True, exist_ok=True)
    if ZIP_PATH.exists() and not args.force:
        print(f"ZIP bereits vorhanden: {ZIP_PATH}")
    else:
        print("Lade offiziellen Destatis-Zensus-Datensatz …")
        req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0 SolarLead/0.2"})
        with urllib.request.urlopen(req, timeout=120) as src, ZIP_PATH.open("wb") as dst:
            shutil.copyfileobj(src, dst)
        print(f"Download abgeschlossen: {ZIP_PATH} ({ZIP_PATH.stat().st_size/1024/1024:.1f} MB)")

    extract_dir = RAW / "gebaeude_wohnungen"
    extract_dir.mkdir(exist_ok=True)
    with zipfile.ZipFile(ZIP_PATH) as zf:
        names = zf.namelist()
        zf.extractall(extract_dir)

    csvs = list(extract_dir.rglob("*.csv"))
    print(f"{len(csvs)} CSV-Dateien extrahiert nach: {extract_dir}")
    for f in sorted(csvs):
        print(" -", f.relative_to(BASE))


if __name__ == "__main__":
    main()
