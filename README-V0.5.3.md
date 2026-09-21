# SolarLead V0.5.3 – Trust, Legal Config & Named Partner Consent

V0.5.3 prepares controlled organic public acquisition without forcing a blanket partner-transfer consent.

## Core changes
- Consumer-facing brand can differ from the internal SolarLead platform brand.
- Operator data is configured centrally via `deploy/configure-public-site.py`.
- Impressum and privacy pages render actual configured operator details.
- Public funnel requires an explicit contact request to the operator, but no blanket transfer to unnamed partners.
- Setter Ops can document a separate transfer consent for one concretely selected partner.
- Consent records now retain a text snapshot and context JSON.
- Public launch checker blocks promotion when core operator details are missing.

## Upgrade
```bash
cd ~/Downloads/solarlead-waldshut
unzip -o ~/Downloads/solarlead-v0.5.3-trust-consent-patch.zip -d ~/Downloads/solarlead-waldshut
cd backend
source .venv/bin/activate
PYTHONPATH=. python scripts/migrate_v053.py
cd ..
python3 deploy/configure-public-site.py
python3 deploy/check-public-launch.py
```

Restart backend and rebuild/restart the frontend afterwards.

## Important
The generated legal text is a technical template reflecting this application's current processing flow. It is not an individualized legal opinion. Have the final live version reviewed before broad public promotion.
