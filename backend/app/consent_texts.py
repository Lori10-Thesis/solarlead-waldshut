from .config import get_settings

PUBLIC_CONTACT_VERSION = "v3_public_contact"
PARTNER_TRANSFER_VERSION = "v3_partner_transfer"

def public_contact_text() -> str:
    s = get_settings()
    return (
        f"Ich bitte {s.operator_name} ausdrücklich, mich zu meiner konkreten Balkon-PV-Anfrage "
        "telefonisch und – falls angegeben – per E-Mail zu kontaktieren. "
        "Die Einwilligung kann jederzeit für die Zukunft widerrufen werden."
    )

def partner_transfer_text(partner_name: str) -> str:
    return (
        "Im Qualifizierungsgespräch wurde die ausdrückliche Zustimmung dokumentiert, "
        f"die Kontakt- und Projektdaten zur Bearbeitung der konkreten Anfrage an {partner_name} weiterzugeben."
    )
