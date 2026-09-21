PROVIDERS = {
    'LGL_BW': {
        'label': 'LGL Baden-Württemberg',
        'kind': 'wfs',
        'endpoint': 'https://owsproxy.lgl-bw.de/owsproxy/wfs/WFS_INSP_BW_Gebaeude_ALKIS',
    },
    'GEOBASIS_NRW': {
        'label': 'Geobasis NRW',
        'kind': 'wfs',
        'endpoint': 'https://www.wfs.nrw.de/geobasis/wfs_nw_alkis_vereinfacht',
    },
}

def get_building_provider(code: str):
    return PROVIDERS.get(code)
