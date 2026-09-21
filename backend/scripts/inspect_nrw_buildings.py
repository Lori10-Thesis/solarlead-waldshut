"""Connectivity check for the NRW building provider used by the Köln market."""
import urllib.request
URL='https://www.wfs.nrw.de/geobasis/wfs_nw_alkis_vereinfacht?SERVICE=WFS&REQUEST=GetCapabilities'
print('Prüfe Geobasis NRW WFS …')
with urllib.request.urlopen(URL, timeout=30) as r:
    data=r.read(4000).decode('utf-8','ignore')
print('HTTP OK; erste Capabilities-Zeichen:')
print(data[:1200])
