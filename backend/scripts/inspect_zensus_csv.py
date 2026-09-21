"""Print the official CSV schema and a few rows without loading the file into RAM."""
from __future__ import annotations
import argparse, csv
from pathlib import Path
from import_zensus_waldshut import choose_100m_csv, sniff


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--csv")
    args=ap.parse_args()
    p=choose_100m_csv(args.csv)
    enc, delim=sniff(p)
    print("Datei:",p)
    print("Encoding:",enc,"Delimiter:",repr(delim))
    with p.open(encoding=enc,newline="",errors="replace") as f:
        r=csv.DictReader(f,delimiter=delim)
        print("Spalten:",r.fieldnames)
        for i,row in enumerate(r):
            print(row)
            if i>=4: break

if __name__=='__main__': main()
