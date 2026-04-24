import re
from typing import Optional, Dict, Any

# Country name → ISO code mapping (African + common countries)
COUNTRY_MAP = {
    "nigeria": "NG", "nigerian": "NG",
    "ghana": "GH", "ghanaian": "GH",
    "kenya": "KE", "kenyan": "KE",
    "ethiopia": "ET", "ethiopian": "ET",
    "tanzania": "TZ", "tanzanian": "TZ",
    "uganda": "UG", "ugandan": "UG",
    "south africa": "ZA", "south african": "ZA",
    "egypt": "EG", "egyptian": "EG",
    "cameroon": "CM", "cameroonian": "CM",
    "senegal": "SN", "senegalese": "SN",
    "angola": "AO", "angolan": "AO",
    "mozambique": "MZ", "mozambican": "MZ",
    "zambia": "ZM", "zambian": "ZM",
    "zimbabwe": "ZW", "zimbabwean": "ZW",
    "rwanda": "RW", "rwandan": "RW",
    "mali": "ML", "malian": "ML",
    "niger": "NE", "nigerien": "NE",
    "burkina faso": "BF",
    "guinea": "GN", "guinean": "GN",
    "benin": "BJ", "beninese": "BJ",
    "togo": "TG", "togolese": "TG",
    "somalia": "SO", "somali": "SO",
    "sudan": "SD", "sudanese": "SD",
    "chad": "TD", "chadian": "TD",
    "madagascar": "MG", "malagasy": "MG",
    "malawi": "MW", "malawian": "MW",
    "botswana": "BW", "batswana": "BW",
    "namibia": "NA", "namibian": "NA",
    "lesotho": "LS", "basotho": "LS",
    "eswatini": "SZ", "swazi": "SZ",
    "gabon": "GA", "gabonese": "GA",
    "congo": "CG", "congolese": "CG",
    "drc": "CD", "democratic republic of congo": "CD",
    "ivory coast": "CI", "cote d'ivoire": "CI",
    "sierra leone": "SL",
    "liberia": "LR", "liberian": "LR",
    "gambia": "GM", "gambian": "GM",
    "mauritius": "MU", "mauritian": "MU",
    "seychelles": "SC",
    "eritrea": "ER", "eritrean": "ER",
    "djibouti": "DJ",
    "comoros": "KM",
    "cape verde": "CV",
    "sao tome": "ST",
    "equatorial guinea": "GQ",
    "central african republic": "CF",
    "burundi": "BI", "burundian": "BI",
    "united states": "US", "usa": "US", "american": "US",
    "united kingdom": "GB", "uk": "GB", "british": "GB",
    "france": "FR", "french": "FR",
    "germany": "DE", "german": "DE",
    "india": "IN", "indian": "IN",
    "china": "CN", "chinese": "CN",
    "brazil": "BR", "brazilian": "BR",
    "canada": "CA", "canadian": "CA",
    "australia": "AU", "australian": "AU",
}

# Age group keywords
AGE_GROUP_KEYWORDS = {
    "child": "child", "children": "child", "kids": "child", "kid": "child",
    "teenager": "teenager", "teenagers": "teenager", "teen": "teenager", "teens": "teenager", "adolescent": "teenager",
    "adult": "adult", "adults": "adult",
    "senior": "senior", "seniors": "senior", "elderly": "senior", "old": "senior",
}

# Gender keywords
GENDER_KEYWORDS = {
    "male": "male", "man": "male", "men": "male", "boy": "male", "boys": "male", "males": "male",
    "female": "female", "woman": "female", "women": "female", "girl": "female", "girls": "female", "females": "female",
}


def parse_natural_language(q: str) -> Optional[Dict[str, Any]]:
    """
    Parse a natural language query into filter dict.
    Returns None if the query cannot be interpreted.
    """
    text = q.lower().strip()
    filters: Dict[str, Any] = {}
    matched_something = False

    # --- Gender ---
    for kw, val in GENDER_KEYWORDS.items():
        if re.search(rf"\b{kw}\b", text):
            filters["gender"] = val
            matched_something = True
            break

    # --- Age group ---
    for kw, val in AGE_GROUP_KEYWORDS.items():
        if re.search(rf"\b{kw}\b", text):
            filters["age_group"] = val
            matched_something = True
            break

    # --- "young" maps to ages 16-24 (not a stored age_group) ---
    if re.search(r"\byoung\b", text):
        filters["min_age"] = 16
        filters["max_age"] = 24
        matched_something = True

    # --- Age modifiers: "above X", "over X", "older than X" ---
    above_match = re.search(r"\b(?:above|over|older than|greater than|more than)\s+(\d+)\b", text)
    if above_match:
        filters["min_age"] = int(above_match.group(1))
        matched_something = True

    # --- "below X", "under X", "younger than X" ---
    below_match = re.search(r"\b(?:below|under|younger than|less than)\s+(\d+)\b", text)
    if below_match:
        filters["max_age"] = int(below_match.group(1))
        matched_something = True

    # --- "between X and Y" ---
    between_match = re.search(r"\bbetween\s+(\d+)\s+and\s+(\d+)\b", text)
    if between_match:
        filters["min_age"] = int(between_match.group(1))
        filters["max_age"] = int(between_match.group(2))
        matched_something = True

    # --- "aged X" or "age X" ---
    aged_match = re.search(r"\baged?\s+(\d+)\b", text)
    if aged_match:
        age_val = int(aged_match.group(1))
        filters["min_age"] = age_val
        filters["max_age"] = age_val
        matched_something = True

    # --- Country ---
    # Try multi-word countries first (longer matches take priority)
    sorted_countries = sorted(COUNTRY_MAP.keys(), key=len, reverse=True)
    for country in sorted_countries:
        # Use "from <country>", "in <country>", "<country adjective>", or just country name
        pattern = rf"\b{re.escape(country)}\b"
        if re.search(pattern, text):
            filters["country_id"] = COUNTRY_MAP[country]
            matched_something = True
            break

    # --- "from <country>" fallback with "from" keyword hint ---
    if "country_id" not in filters:
        from_match = re.search(r"\bfrom\s+([a-z\s]+?)(?:\s+(?:aged?|above|below|over|under|between|who|with|and|$)|\s*$)", text)
        if from_match:
            country_candidate = from_match.group(1).strip()
            if country_candidate in COUNTRY_MAP:
                filters["country_id"] = COUNTRY_MAP[country_candidate]
                matched_something = True

    if not matched_something:
        return None

    return filters
