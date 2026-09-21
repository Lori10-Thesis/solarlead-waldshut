def lead_score(data: dict) -> int:
    """Buyer-intent-first score. Technical fit matters, but intent dominates."""
    score = 0

    # Kaufabsicht: bis 40
    timeframe = data.get('purchase_timeframe')
    score += {'immediately': 25, '30_days': 20, '3_months': 12, 'information': 2}.get(timeframe, 2)
    if data.get('wants_installation'):
        score += 10
    pref = data.get('product_preference')
    if pref == 'complete_with_installation':
        score += 5
    elif pref == 'consultation':
        score += 3

    # Projektfit: bis 30
    if data.get('installation_location') == 'balcony':
        score += 8
    ori = data.get('orientation')
    if ori in {'south','south_west','south_east'}:
        score += 8
    elif ori in {'west','east'}:
        score += 5
    if data.get('shading') == 'low':
        score += 6
    elif data.get('shading') == 'medium':
        score += 3
    score += 8 if data.get('owner_status') == 'owner' else 4 if data.get('owner_status') == 'tenant' else 0

    # Leadqualität: bis 30
    if data.get('phone'):
        score += 10
    if data.get('contact_time'):
        score += 5
    if data.get('review_confirmed'):
        score += 5
    if data.get('street') and data.get('house_number'):
        score += 3
    if data.get('email'):
        score += 3
    geo_fit = data.get('geo_fit_score')
    if isinstance(geo_fit, (int, float)):
        if geo_fit >= 80: score += 4
        elif geo_fit >= 65: score += 2

    return min(int(score), 100)


def potential_score_from_pv(pv_yield_kwh: float, shading: str, orientation: str) -> int:
    yield_score = min(55, int((pv_yield_kwh / 800) * 55))
    shade_bonus = {'low': 25, 'medium': 14, 'high': 3}.get(shading, 8)
    orientation_bonus = {
        'south': 20, 'south_west': 18, 'south_east': 18,
        'west': 12, 'east': 12, 'north': 2
    }.get(orientation, 8)
    return min(100, yield_score + shade_bonus + orientation_bonus)
