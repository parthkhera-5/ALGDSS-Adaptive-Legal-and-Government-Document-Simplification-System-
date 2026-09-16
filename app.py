"""
Government Schemes RAG Chatbot — Flask app
--------------------------------------------
Consolidated, de-duplicated version of the logic built up across the Colab
notebook. Pipeline per query:

    1. Try local retrieval (FAISS + bge-small embeddings) over scheme chunks.
    2. If a scheme is already "pinned" (conversation topic from a previous
       turn) or a follow-up pronoun ("it"/"this scheme"/etc.) is resolved
       against that pinned topic, answer from that scheme's full profile.
    3. If local retrieval is weak/empty, fall back to a live web search
       (DuckDuckGo) restricted to gov.in / india.gov.in / wikipedia.org.
    4. "List schemes I'm eligible for ..." style queries get a dedicated
       multi-scheme evaluation path instead of the single-scheme path.
    5. Conversational memory is handled two ways:
         - mem0 (Groq LLM + HF embeddings + local Qdrant) stores every turn
           per user_id, for long-term recall.
         - a lightweight in-process `last_scheme` dict deterministically
           tracks "what scheme is this conversation currently about", used
           to resolve pronouns like "its eligibility?" -> the actual scheme.
    6. Multi-language support:
         - Incoming queries are script-detected (Devanagari/Bengali/etc.).
           A non-English query is translated to English BEFORE it enters
           the retrieval/pinning pipeline above (which is English-only:
           scheme keyword index, PRONOUN_PATTERN, FAISS embeddings, and
           the dataset itself are all English), then the finished answer
           is translated back into the detected (or explicitly selected)
           language.
         - Answer translation is now stricter about not leaving section
           labels ("Category", "Eligibility", ...) or half a sentence in
           English, to avoid mixed-language output when switching between
           languages that share little vocabulary (e.g. Hindi -> Urdu).
         - The SAME language support now also covers the Schemes browse
           tab, the "Find Schemes for Me" tab, and the Profile tab (see
           translate_strings / _row_to_summary / _row_to_detail /
           rank_schemes_for_profile / api_ui_strings below) — previously
           only the Discovery chat pipeline was translated, so switching
           the language dropdown had no visible effect anywhere else.
    7. Personalized "Find Schemes for Me":
         - A separate, deterministic rule-based eligibility engine (no LLM
           calls for the scoring itself, so ranking is instant) that scores
           every scheme in the dataset against a small structured profile
           (age, income, gender, social category, occupation, rural/urban,
           state) submitted from a form on the frontend. Scoring is done by
           pattern-matching the profile against each scheme's
           category/tags/details/eligibility text, and every point awarded
           is paired with a human-readable reason, which the frontend
           surfaces as "Why this matches you".
         - NEW: results are now grouped into three tiers ahead of raw score
           — (0) schemes that specifically name the user's own state,
           (1) Central/National or state-unspecified schemes, (2) schemes
           that specifically name a *different* state — via
           classify_scheme_tier(). Previously a same-state match only added
           +2 to the score, so a Central scheme that happened to match on
           age/income/occupation could easily outrank a genuine state
           scheme; a Rajasthan user could see Maharashtra-only schemes
           ranked above Rajasthan ones. Sorting by (tier, -score) instead
           of score alone fixes that, and the frontend renders each tier
           under its own heading.
         - This is otherwise independent of the chat/RAG pipeline above
           (different route, different function, no FAISS) so it can't
           regress or be regressed by chat behavior.

Run locally:
    1. pip install -r requirements.txt
    2. Put your dataset at data/updated_data.csv (see README for columns)
    3. Copy .env.example to .env and fill in GROQ_API_KEY
    4. python app.py
    5. Open http://localhost:5000
"""

import os
import re
import gc
import shutil
import threading
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd
import faiss
import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template

from sentence_transformers import SentenceTransformer
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from mem0 import Memory

load_dotenv()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY not set. Copy .env.example to .env and add your key."
    )

DATA_PATH = os.environ.get("DATA_PATH", os.path.join("data", "updated_data.csv"))
EMBED_MODEL_NAME = "BAAI/bge-small-en-v1.5"
MAIN_LLM_MODEL = "openai/gpt-oss-120b"
# NOTE: Groq deprecated llama-3.1-8b-instant (and llama-3.3-70b-versatile)
# in June 2026 and recommends openai/gpt-oss-20b as the replacement small/
# fast model. If Groq changes this again, check https://console.groq.com/docs/deprecations
# and update this one constant -- invoke_light() below will keep working as
# long as this is a valid model name.
LIGHT_LLM_MODEL = "openai/gpt-oss-20b"

MEM0_QDRANT_PATH = os.environ.get("MEM0_QDRANT_PATH", "./mem0_store/qdrant")
MEM0_HISTORY_DB = os.environ.get("MEM0_HISTORY_DB", "./mem0_store/mem0_history.db")

FALLBACK_MSG = (
    "I couldn't find a scheme matching that question. "
    "Could you check the spelling or rephrase it?"
)

STRUCTURE_INSTRUCTIONS = """
Format your answer as structured Markdown with exactly these sections (omit a section only if the context has no information for it):

## <Scheme Name>
**Category:** <one line>

### Overview
<2-3 sentence summary of what the scheme is and its objective>

### Eligibility
- <bullet per eligibility criterion>

### Benefits
- <bullet per benefit>

### How to Apply
1. <numbered step>

### Documents Required
- <bullet per document>

Use ONLY information present in the context below. Do not invent sections or details not present in the context.
"""

ACRONYM_MAP = {
    "mnrega": "mahatma gandhi national rural employment guarantee act mgnrega",
    "mgnrega": "mahatma gandhi national rural employment guarantee act mgnrega",
    "bbbp": "beti bachao beti padhao",
    "pmay": "pradhan mantri awaas yojana",
    "pmay-g": "pradhan mantri awaas yojana gramin",
}

# ---------------------------------------------------------------------------
# Personalized eligibility matching — keyword tables
# ---------------------------------------------------------------------------
# Used only by the rule-based "Find Schemes for Me" engine below (see
# score_scheme_for_profile / rank_schemes_for_profile). Kept separate from
# ACRONYM_MAP / SCHEME_KEYWORDS above, which power the chat pipeline's
# "is this query naming a scheme" detection -- a different problem.

# occupation select value (lowercased, matches the frontend <option value>)
# -> list of regex fragments that indicate a scheme targets that occupation.
OCCUPATION_KEYWORDS = {
    "farmer": [r"farmer", r"agricultur", r"kisan", r"cultivat", r"crop", r"irrigat"],
    "student": [r"\bstudent\b", r"scholarship", r"\beducation\b"],
    "unemployed": [r"unemployed", r"job seeker", r"\bemployment\b"],
    "daily wage laborer": [r"labour", r"laborer", r"\bworker\b", r"\bnrega\b", r"mgnrega", r"wage"],
    "self-employed / business": [r"entrepreneur", r"\bbusiness\b", r"self.?employed", r"startup", r"\bmudra\b", r"msme"],
    "government employee": [r"government employee", r"public servant", r"govt\.?\s*employee"],
    "salaried / private employee": [r"\bemployee\b", r"salaried", r"private sector"],
    "senior citizen / retired": [r"senior citizen", r"\belderly\b", r"\bpension\b", r"old age", r"retired"],
    "person with disability": [r"disab", r"divyang", r"handicap"],
    "artisan / craftsperson": [r"artisan", r"craftsman", r"weaver", r"handicraft", r"handloom"],
    "other": [],
}

# social-category select value (lowercased) -> regex that indicates a
# scheme references that reservation/social category.
SOCIAL_CATEGORY_PATTERNS = {
    "sc": r"\bsc\b|scheduled caste",
    "st": r"\bst\b|scheduled tribe",
    "obc": r"\bobc\b|other backward class",
    "ews": r"\bews\b|economically weaker",
    "minority": r"\bminority\b|minorit",
}

FEMALE_PATTERN = re.compile(r"\b(women|woman|girl|female|mahila|beti)\b", re.IGNORECASE)
RURAL_PATTERN = re.compile(r"\b(rural|village|gramin)\b", re.IGNORECASE)
URBAN_PATTERN = re.compile(r"\b(urban|city|municipal)\b", re.IGNORECASE)

_AGE_RANGE_PATTERN = re.compile(r"(\d{1,2})\s*(?:-|to|–)\s*(\d{1,2})\s*years", re.IGNORECASE)
_AGE_MIN_PATTERN = re.compile(r"(?:above|over|minimum(?: age of)?|at least)\s*(\d{1,2})\s*years", re.IGNORECASE)
_AGE_MAX_PATTERN = re.compile(r"(?:below|under|maximum(?: age of)?|up ?to|not exceeding)\s*(\d{1,2})\s*years", re.IGNORECASE)

_INCOME_CAP_PATTERN = re.compile(
    r"(?:income|salary|earning)[^.]{0,40}?"
    r"(?:below|under|up ?to|less than|not (?:exceed\w*|more than)|maximum(?: of)?)\s*"
    r"(?:rs\.?|₹|inr)?\s*([\d,]+(?:\.\d+)?)\s*(lakh|lakhs|crore|crores)?",
    re.IGNORECASE,
)


def extract_age_ranges(text):
    """Returns a list of (min_age_or_None, max_age_or_None) tuples found in
    the given (already-lowercased) eligibility text."""
    ranges = []
    for m in _AGE_RANGE_PATTERN.finditer(text):
        lo, hi = int(m.group(1)), int(m.group(2))
        if lo < hi:
            ranges.append((lo, hi))
    for m in _AGE_MIN_PATTERN.finditer(text):
        ranges.append((int(m.group(1)), None))
    for m in _AGE_MAX_PATTERN.finditer(text):
        ranges.append((None, int(m.group(1))))
    return ranges


def extract_income_cap(text):
    """Returns the income ceiling (in rupees) mentioned near the word
    'income'/'salary'/'earning' in the given text, handling lakh/crore
    units, or None if no such ceiling is stated."""
    m = _INCOME_CAP_PATTERN.search(text)
    if not m:
        return None
    amount = float(m.group(1).replace(",", ""))
    unit = (m.group(2) or "").lower()
    if "lakh" in unit:
        amount *= 100_000
    elif "crore" in unit:
        amount *= 10_000_000
    return amount


PRONOUN_PATTERN = re.compile(r"\b(its|that scheme|this scheme|it|the scheme)\b", re.IGNORECASE)

# Catches queries that explicitly introduce/name a topic ("what is X",
# "tell me about X", "explain X", "define X") with no pronoun. Used to
# prevent such queries from staying wrongly pinned to a previous scheme
# just because they don't match any *local* scheme keyword (e.g. the new
# topic isn't in the local dataset at all, so mentions_scheme_keyword()
# can't catch it, and the semantic FAISS check comes back empty too).
NEW_TOPIC_QUERY_PATTERN = re.compile(
    r"^\s*(what is|what'?s|tell me about|explain|define)\b", re.IGNORECASE
)

FOCUS_KEYWORDS = {
    "eligibility": ["eligibility", "eligible", "who can apply", "can i apply",
                    "criteria", "qualify", "can i join", "am i eligible", "do i qualify"],
    "benefits": ["benefit", "benefits", "advantage"],
    "application": ["how to apply", "application process", "document", "documents required", "how do i apply"],
}

_FOCUS_CLASSIFIER_PROMPT = """Classify what part of a government scheme the user is asking about.
Reply with EXACTLY ONE WORD from: eligibility, benefits, application, overview.
- eligibility: whether the user personally qualifies (age/income/category/criteria, "can I join/apply")
- benefits: what the user receives (money, perks, entitlements)
- application: how to apply, process steps, documents needed
- overview: general "what is this scheme" questions, or anything not clearly one of the above

Question: {query}
Answer with one word only."""

LIST_QUERY_PATTERN = re.compile(
    r"\b(list all|all schemes|which schemes|what schemes|show me schemes|"
    r"schemes (?:can|could) i|eligible for (?:which|what)|which (?:all )?schemes)\b",
    re.IGNORECASE,
)

LIST_EVAL_PATTERN = re.compile(
    r"SCHEME:\s*(?P<name>.+?)\s*\n"
    r"STATUS:\s*(?P<status>FIT|NO_FIT)\s*\n"
    r"REASON:\s*(?P<reason>.+?)\s*\n"
    r"ELIGIBILITY:\s*(?P<eligibility>.*)",
    re.IGNORECASE,
)

NO_MATCH_PATTERN = re.compile(
    r"(does not contain|doesn'?t contain|does not include|no (?:information|data|details) (?:about|on)|"
    r"not (?:available|found|mentioned) in (?:the )?(?:given|provided|local)|"
    r"could not find|couldn'?t find|is not (?:present|available) in the (?:context|data)|"
    r"context (?:only |)describes|context does not|cannot (?:supply|provide))",
    re.IGNORECASE,
)

MATCH_STATUS_INSTRUCTIONS = """
Before your answer, output exactly one status line, then a blank line, then your answer:
STATUS: MATCH
or
STATUS: NO_MATCH

The context below is the profile of the scheme currently being discussed with the user — treat
it as the subject of this question even if the question doesn't repeat its name. Use
STATUS: NO_MATCH ONLY if this scheme's profile genuinely does not contain information relevant to
what's being asked (e.g. the question is clearly about a different scheme/topic). If it's a
normal follow-up (eligibility, benefits, documents, how to apply, etc.) and the context covers it,
use STATUS: MATCH.
"""

SCHEME_NAME_PATTERN = re.compile(r"^SCHEME_NAME:\s*(.+)$", re.IGNORECASE | re.MULTILINE)

# ---------------------------------------------------------------------------
# Data + index setup (runs once at startup)
# ---------------------------------------------------------------------------
print("Loading dataset...")
df = pd.read_csv(DATA_PATH)
df.ffill(axis=0, inplace=True)
df = df.drop(columns=["Unnamed: 9"], errors="ignore")
df = df.reset_index(drop=True)


def build_chunks(df):
    chunks = []
    for i, row in df.iterrows():
        base_meta = {"row_idx": i, "scheme_name": row["scheme_name"], "slug": row["slug"]}

        chunks.append({
            "text": f"Scheme: {row['scheme_name']}. Category: {row['schemeCategory']}. "
                    f"Tags: {row['tags']}. Details: {row['details']}",
            "type": "overview", **base_meta
        })
        chunks.append({
            "text": f"Scheme: {row['scheme_name']}. Eligibility: {row['eligibility']}",
            "type": "eligibility", **base_meta
        })
        chunks.append({
            "text": f"Scheme: {row['scheme_name']}. Benefits: {row['benefits']}",
            "type": "benefits", **base_meta
        })
        chunks.append({
            "text": f"Scheme: {row['scheme_name']}. How to apply: {row['application']}. "
                    f"Documents required: {row['documents']}",
            "type": "application", **base_meta
        })
    return chunks


chunks = build_chunks(df)
chunk_texts = [c["text"] for c in chunks]
print(f"{len(df)} schemes -> {len(chunks)} chunks")

print("Loading embedding model (first run downloads it)...")
embedder = SentenceTransformer(EMBED_MODEL_NAME)

CACHE_DIR = os.environ.get("EMBED_CACHE_DIR", "./cache")
os.makedirs(CACHE_DIR, exist_ok=True)
INDEX_CACHE_PATH = os.path.join(CACHE_DIR, "faiss_index.bin")
EMBED_CACHE_PATH = os.path.join(CACHE_DIR, "embeddings.npy")
CACHE_META_PATH = os.path.join(CACHE_DIR, "cache_meta.txt")

# Cache is invalidated if the number of chunks changes (i.e. the CSV changed).
cache_valid = (
    os.path.exists(INDEX_CACHE_PATH)
    and os.path.exists(EMBED_CACHE_PATH)
    and os.path.exists(CACHE_META_PATH)
    and open(CACHE_META_PATH).read().strip() == str(len(chunk_texts))
)

if cache_valid:
    print("Loading cached embeddings + FAISS index (skipping re-encoding)...")
    embeddings = np.load(EMBED_CACHE_PATH)
    index = faiss.read_index(INDEX_CACHE_PATH)
else:
    print("No valid cache found — encoding all chunks (this only happens once)...")
    embeddings = embedder.encode(chunk_texts, batch_size=64, show_progress_bar=True, normalize_embeddings=True)
    embeddings = np.array(embeddings).astype("float32")

    index = faiss.IndexFlatIP(embeddings.shape[1])  # inner product on normalized vecs = cosine sim
    index.add(embeddings)

    np.save(EMBED_CACHE_PATH, embeddings)
    faiss.write_index(index, INDEX_CACHE_PATH)
    with open(CACHE_META_PATH, "w") as f:
        f.write(str(len(chunk_texts)))

print("FAISS index size:", index.ntotal)


def get_all_chunks_for_scheme(slug):
    return [c for c in chunks if c["slug"] == slug]


# ---------------------------------------------------------------------------
# Schemes browse/search API helpers
# --------------------------------------------------------------------------
# Backs the "Schemes" tab (browse/search/filter/save) and the "Profile" tab
# (looking up saved scheme names) in the frontend. This is plain dataset
# access -- no retrieval, no LLM calls for the data itself -- separate from
# the chat_rag pipeline above which powers the Discovery tab. Translation
# (see translate_strings below) is layered on top of this plain access, not
# mixed into it.
# ---------------------------------------------------------------------------

# Some datasets may not have a "level" (Central/State) or an official "link"
# column at all -- detect whichever of these common names is present so the
# API degrades gracefully (returns null) instead of raising a KeyError.
_LEVEL_COL = next(
    (c for c in ["level", "Level", "scheme_level", "govt_level", "government_level"] if c in df.columns),
    None,
)
_LINK_COL = next(
    (c for c in ["link", "url", "official_link", "apply_link", "website", "scheme_link"] if c in df.columns),
    None,
)

# slug -> row, built once at startup for O(1) detail lookups
SLUG_TO_ROW = {str(row["slug"]): row for _, row in df.iterrows()}


def _make_short_description(details, max_len=140):
    """Trim the long 'details' field down to a card-sized teaser, cutting on
    a word boundary rather than mid-word."""
    text = str(details or "").strip()
    if len(text) <= max_len:
        return text
    cut = text[:max_len].rsplit(" ", 1)[0]
    return cut.rstrip(",.;:- ") + "…"


def _row_to_summary(row, lang="en"):
    category = str(row.get("schemeCategory", "") or "").strip()
    level_val = row.get(_LEVEL_COL) if _LEVEL_COL else None
    name = str(row["scheme_name"])
    level_str = str(level_val).strip() if _LEVEL_COL and pd.notna(level_val) else ""
    short_desc = _make_short_description(row.get("details", ""))

    if lang and lang != "en":
        translated = translate_strings([name, category, short_desc, level_str], lang)
        name, category, short_desc = translated[0], translated[1], translated[2]
        level_str = translated[3]

    return {
        "slug": str(row["slug"]),
        "name": name,
        "category": category,
        "level": level_str or None,
        "short_description": short_desc,
        "tags": str(row.get("tags", "") or ""),
    }


def _row_to_detail(row, lang="en"):
    """Full profile for the scheme-details modal -- same underlying fields
    used to build the RAG chunks, so this always matches what the chatbot
    itself would cite (before translation is layered on)."""
    link_val = row.get(_LINK_COL) if _LINK_COL else None
    detail = _row_to_summary(row, lang=lang)

    details_text = str(row.get("details", "") or "")
    eligibility_text = str(row.get("eligibility", "") or "")
    benefits_text = str(row.get("benefits", "") or "")
    application_text = str(row.get("application", "") or "")
    documents_text = str(row.get("documents", "") or "")

    if lang and lang != "en":
        translated = translate_strings(
            [details_text, eligibility_text, benefits_text, application_text, documents_text],
            lang,
        )
        details_text, eligibility_text, benefits_text, application_text, documents_text = translated

    detail.update({
        "details": details_text,
        "eligibility": eligibility_text,
        "benefits": benefits_text,
        "application": application_text,
        "documents": documents_text,
        "link": str(link_val).strip() if _LINK_COL and pd.notna(link_val) else None,
    })
    return detail


# ---------------------------------------------------------------------------
# State-priority tiering ("For You" / Find Schemes for Me)
# ---------------------------------------------------------------------------
# Full list of Indian states/UTs. Used both to detect whether a scheme names
# the user's own state (tier 0), and to detect whether it instead names a
# *different* specific state (tier 2) so that scheme doesn't get grouped in
# with genuinely nationwide/Central schemes (tier 1).
ALL_INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa",
    "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala",
    "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland",
    "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
    "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Andaman and Nicobar Islands", "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu", "Delhi", "Jammu and Kashmir",
    "Ladakh", "Lakshadweep", "Puducherry",
]
ALL_INDIAN_STATES_LOWER = [s.lower() for s in ALL_INDIAN_STATES]


def classify_scheme_tier(row, combined_text, user_state):
    """Returns a priority tier for ranking a scheme against a user's stated
    state, LOWEST tier sorts first:
        0 = scheme text specifically names the user's own state
        1 = Central/National scheme, OR the user gave no state, OR the
            scheme's text doesn't name any specific state at all
        2 = scheme text specifically names a DIFFERENT state than the user's

    This exists so a Rajasthan user sees Rajasthan-specific schemes first,
    Central/nationwide schemes next, and other-state-only schemes last --
    instead of everything being interleaved purely by raw eligibility score
    (see rank_schemes_for_profile below, which sorts by (tier, -score))."""
    own = (user_state or "").strip().lower()
    if not own:
        return 1  # no state given -> no tiering possible, treat as neutral

    if own in combined_text:
        return 0

    level_val = str(row.get(_LEVEL_COL) or "").strip().lower() if _LEVEL_COL else ""
    if "central" in level_val or "national" in level_val:
        return 1

    for other in ALL_INDIAN_STATES_LOWER:
        if other != own and other in combined_text:
            return 2

    return 1  # no specific state mentioned -> treat as general/nationwide


def _combined_scheme_text(row):
    """All the free-text fields worth pattern-matching against, lower-cased
    and concatenated once per scheme."""
    return " ".join([
        str(row.get("schemeCategory", "") or ""),
        str(row.get("tags", "") or ""),
        str(row.get("details", "") or ""),
        str(row.get("eligibility", "") or ""),
    ]).lower()


# slug -> combined lower-cased text, built once at startup so scoring a
# profile against the whole dataset doesn't re-stringify every row each time.
SLUG_TO_TEXT = {str(row["slug"]): _combined_scheme_text(row) for _, row in df.iterrows()}


def score_scheme_for_profile(row, combined_text, profile):
    """Returns (score, reasons) for how well one scheme fits one profile.
    `reasons` is a list of short, human-readable sentences explaining every
    point that was awarded -- this list is exactly what the frontend shows
    as "Why this matches you", so nothing is added to the score without an
    accompanying explanation.

    NOTE: state match is intentionally still scored here too (not just used
    for tiering) so that among several same-tier schemes, an explicit state
    mention still nudges ranking and still gets its own "why" reason."""
    eligibility_text = str(row.get("eligibility", "") or "").lower()
    score = 0.0
    reasons = []

    # --- Age ---
    age = profile.get("age")
    if age is not None:
        age_ranges = extract_age_ranges(eligibility_text)
        for lo, hi in age_ranges:
            if (lo is None or age >= lo) and (hi is None or age <= hi):
                score += 3
                if lo is not None and hi is not None:
                    reasons.append(f"Your age ({age}) falls within this scheme's eligible range ({lo}–{hi} years).")
                elif lo is not None:
                    reasons.append(f"Your age ({age}) meets this scheme's minimum age requirement ({lo}+ years).")
                else:
                    reasons.append(f"Your age ({age}) is within this scheme's maximum age limit ({hi} years).")
                break

    # --- Income ---
    income = profile.get("income")
    if income is not None:
        income_cap = extract_income_cap(eligibility_text)
        if income_cap is not None:
            if income <= income_cap:
                score += 3
                reasons.append(
                    f"Your annual income (₹{income:,.0f}) is within this scheme's stated limit (₹{income_cap:,.0f})."
                )
            else:
                score -= 2  # stated cap exceeded — likely not eligible

    # --- Gender ---
    gender = (profile.get("gender") or "").lower()
    if gender == "female" and FEMALE_PATTERN.search(combined_text):
        score += 2
        reasons.append("This scheme is specifically for women/girls.")

    # --- Social category (SC/ST/OBC/EWS/Minority) ---
    social_category = (profile.get("category") or "").lower()
    if social_category and social_category not in ("general", "other"):
        pattern = SOCIAL_CATEGORY_PATTERNS.get(social_category)
        if pattern and re.search(pattern, combined_text, re.IGNORECASE):
            score += 2
            reasons.append(f"This scheme references eligibility for your category ({profile.get('category')}).")

    # --- Occupation ---
    occupation = (profile.get("occupation") or "").lower()
    if occupation and occupation in OCCUPATION_KEYWORDS:
        keywords = OCCUPATION_KEYWORDS[occupation]
        if keywords and any(re.search(kw, combined_text, re.IGNORECASE) for kw in keywords):
            score += 2.5
            reasons.append(f"This scheme targets people in your occupation ({profile.get('occupation')}).")

    # --- Rural / Urban ---
    area = (profile.get("area") or "").lower()
    if area == "rural" and RURAL_PATTERN.search(combined_text):
        score += 1
        reasons.append("This scheme focuses on rural areas.")
    elif area == "urban" and URBAN_PATTERN.search(combined_text):
        score += 1
        reasons.append("This scheme focuses on urban/city areas.")

    # --- State ---
    state = (profile.get("state") or "").strip()
    if state and state.lower() in combined_text:
        score += 2
        reasons.append(f"This scheme specifically mentions {state}.")

    return score, reasons


def rank_schemes_for_profile(profile, top_n=10, lang="en"):
    """Scores every scheme in the dataset against `profile` and returns the
    top_n as a list of dicts ready for jsonify: slug, name, category,
    short_description, score, reasons ("why this matches you"), plus
    state_scope (0/1/2) and state_scope_label for grouping in the UI.

    Ranking is now two-level: primarily by state_scope tier (own-state
    schemes first, then Central/general, then other-state-only schemes
    last), and only within a tier by raw eligibility score. This is what
    makes a Rajasthan user see Rajasthan-specific schemes on top instead of
    them being outranked by an unrelated Central scheme that happens to
    score higher on age/income/occupation alone.

    If nothing scores above zero (profile gave too few/too vague signals,
    or the dataset's eligibility text just doesn't mention anything
    matchable), falls back to returning the top_n schemes anyway (still
    tier-sorted) so the user isn't shown a blank page, each labeled as a
    general/open scheme rather than a confident match.
    """
    user_state = (profile.get("state") or "").strip()

    scored = []
    for _, row in df.iterrows():
        slug = str(row["slug"])
        combined_text = SLUG_TO_TEXT.get(slug, "")
        score, reasons = score_scheme_for_profile(row, combined_text, profile)
        tier = classify_scheme_tier(row, combined_text, user_state)
        scored.append((tier, score, row, reasons))

    # Sort by tier ascending (0 = own state first), then score descending
    # within each tier.
    scored.sort(key=lambda entry: (entry[0], -entry[1]))

    positive = [entry for entry in scored if entry[1] > 0]
    top = positive[:top_n] if positive else scored[:top_n]

    tier_labels_en = {
        0: f"{user_state} (Your State)" if user_state else "Your State",
        1: "Central / National",
        2: "Other States",
    }

    results = []
    for tier, score, row, reasons in top:
        if not reasons:
            reasons = [
                "This scheme doesn't state restrictive eligibility criteria we could "
                "match against your profile — it may be open to a wide range of applicants. "
                "Check the full eligibility details before applying."
            ]
        results.append({
            "slug": str(row["slug"]),
            "name": str(row["scheme_name"]),
            "category": str(row.get("schemeCategory", "") or ""),
            "short_description": _make_short_description(row.get("details", "")),
            "score": round(score, 1),
            "reasons": reasons,
            "state_scope": tier,
            "state_scope_label": tier_labels_en[tier],
        })

    if lang and lang != "en":
        # Batch-translate every translatable string across all results in
        # one pass: name, category, short_description, state_scope_label,
        # then all reasons flattened, then unflatten back into place.
        names = [r["name"] for r in results]
        categories = [r["category"] for r in results]
        short_descs = [r["short_description"] for r in results]
        scope_labels = list({r["state_scope_label"] for r in results})

        t_names = translate_strings(names, lang)
        t_categories = translate_strings(categories, lang)
        t_short_descs = translate_strings(short_descs, lang)
        t_scope_labels = dict(zip(scope_labels, translate_strings(scope_labels, lang)))

        reason_counts = [len(r["reasons"]) for r in results]
        flat_reasons = [reason for r in results for reason in r["reasons"]]
        t_flat_reasons = translate_strings(flat_reasons, lang)

        cursor = 0
        for i, r in enumerate(results):
            r["name"] = t_names[i]
            r["category"] = t_categories[i]
            r["short_description"] = t_short_descs[i]
            r["state_scope_label"] = t_scope_labels.get(r["state_scope_label"], r["state_scope_label"])
            n = reason_counts[i]
            r["reasons"] = t_flat_reasons[cursor:cursor + n]
            cursor += n

    return results


# ---------------------------------------------------------------------------
# Keyword index used to detect "does this query name a (different) scheme"
# ---------------------------------------------------------------------------
_SCHEME_NAME_STOPWORDS = {
    "pradhan", "mantri", "yojana", "yojna", "scheme", "abhiyan", "mission",
    "programme", "program", "national", "india", "indian", "the", "of",
    "and", "for", "act", "central", "state",
}

def _build_scheme_keyword_index(df):
    keywords = set()
    for name in df["scheme_name"]:
        for w in re.findall(r"[a-zA-Z]+", str(name).lower()):
            if len(w) > 3 and w not in _SCHEME_NAME_STOPWORDS:
                keywords.add(w)
    keywords.update(ACRONYM_MAP.keys())
    return keywords

SCHEME_KEYWORDS = _build_scheme_keyword_index(df)

def mentions_scheme_keyword(query):
    q = query.lower()

    # 1. Full scheme name appears verbatim
    for name in df["scheme_name"]:
        name = str(name).lower()
        if name and name in q:
            return True

    # 2. Known acronym appears as a whole word
    for acronym in ACRONYM_MAP:
        if re.search(rf"\b{re.escape(acronym)}\b", q):
            return True

    # 3. At least two distinctive scheme-name words appear together — catches
    # abbreviated/partial references ("PM Jeevan Jyoti Bima Yojana" instead
    # of the dataset's full "Pradhan Mantri Jeevan Jyoti Bima Yojana").
    # Requiring 2+ words (not just 1) avoids a single common word in an
    # ordinary follow-up falsely triggering a "new topic" verdict.
    words = set(re.findall(r"[a-zA-Z]+", q))
    if len(words & SCHEME_KEYWORDS) >= 2:
        return True

    return False

def retrieve(query, k=8, min_score=0.30, per_scheme_limit=1, expand_k=20):
    q_emb = embedder.encode(
        [f"Represent this sentence for searching relevant passages: {query}"],
        normalize_embeddings=True,
    ).astype("float32")
    scores, idxs = index.search(q_emb, expand_k)  # cast a wider net first
    seen_schemes = {}
    results = []
    for score, idx in zip(scores[0], idxs[0]):
        if score < min_score:
            continue
        c = chunks[idx]
        cnt = seen_schemes.get(c["slug"], 0)
        if cnt >= per_scheme_limit:
            continue  # avoid one scheme hogging multiple slots
        seen_schemes[c["slug"]] = cnt + 1
        results.append({**c, "score": float(score)})
        if len(results) >= k:
            break
    return results


def expand_acronyms(text):
    words = text.lower().split()
    expanded = []
    for w in words:
        clean = re.sub(r"[^a-z]", "", w)
        expanded.append(ACRONYM_MAP.get(clean, w))
    return " ".join(expanded)


# ---------------------------------------------------------------------------
# LLMs
# ---------------------------------------------------------------------------
llm = ChatGroq(
    model=MAIN_LLM_MODEL,
    api_key=GROQ_API_KEY,
    temperature=0,
    # RELIABILITY FIX: without an explicit timeout, a stalled/slow response
    # from Groq (rate limiting, network hiccup, etc.) can leave .invoke()
    # hanging indefinitely -- the dev server is single-threaded
    # (threaded=False, required by mem0's SQLite history store), so one
    # stuck request freezes the ENTIRE app until you kill and restart it.
    # timeout=60 gives the main model (which can be asked to write a full
    # multi-scheme evaluation) reasonable room, while still failing loudly
    # instead of hanging forever. max_retries lets the Groq client itself
    # retry a couple of times on transient network errors before giving up.
    timeout=60,
    max_retries=2,
)

# PERFORMANCE / COST FIX
# -----------------------
# This used to be `light_llm = llm`, i.e. every "small" auxiliary task
# (query translation, answer translation, pronoun rewriting, focus
# classification, UI-string translation) was routed through the big
# 120b-parameter MAIN_LLM_MODEL. That is the main reason non-English turns
# were slow and token-hungry: a single Hindi question could trigger 3-5
# separate calls to the large model in sequence
# (translate query -> maybe rewrite pronoun -> maybe classify focus ->
# generate answer -> translate answer) instead of just the one call that
# actually needs the big model (answer generation).
#
# Now only answer generation uses MAIN_LLM_MODEL. Every auxiliary task goes
# through LIGHT_LLM_MODEL (a small, fast Groq model) via invoke_light()
# below, which also transparently falls back to the big model if the light
# model errors out or gets renamed/retired on your Groq account — so a bad
# light-model name degrades gracefully instead of breaking every
# non-English request.
try:
    light_llm = ChatGroq(
        model=LIGHT_LLM_MODEL,
        api_key=GROQ_API_KEY,
        temperature=0,
        # openai/gpt-oss-* models are REASONING models: before writing the
        # final answer they first spend tokens on an internal "thinking"
        # pass. Two settings matter a lot for a small/fast helper model:
        #   - max_tokens: if this is too low (or left at whatever default
        #     langchain-groq applies), the model can burn its entire budget
        #     on the hidden reasoning pass and have nothing left for the
        #     actual output -- you get back a *successful* API call with an
        #     EMPTY .content, which is exactly what produced the blank
        #     Hindi chat bubbles. Set it generously high so translation of
        #     a full scheme write-up always has room to finish.
        #   - reasoning_effort: "low" keeps that hidden thinking pass short
        #     for these small tasks (translation/classification/rewriting
        #     don't need deep reasoning), which both speeds them up and
        #     leaves more of the token budget for the real output.
        max_tokens=4096,
        reasoning_effort="low",
        # RELIABILITY FIX: same reasoning as the main `llm` above, but a
        # shorter timeout -- these are meant to be small/fast helper calls,
        # so if one is taking longer than 20s something's wrong and
        # invoke_light() should move on to its retry/fallback rather than
        # sit there indefinitely.
        timeout=20,
        max_retries=2,
    )
except Exception as e:
    print(f"Could not initialize LIGHT_LLM_MODEL ({LIGHT_LLM_MODEL}): {e}. Falling back to MAIN_LLM_MODEL for light tasks.")
    light_llm = llm


def invoke_light(messages, retries=1):
    """Wrapper used for every small/auxiliary LLM call (translation,
    classification, rewriting). Tries the light model first; if it fails
    OR comes back with empty/blank content (reasoning models can return a
    200-OK response with nothing in .content if their reasoning pass ate
    the whole token budget -- that's not an exception, so it has to be
    checked for explicitly) it retries once, then falls back to the main
    model rather than silently returning blank text to the user."""
    last_err = None
    for _ in range(retries + 1):
        try:
            resp = light_llm.invoke(messages)
            if resp.content and resp.content.strip():
                return resp
            last_err = "empty content (reasoning model likely ran out of output tokens)"
        except Exception as e:
            last_err = e
    print(f"light_llm invoke failed after retries ({last_err}); falling back to MAIN_LLM_MODEL.")
    return llm.invoke(messages)

# ---------------------------------------------------------------------------
# Multi-language support (voice input/output + answer translation +
# incoming-query language detection & translation + Schemes/For You/Profile
# translation)
# ---------------------------------------------------------------------------
# This section is intentionally self-contained: the query-translation helpers
# below run BEFORE chat_rag_with_memory() and the answer-translation helper
# runs AFTER it, as separate pre/post passes. Neither touches chat_rag(),
# chat_rag_with_memory(), resolve_query_with_memory(), or any retrieval/
# pinning logic above -- that pipeline still always operates in English.
#
# translate_strings() (below) is the generic building block that the
# Schemes/For You/Profile tabs now also use, via _row_to_summary,
# _row_to_detail, rank_schemes_for_profile, and api_ui_strings — it is
# purely a translation utility and has no involvement in retrieval/pinning
# either.
#
# `code` matches the value sent by the <select> in index.html.
# `speech_locale` is the BCP-47 tag used by the browser's Web Speech API
# (SpeechRecognition for mic input, speechSynthesis for read-aloud output).
SUPPORTED_LANGUAGES = {
    "en": {"name": "English", "speech_locale": "en-IN"},
    "hi": {"name": "Hindi", "speech_locale": "hi-IN"},
    "bn": {"name": "Bengali", "speech_locale": "bn-IN"},
    "ta": {"name": "Tamil", "speech_locale": "ta-IN"},
    "te": {"name": "Telugu", "speech_locale": "te-IN"},
    "mr": {"name": "Marathi", "speech_locale": "mr-IN"},
    "gu": {"name": "Gujarati", "speech_locale": "gu-IN"},
    "kn": {"name": "Kannada", "speech_locale": "kn-IN"},
    "ml": {"name": "Malayalam", "speech_locale": "ml-IN"},
    "pa": {"name": "Punjabi", "speech_locale": "pa-IN"},
    "ur": {"name": "Urdu", "speech_locale": "ur-IN"},
}

# Unicode script ranges used to detect which language a typed/spoken query
# is in, WITHOUT an LLM call (cheap, deterministic, works even for very
# short queries). Devanagari is shared by Hindi and Marathi -- we label it
# "hi" since Hindi is far more common in this app's context; nothing below
# depends on distinguishing the two.
_SCRIPT_LANG_RANGES = {
    "ur": [(0x0600, 0x06FF), (0x0750, 0x077F)],  # Arabic block, used for Urdu
    "hi": [(0x0900, 0x097F)],                     # Devanagari (Hindi/Marathi)
    "bn": [(0x0980, 0x09FF)],                     # Bengali
    "pa": [(0x0A00, 0x0A7F)],                     # Gurmukhi (Punjabi)
    "gu": [(0x0A80, 0x0AFF)],                     # Gujarati
    "ta": [(0x0B80, 0x0BFF)],                     # Tamil
    "te": [(0x0C00, 0x0C7F)],                     # Telugu
    "kn": [(0x0C80, 0x0CFF)],                     # Kannada
    "ml": [(0x0D00, 0x0D7F)],                     # Malayalam
}


def detect_query_script_language(text):
    """Best-effort language guess from the Unicode script of the characters
    in `text`. Returns a SUPPORTED_LANGUAGES key, or None if the text looks
    like plain Latin script (i.e. probably already English)."""
    counts = {}
    for ch in text:
        cp = ord(ch)
        for lang, ranges in _SCRIPT_LANG_RANGES.items():
            if any(lo <= cp <= hi for lo, hi in ranges):
                counts[lang] = counts.get(lang, 0) + 1
                break
    if not counts:
        return None
    return max(counts, key=counts.get)


# Cache of query text -> its English translation. Repeated/common questions
# ("eligibility?", "documents required?", etc.) are now free after the
# first time any user asks them in a given language.
_query_translation_cache = {}


def translate_query_to_english(query):
    """Translate an incoming non-English query into English before it enters
    the retrieval/pinning pipeline (mentions_scheme_keyword, PRONOUN_PATTERN,
    FAISS over the English dataset, LIST_QUERY_PATTERN, etc. -- none of which
    understand any script but Latin). Without this step, a query like
    "पीएम विश्वकर्मा योजना क्या है?" never matches anything locally and falls
    straight through to a weak/failed web fallback."""
    cached = _query_translation_cache.get(query)
    if cached is not None:
        return cached

    messages = [
        SystemMessage(content=(
            "Translate the following question about an Indian government scheme into "
            "English. Keep scheme names recognizable — transliterate proper nouns rather "
            "than inventing an English name for them. "
            "Return ONLY the English translation, nothing else, no preamble."
        )),
        HumanMessage(content=query)
    ]
    try:
        translated = invoke_light(messages).content.strip()
        result = translated if translated else query
    except Exception as e:
        print(f"translate_query_to_english failed: {e}")
        result = query

    _query_translation_cache[query] = result
    return result


def translate_answer(answer_text, target_lang_code):
    """Translate an already-generated answer into the requested language.

    Runs strictly AFTER chat_rag_with_memory() has produced its answer, as a
    separate formatting pass -- the retrieval/pinning/web-fallback pipeline
    above always runs in English, unchanged, regardless of the UI language.

    Stricter than a plain "translate this" prompt: earlier this allowed the
    model to leave section labels (Category/Eligibility/...) or a scheme
    name in English "if there's no natural equivalent," which produced
    visibly mixed-language output -- especially noticeable switching between
    languages that share little vocabulary (e.g. Hindi -> Urdu), where half
    a line would come out translated and the rest wouldn't.
    """
    lang = SUPPORTED_LANGUAGES.get(target_lang_code)
    if not lang or target_lang_code == "en":
        return answer_text

    messages = [
        SystemMessage(content=(
            f"Translate the following Markdown text FULLY into {lang['name']}. "
            "Translate EVERYTHING, including section labels and headings such as "
            "'Category', 'Overview', 'Scheme', 'Eligibility', 'Benefits', "
            "'How to Apply', 'Documents Required' -- do not leave these as English words. "
            "Never mix two languages within a single sentence, and never leave part of a "
            "sentence untranslated. "
            "For scheme names: use the scheme's well-known name in the target language if "
            "one exists (most Indian government schemes have an established Hindi/regional "
            "name), transliterating into the target script rather than leaving it in Latin "
            "script. Only keep a genuinely untranslatable acronym in Latin script. "
            "Preserve ALL Markdown structure exactly (headings like ##/###, bold **text**, "
            "bullet points, numbered lists, blank lines) -- translate only the natural-language "
            "content inside it. "
            "Return ONLY the translated Markdown, nothing else -- no preamble, no explanation."
        )),
        HumanMessage(content=answer_text)
    ]
    try:
        translated = invoke_light(messages).content.strip()
        # invoke_light() already retries+falls back internally on empty
        # content, but guard here too: NEVER let an empty string reach the
        # user as their "answer" -- show the original (English) answer
        # instead of a blank chat bubble if translation still came back empty.
        return translated if translated else answer_text
    except Exception as e:
        print(f"translate_answer failed: {e}")
        return answer_text


# In-process cache of (lang, source_string) -> translated_string. This is
# what makes the Schemes/For You/Profile tabs fast after the first view: the
# scheme dataset is static for the lifetime of the process, so once a given
# string has been translated into a given language it never needs a Groq
# call again. Unbounded for simplicity (dataset + UI strings are small); for
# a large dataset or many languages you'd want an LRU cap or a persisted
# cache (e.g. a table/column in the CSV) instead of calling this live.
_translation_cache = {}

# Max number of strings translated per LLM call. The previous version sent
# every uncached string in ONE prompt -- so the first time anyone opened the
# Schemes tab in a new language with no search/filter applied, it built a
# single prompt containing every scheme's name + category + short
# description in the dataset, and waited on one giant completion. That is
# almost certainly the "hugely" slow/expensive case you're seeing. Batching
# keeps each call small (fast, cheap, and unlikely to hit output-length
# issues that silently drop lines), and a bad batch no longer costs you the
# translations that would otherwise have succeeded in other batches.
_TRANSLATE_BATCH_SIZE = 25


def translate_strings(strings, lang):
    """Batch-translates a list of plain strings into `lang`, in chunks of
    _TRANSLATE_BATCH_SIZE per LLM call (falling back to per-string cache hits
    where available), preserving order and count. Returns the input
    unchanged if lang is English/unknown or the list is empty. Used by
    _row_to_summary, _row_to_detail, rank_schemes_for_profile, and
    api_ui_strings -- i.e. everywhere the Schemes/For You/Profile tabs need
    translated text, as opposed to translate_answer/translate_query_to_english
    which are specific to the Discovery chat pipeline's single Markdown
    answer / single question.

    This does NOT touch retrieval, scoring, or ranking -- it only converts
    already-decided text for display, after all matching/tiering is done.
    """
    if not lang or lang == "en" or lang not in SUPPORTED_LANGUAGES or not strings:
        return list(strings)

    result = [None] * len(strings)
    to_translate = []  # list of (original_index, string)
    for i, s in enumerate(strings):
        if not s:
            result[i] = s
            continue
        key = (lang, s)
        cached = _translation_cache.get(key)
        if cached is not None:
            result[i] = cached
        else:
            to_translate.append((i, s))

    if not to_translate:
        return result

    lang_name = SUPPORTED_LANGUAGES[lang]["name"]
    line_pattern = re.compile(r"^\s*(\d+)\s*[\.\)]\s*(.*)$")

    for batch_start in range(0, len(to_translate), _TRANSLATE_BATCH_SIZE):
        batch = to_translate[batch_start:batch_start + _TRANSLATE_BATCH_SIZE]
        numbered_input = "\n".join(f"{n}. {s}" for n, (_, s) in enumerate(batch))
        messages = [
            SystemMessage(content=(
                f"Translate each numbered line below FULLY into {lang_name}. "
                "Keep the exact same numbering, output exactly one translated line per "
                "input line, and do not merge, skip, or reorder lines. "
                "Do not add any commentary, preamble, or extra numbering of your own. "
                "If a line is a proper noun or acronym with no natural translation, "
                "transliterate it into the target script rather than leaving it in Latin "
                "script, unless it is a globally recognized acronym."
            )),
            HumanMessage(content=numbered_input)
        ]
        try:
            raw = invoke_light(messages).content.strip()
            translated_map = {}
            for line in raw.split("\n"):
                m = line_pattern.match(line)
                if m:
                    translated_map[int(m.group(1))] = m.group(2).strip()
            for n, (orig_i, s) in enumerate(batch):
                translated = translated_map.get(n, s)  # fall back to source string if parsing missed a line
                _translation_cache[(lang, s)] = translated
                result[orig_i] = translated
        except Exception as e:
            print(f"translate_strings batch failed: {e}")
            for orig_i, s in batch:
                result[orig_i] = s  # fail open: show English rather than break the tab

    return result


# Static UI copy for the Schemes / Find Schemes for Me / Profile tabs --
# search placeholders, button labels, empty-state text, etc. Translated as
# one batch per language on first request and then served from
# _translation_cache, via GET /api/ui-strings?lang=<code>. Keys are matched
# to element ids/usages in index.html's applyUiStrings().
UI_STRINGS_EN = {
    "nav_discovery": "Discovery",
    "nav_schemes": "Schemes",
    "nav_finder": "For You",
    "nav_profile": "Profile",
    "schemes_search_placeholder": "Search by name, category, or tag...",
    "schemes_filter_all": "All",
    "schemes_filter_saved": "♡ Saved",
    "schemes_empty_default": "No schemes found. Try a different search or filter.",
    "schemes_empty_saved": "No saved schemes yet. Tap ♡ on a scheme to save it.",
    "finder_intro_title": "Find Schemes for Me",
    "finder_intro_body": (
        "Tell us a bit about yourself and our matching engine will rank government schemes "
        "you're likely eligible for — with a plain-language reason for every match, grouped "
        "by your state, Central schemes, and other states."
    ),
    "finder_label_age": "Age",
    "finder_label_gender": "Gender",
    "finder_gender_prefer_not": "Prefer not to say",
    "finder_gender_female": "Female",
    "finder_gender_male": "Male",
    "finder_gender_other": "Other",
    "finder_label_income": "Annual income (₹)",
    "finder_label_category": "Category",
    "finder_label_occupation": "Occupation",
    "finder_occupation_select": "Select occupation",
    "finder_label_area": "Area",
    "finder_area_not_sure": "Not sure",
    "finder_area_rural": "Rural",
    "finder_area_urban": "Urban",
    "finder_label_state": "State / UT",
    "finder_state_all_india": "All India / Not sure",
    "finder_hint": (
        "This gives you a quick shortlist based on stated eligibility patterns — always "
        "confirm final eligibility on the scheme's official page before applying."
    ),
    "finder_submit": "Find My Schemes",
    "finder_submit_loading": "Finding your schemes…",
    "finder_empty_default": 'Fill in your details above and tap "Find My Schemes" to see your matches here.',
    "finder_empty_no_match": (
        "We couldn't find a confident match for these details — try broadening a field "
        "like income or occupation."
    ),
    "finder_results_label": "Top {n} matches for you",
    "match_why_label": "Why this matches you",
    "modal_overview": "Overview",
    "modal_eligibility": "Eligibility",
    "modal_benefits": "Benefits",
    "modal_apply": "How to Apply",
    "modal_documents": "Documents Required",
    "modal_official_link": "Official link ↗",
    "modal_save": "♡ Save this scheme",
    "modal_saved": "♥ Saved — tap to remove",
    "profile_title": "Citizen",
    "profile_stat_saved": "Saved Schemes",
    "profile_stat_theme": "Theme",
    "profile_theme_light": "Light",
    "profile_theme_dark": "Dark",
    "profile_saved_section": "Saved Schemes",
    "profile_empty_note": "You haven't saved any schemes yet. Tap ♡ on a scheme in the Schemes tab to save it here.",
    "profile_clear_btn": "Clear all saved schemes",
    "snackbar_saved": "Saved to Profile",
    "snackbar_removed": "Removed from saved",
    "snackbar_cleared": "Cleared all saved schemes",
    "snackbar_load_error": "Couldn't load schemes right now. Please try again.",
    "snackbar_network_error": "Network error — please try again",
}


# ---------------------------------------------------------------------------
# mem0 long-term memory store
# ---------------------------------------------------------------------------
os.makedirs(os.path.dirname(MEM0_QDRANT_PATH) or ".", exist_ok=True)

mem0_config = {
    "llm": {
        "provider": "groq",
        "config": {
            # COST FIX: this used to be MAIN_LLM_MODEL. add_to_memory() below
            # always calls memory.add(..., infer=False), which skips mem0's
            # LLM-based fact-extraction pass entirely, so in normal operation
            # this model is never actually invoked per-turn. Still, pointing
            # it at the small model instead of the 120b one is a free safety
            # net in case that ever changes (e.g. you later call
            # memory.search() with LLM reranking, or flip infer=True).
            "model": LIGHT_LLM_MODEL,
            "api_key": GROQ_API_KEY,
        },
    },
    "embedder": {
        "provider": "huggingface",
        "config": {
            "model": EMBED_MODEL_NAME,  # reuse the same embedder already loaded above
        },
    },
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "collection_name": "scheme_assistant_memory",
            "embedding_model_dims": 384,
            "path": MEM0_QDRANT_PATH,  # local on-disk store, persists across runs
        },
    },
    "history_db_path": MEM0_HISTORY_DB,
}

memory = Memory.from_config(mem0_config)


# mem0's SQLite history-db connection was created on the main thread at
# startup, and sqlite3 connections can't be used from a different thread.
# A single-worker executor guarantees every memory.add() call below runs on
# the SAME thread every time (this one), so the connection stays valid --
# while letting Flask itself handle multiple requests concurrently for
# everything else (chat, schemes list, scheme detail, find-schemes).
# Nothing in this file ever calls memory.search(), so these writes are pure
# bookkeeping the response never needs to wait on -- hence submit() and not
# .result().
_mem0_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="mem0-writer")


def add_to_memory(user_id, role, content):
    # infer=False: store the raw turn as-is instead of letting mem0 run its own
    # fact-extraction LLM pass over it (we already control what gets stored).
    def _write():
        try:
            memory.add(content, user_id=user_id, metadata={"role": role}, infer=False)
        except Exception as e:
            print(f"mem0 add_to_memory failed (non-fatal): {e}")

    _mem0_executor.submit(_write)


# last_scheme[user_id] = {"slug": str|None, "name": str}
# Deterministic "what scheme is this conversation about right now" tracker,
# used to resolve pronouns ("its eligibility?") without relying on mem0 search.
last_scheme = {}


def resolve_query_with_memory(user_id, query):
    """Returns (resolved_query, pinned_slug, force_web).
    force_web=True means the current topic was web-sourced last time --
    skip local retrieval entirely for the follow-up too.

    A query gets pinned to the current topic three ways:
      1. Explicit reference ("its eligibility?", "what about this scheme?")
         -> the LLM rewrites it, substituting the actual scheme name.
      2. No scheme named, not a "list schemes" query, short enough to be a
         quick follow-up ("what documents are required?", "how do I
         apply?") -> pinned as-is, no rewrite needed.
      3. None of the above textual signals fired, but a cheap semantic
         retrieval check confirms the query doesn't strongly match some
         OTHER scheme -> stays pinned. If it does match a different scheme
         (e.g. "agniveer" vs. the dataset's "Agnipath Yojana" -- related in
         meaning but sharing no keyword with mentions_scheme_keyword()), it
         un-pins so the query gets a fresh normal retrieval instead of being
         wrongly answered against the pinned scheme's unrelated context.

    FIX: a query that explicitly introduces a new topic ("what is X",
    "tell me about X", ...) with no pronoun is now always treated as a new
    topic and unpinned, even when X isn't in the local dataset at all (so
    mentions_scheme_keyword() can't see it) and even when the FAISS
    semantic check comes back empty (score < 0.45, so quick_matches is
    empty and the "unpin if a different scheme matches" check never
    fires). Previously such a query silently stayed pinned to whatever
    scheme was last discussed, and its downstream web-fallback query was
    then corrupted by having the (wrong) pinned scheme's name prepended to
    it -- see the fallback_query fix in chat_rag() below.

    NOTE: this function always receives an already-English query -- any
    script-based translation happens in api_chat() before this is called.
    """
    topic = last_scheme.get(user_id)
    if not topic:
        return query, None, False

    has_pronoun = bool(PRONOUN_PATTERN.search(query))

    if not has_pronoun:
        focus = detect_focus(query)

        if focus in ("eligibility", "benefits", "application") and len(query.split()) <= 12:
            if topic["slug"]:
                return query, topic["slug"], False
            else:
                return query, None, True

        looks_like_new_topic = (
            is_list_query(query)
            or mentions_scheme_keyword(query)
            or len(query.split()) > 12
            or bool(NEW_TOPIC_QUERY_PATTERN.match(query))
        )
        if looks_like_new_topic:
            return query, None, False

        # None of the textual signals fired -- before defaulting to "stay
        # pinned," do a cheap semantic check via the same FAISS retrieval
        # chat_rag already uses elsewhere. Only overrides the pin if some
        # OTHER scheme is a strong, confident match for this query.
        quick_matches = retrieve(query, k=1, min_score=0.45)
        if quick_matches and quick_matches[0]["slug"] != topic.get("slug"):
            return query, None, False

    if has_pronoun:
        rewrite_prompt = [
            SystemMessage(content=(
                "Rewrite the user's question to replace vague references (it/its/that scheme/this scheme) "
                f'with the specific scheme name: "{topic["name"]}". '
                "Return ONLY the rewritten question, nothing else."
            )),
            HumanMessage(content=f"Question: {query}")
        ]
        # Guard against an empty rewrite reaching chat_rag() -- an empty
        # query would break retrieval entirely, so fall back to the
        # original (un-rewritten) query rather than passing "" downstream.
        resolved = invoke_light(rewrite_prompt).content.strip() or query
    else:
        resolved = query

    if topic["slug"]:
        return resolved, topic["slug"], False
    else:
        return resolved, None, True  # web-only topic -> stay on the web


# ---------------------------------------------------------------------------
# Focus detection (eligibility / benefits / application / overview)
# ---------------------------------------------------------------------------
def _detect_focus_keywords(query):
    q = query.lower()
    # order matters: eligibility phrases are checked first so "who can apply"
    # doesn't fall into the "application" bucket via the bare word "apply"
    for focus in ("eligibility", "benefits", "application"):
        if any(kw in q for kw in FOCUS_KEYWORDS[focus]):
            return focus
    return None


def detect_focus(query):
    focus = _detect_focus_keywords(query)
    if focus:
        return focus
    # keyword list missed it (e.g. "can I join it?") -> ask the cheap model
    try:
        resp = invoke_light(
            [HumanMessage(content=_FOCUS_CLASSIFIER_PROMPT.format(query=query))]
        ).content.strip().lower()
        if resp in ("eligibility", "benefits", "application"):
            return resp
    except Exception:
        pass
    return None  # overview / unclear -> full template


def _focus_format_instructions(focus):
    return (
        f"Start your answer with a single line: '**Scheme: <exact scheme name>**' then a blank line. "
        f"The user is asking specifically about the scheme's {focus}. "
        f"Answer ONLY that — a short paragraph or bullet list. "
        f"Do NOT include Overview or the other sections unless directly asked. "
        f"Do not use the full structured template."
    )


# ---------------------------------------------------------------------------
# "List schemes I'm eligible for" handling
# ---------------------------------------------------------------------------
def is_list_query(query):
    return bool(LIST_QUERY_PATTERN.search(query))


def _parse_list_evaluation(raw_text, max_schemes=4):
    entries = []
    for block in raw_text.split("---"):
        m = LIST_EVAL_PATTERN.search(block)
        if not m or m.group("status").upper() != "FIT":
            continue
        entries.append({
            "name": m.group("name").strip(),
            "reason": m.group("reason").strip(),
            "eligibility": m.group("eligibility").strip(),
        })
    return entries[:max_schemes]


def _format_list_answer(entries):
    if not entries:
        return ("None of the schemes I found clearly matched your situation. "
                "You may want to check with your local government office for more options.")
    lines = []
    for e in entries:
        lines.append(f"**{e['name']}**")
        lines.append(f"- Why it fits: {e['reason']}")
        if e["eligibility"]:
            lines.append(f"- Eligibility: {e['eligibility']}")
        lines.append("")
    return "\n".join(lines).strip()


def _web_fallback_list_answer(query):
    """Used when local retrieval has nothing (or nothing FIT) for a
    'list schemes I qualify for' style query. Searches the web and asks the
    model to enumerate every relevant scheme it finds in the results, each
    with a short eligibility check against the user's situation and a
    citation — instead of forcing a single-scheme profile format."""
    web_context = web_fallback_context(query)
    if not web_context:
        return None  # let the caller decide what to show if web also comes up empty

    messages = [
        SystemMessage(content=(
            "You are a government scheme assistant. The context below was retrieved from the web "
            "because the local database didn't have a strong match for this user's situation.\n\n"
            "List EVERY relevant government scheme you find in this context that plausibly fits the "
            "user's situation (age, income, employment status, location, category, etc. — whatever "
            "they mentioned). For each scheme, write:\n"
            "- **<Scheme name>** — one line on what it offers and why it fits the user's situation, "
            "ending with a citation like 【Source: <page title>】.\n\n"
            "Only include schemes the context actually supports — do not invent schemes or eligibility "
            "details not present in the context. If nothing in the context is genuinely relevant, say so."
        )),
        HumanMessage(content=f"Web search context:\n{web_context}\n\nUser's situation: {query}")
    ]
    return llm.invoke(messages).content


# ---------------------------------------------------------------------------
# NO_MATCH / STATUS line handling
# ---------------------------------------------------------------------------
def _looks_like_no_match(answer_text):
    first_line = answer_text.strip().split("\n", 1)[0].strip().upper()
    if first_line.startswith("STATUS:"):
        return "NO_MATCH" in first_line
    return bool(NO_MATCH_PATTERN.search(answer_text))  # safety net if the model forgets the status line


def _strip_status_line(answer_text):
    lines = answer_text.strip().split("\n", 1)
    if lines[0].strip().upper().startswith("STATUS:"):
        return lines[1].strip() if len(lines) > 1 else ""
    return answer_text


def _extract_scheme_name_from_answer(answer_text):
    m = SCHEME_NAME_PATTERN.search(answer_text)
    return m.group(1).strip(" *") if m else None


def _strip_scheme_name_line(answer_text):
    lines = answer_text.strip().split("\n")
    if lines and SCHEME_NAME_PATTERN.match(lines[0].strip()):
        return "\n".join(lines[1:]).lstrip("\n")
    return answer_text


# ---------------------------------------------------------------------------
# Web search fallback (used when local retrieval is empty/weak)
# ---------------------------------------------------------------------------
def web_search(query, focus=None, max_results=3, retries=1, timeout=8):
    search_query = query
    if focus:
        search_query += f" {focus}"
    search_query += " government scheme India site:gov.in OR site:india.gov.in OR site:wikipedia.org"

    for _ in range(retries + 1):
        try:
            with DDGS(timeout=timeout) as ddgs:
                return list(ddgs.text(search_query, max_results=max_results))
        except Exception as e:
            print(f"web_search failed: {e}")
    return []


def fetch_page_text(url, focus=None, max_chars=2200, window_chars=1800):
    try:
        resp = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = " ".join(soup.get_text(separator=" ").split())

        if focus:
            focus_terms = {
                "eligibility": ["eligibility", "eligible", "criteria", "who can apply"],
                "benefits": ["benefits", "benefit"],
                "application": ["how to apply", "application process", "documents required"],
            }.get(focus, [focus])

            lower_text = text.lower()
            for term in focus_terms:
                idx = lower_text.find(term)
                if idx != -1:
                    start = max(0, idx - 300)
                    end = min(len(text), idx + window_chars)
                    return text[start:end]

        return text[:max_chars]
    except Exception:
        return ""


def web_fallback_context(query, focus=None):
    results = web_search(query, focus=focus)
    contexts = []
    for r in results:
        text = fetch_page_text(r["href"], focus=focus)
        if text:
            contexts.append(f"[Source: {r['title']} — {r['href']}]\n{text}")
    return "\n\n".join(contexts)


def _web_fallback_answer(query, focus=None):
    """Returns (answer, used, scheme_name). used=False means no usable web context was found."""
    web_context = web_fallback_context(query, focus=focus)
    if not web_context:
        return FALLBACK_MSG, False, None

    format_instructions = _focus_format_instructions(focus) if focus else STRUCTURE_INSTRUCTIONS

    messages = [
        SystemMessage(content=(
            "You are a government scheme assistant. The context below was retrieved from the web "
            "because the scheme wasn't found (or wasn't a confident match) in the local database.\n\n"
            "Before your answer, output exactly one line:\n"
            "SCHEME_NAME: <the exact name of the scheme/act/programme this context is about>\n"
            "Then a blank line, then your answer.\n\n"
            "Answer the user's question using ONLY this context. Cite specific source names/URLs "
            "inline where you use a fact, but do NOT add a closing note or disclaimer stating that "
            "the answer came from a web search — just answer directly."
            + "\n\n" + format_instructions
        )),
        HumanMessage(content=f"Web search context:\n{web_context}\n\nQuestion: {query}")
    ]
    raw_answer = llm.invoke(messages).content
    scheme_name = _extract_scheme_name_from_answer(raw_answer)
    answer = _strip_scheme_name_line(raw_answer)
    return answer, True, scheme_name


# ---------------------------------------------------------------------------
# Core RAG answer function
# ---------------------------------------------------------------------------
def chat_rag(query, k=8, min_score=0.30, weak_score=0.35,
             web_fallback_threshold=0.55, pinned_slug=None, force_web=False, return_meta=False):

    # --- "list all schemes I'm eligible for" path ---
    if is_list_query(query) and not pinned_slug and not force_web:
        matched = retrieve(query, k=6, min_score=min_score, per_scheme_limit=1)
        top1_score = matched[0]["score"] if matched else 0.0

        if not matched or top1_score < web_fallback_threshold:
            # nothing plausible locally, or only weak/tangential local matches
            # (e.g. narrow regional schemes that barely overlap the user's
            # situation) -- try the web for stronger, more relevant schemes
            web_answer = _web_fallback_list_answer(query)
            if web_answer:
                return (web_answer, None, None) if return_meta else web_answer
            # web came up empty too -- fall through and use whatever local
            # candidates exist rather than showing nothing at all

        sections = []
        for r in matched:
            scheme_chunks = get_all_chunks_for_scheme(r["slug"])
            text = "\n".join(c["text"] for c in scheme_chunks[:3])
            sections.append(f"[{r['scheme_name']}]\n{text}")
        combined_context = "\n\n".join(sections)

        messages = [
            SystemMessage(content=(
                "You are a government scheme assistant. Below is context on several candidate schemes "
                "retrieved for this user's situation, separated by '---'. You MUST evaluate EVERY single "
                "scheme listed — do not skip any. For each scheme, in the exact order given, decide whether "
                "it plausibly fits the user's situation (age, state/location, gender, category, and any "
                "other stated criteria). If eligibility isn't fully clear from the context but the scheme "
                "looks plausibly relevant, mark it FIT anyway and note what's uncertain in the eligibility "
                "line. Only mark NO_FIT if it clearly does not match (e.g. wrong state, wrong age group, "
                "wrong gender).\n\n"
                "Output ONLY the following block for each scheme, nothing else, no extra commentary:\n\n"
                "SCHEME: <exact scheme name>\n"
                "STATUS: FIT or NO_FIT\n"
                "REASON: <one line on why it fits or doesn't>\n"
                "ELIGIBILITY: <one line on eligibility criteria, blank if NO_FIT>\n"
                "---\n"
                "(repeat this block for every scheme in the context, separated by ---)"
            )),
            HumanMessage(content=f"Context:\n{combined_context}\n\nUser's question: {query}")
        ]
        raw_eval = llm.invoke(messages).content
        entries = _parse_list_evaluation(raw_eval, max_schemes=4)

        if not entries:
            # local candidates existed but none held up under evaluation --
            # try the web instead of settling fxor "no match"
            web_answer = _web_fallback_list_answer(query)
            answer = web_answer if web_answer else _format_list_answer(entries)
            return (answer, None, None) if return_meta else answer

        answer = _format_list_answer(entries)
        return (answer, None, None) if return_meta else answer

    focus = detect_focus(query)

    # --- previous turn was web-sourced, stay on the web for follow-ups ---
    if force_web:
        answer, used, topic_name = _web_fallback_answer(query, focus=focus)
        return (answer, topic_name, None) if return_meta else answer

    # --- conversation is pinned to a known local scheme ---
    if pinned_slug:
        full_scheme_chunks = get_all_chunks_for_scheme(pinned_slug)
        if full_scheme_chunks:
            best_scheme_name = full_scheme_chunks[0]["scheme_name"]
            context = "\n\n".join(f"[{c['scheme_name']} — {c['type']}]\n{c['text']}" for c in full_scheme_chunks)
            format_instructions = _focus_format_instructions(focus) if focus else STRUCTURE_INSTRUCTIONS
            messages = [
                SystemMessage(content=(
                    "You are a government scheme assistant. Below is the full profile of the scheme "
                    "the user is currently discussing. Answer the user's specific question using only "
                    "what's relevant to it.\n\n" + MATCH_STATUS_INSTRUCTIONS + "\n\n" + format_instructions
                )),
                HumanMessage(content=f"Context:\n{context}\n\nQuestion: {query}")
            ]
            answer = llm.invoke(messages).content
            if _looks_like_no_match(answer):
                # FIX: previously this always prepended best_scheme_name
                # (the WRONG pinned scheme, in the mis-pinning case) onto
                # the query whenever the query didn't already contain that
                # name -- e.g. "what is Garib Kalyan Rojgar Abhiyaan?" while
                # wrongly pinned to "Agnipath Yojana" became
                # "Agnipath Yojana what is Garib Kalyan Rojgar Abhiyaan ?",
                # which corrupted/derailed the web search. Now: if the query
                # already looks like it's explicitly introducing its own
                # topic (NEW_TOPIC_QUERY_PATTERN, e.g. "what is X",
                # "tell me about X"), search with the query as-is instead of
                # prepending a possibly-wrong scheme name. The prepend is
                # still useful (and kept) for genuine short follow-ups like
                # "who can apply?" where the scheme name really does need to
                # be added back in for a good web search.
                if NEW_TOPIC_QUERY_PATTERN.match(query) or best_scheme_name.lower() in query.lower():
                    fallback_query = query
                else:
                    fallback_query = f"{best_scheme_name} {query}"
                answer, used, topic_name = _web_fallback_answer(fallback_query, focus=focus)
                return (answer, topic_name, None) if return_meta else answer
            answer = _strip_status_line(answer)
            return (answer, best_scheme_name, pinned_slug) if return_meta else answer
        # slug not found locally -> fall through to normal retrieval below

    # --- normal local retrieval path ---
    query_expanded = expand_acronyms(query)
    retrieved = retrieve(query_expanded, k=k, min_score=min_score)
    top1_score = retrieved[0]["score"] if retrieved else 0.0
    needs_web_fallback = (not retrieved) or (top1_score < web_fallback_threshold)

    if needs_web_fallback:
        answer, used, topic_name = _web_fallback_answer(query, focus=focus)
        return (answer, topic_name, None) if return_meta else answer

    best_slug = retrieved[0]["slug"]
    best_scheme_name = retrieved[0]["scheme_name"]
    full_scheme_chunks = get_all_chunks_for_scheme(best_slug)
    context = "\n\n".join(f"[{c['scheme_name']} — {c['type']}]\n{c['text']}" for c in full_scheme_chunks)

    confidence_note = "" if top1_score >= weak_score else (
        "\nNote: retrieval confidence is low — only use this context if it clearly matches the question."
    )
    format_instructions = _focus_format_instructions(focus) if focus else STRUCTURE_INSTRUCTIONS

    messages = [
        SystemMessage(content=(
            "You are a government scheme assistant. Below is the full profile of the best-matching scheme. "
            "Answer the user's specific question using only what's relevant to it."
            + confidence_note + "\n\n" + MATCH_STATUS_INSTRUCTIONS + "\n\n" + format_instructions
        )),
        HumanMessage(content=f"Context:\n{context}\n\nQuestion: {query}")
    ]
    answer = llm.invoke(messages).content

    if _looks_like_no_match(answer):
        answer, used, topic_name = _web_fallback_answer(query, focus=focus)
        return (answer, topic_name, None) if return_meta else answer

    answer = _strip_status_line(answer)
    matched_slug = best_slug if top1_score >= weak_score else None
    matched_name = best_scheme_name if top1_score >= weak_score else None
    return (answer, matched_name, matched_slug) if return_meta else answer


def chat_rag_with_memory(user_id, query, k=8, min_score=0.30, weak_score=0.35, web_fallback_threshold=0.55):
    resolved_query, pinned_slug, force_web = resolve_query_with_memory(user_id, query)

    answer, matched_name, matched_slug = chat_rag(
        resolved_query, k=k, min_score=min_score, weak_score=weak_score,
        web_fallback_threshold=web_fallback_threshold,
        pinned_slug=pinned_slug, force_web=force_web, return_meta=True
    )

    if matched_slug:
        last_scheme[user_id] = {"slug": matched_slug, "name": matched_name}
    elif matched_name:
        # web-sourced topic -- track it (slug=None) so a follow-up pronoun
        # routes straight back to web instead of risking another bad local match
        last_scheme[user_id] = {"slug": None, "name": matched_name}

    # mem0 long-term store (kept separate from the deterministic last_scheme tracker)
    add_to_memory(user_id, "user", resolved_query)
    add_to_memory(user_id, "assistant", f"Answered about: {resolved_query}")

    return answer


# ---------------------------------------------------------------------------
# Flask app
# ---------------------------------------------------------------------------
app = Flask(__name__)


def _normalize_lang(raw):
    """Every route below accepts an optional lang param; this normalizes it
    to a known SUPPORTED_LANGUAGES key (defaulting to English) so a typo or
    stale localStorage value never causes a translate_strings KeyError."""
    lang = (raw or "en").strip().lower()
    return lang if lang in SUPPORTED_LANGUAGES else "en"


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/schemes", methods=["GET"])
def api_schemes_list():
    """Plain browse/search/filter over the dataset -- powers the Schemes tab
    grid. Query params:
      - search: matches against scheme name, category, and tags (substring,
        case-insensitive). NOTE: matching is always done against the
        underlying ENGLISH dataset text regardless of `lang`, since the
        dataset itself is English -- only the returned display strings are
        translated. If you want search-in-translated-text too, translate
        `search` back to English first the same way api_chat() does for
        chat queries.
      - category: exact category match (case-insensitive); omit or "all" for no filter
      - lang: language code for the returned scheme names/categories/descriptions
        (see SUPPORTED_LANGUAGES); defaults to English.

    NOTE ON TOKEN USAGE: with no search/category filter applied, this
    translates every scheme in the dataset the first time a given language
    is requested (subsequent requests reuse _translation_cache and cost
    nothing). If your dataset is large and you want the *very first* load
    in each language to be fast too, consider adding a `limit`/`offset`
    (pagination) here and only translating the page actually shown -- the
    frontend would need a matching change to request pages instead of the
    full list.
    """
    search = (request.args.get("search") or "").strip().lower()
    category = (request.args.get("category") or "").strip().lower()
    lang = _normalize_lang(request.args.get("lang"))

    results = []
    for _, row in df.iterrows():
        row_category = str(row.get("schemeCategory", "") or "").strip()

        if category and category != "all" and row_category.lower() != category:
            continue

        if search:
            haystack = " ".join([
                str(row.get("scheme_name", "")),
                row_category,
                str(row.get("tags", "")),
            ]).lower()
            if search not in haystack:
                continue

        results.append(_row_to_summary(row, lang=lang))

    return jsonify({"schemes": results})


@app.route("/api/schemes/categories", methods=["GET"])
def api_schemes_categories():
    """Distinct category list for the category-chip row.

    Returns each category as {"value": <english, lowercased>, "label": <translated
    display text>}. The chip's filter VALUE must stay in English because
    /api/schemes always matches against the untranslated dataset text -- only
    the LABEL shown to the user should be translated. Previously this endpoint
    returned plain translated strings, which the frontend lower-cased and sent
    straight back as the `category` filter param; picking any category chip
    while a non-English language was active then compared translated text
    against English data and matched nothing.
    """
    lang = _normalize_lang(request.args.get("lang"))
    categories = sorted({
        str(c).strip()
        for c in df.get("schemeCategory", pd.Series(dtype=str)).tolist()
        if str(c).strip()
    })
    labels = translate_strings(categories, lang) if lang != "en" else list(categories)
    return jsonify({
        "categories": [
            {"value": c.lower(), "label": label}
            for c, label in zip(categories, labels)
        ]
    })


@app.route("/api/schemes/<slug>", methods=["GET"])
def api_scheme_detail(slug):
    """Full profile for the scheme-details modal, and for resolving saved
    scheme names on the Profile tab."""
    lang = _normalize_lang(request.args.get("lang"))
    row = SLUG_TO_ROW.get(slug)
    if row is None:
        return jsonify({"error": "Scheme not found"}), 404
    return jsonify(_row_to_detail(row, lang=lang))


@app.route("/api/find-schemes", methods=["POST"])
def api_find_schemes():
    """Personalized "Find Schemes for Me" endpoint. Takes a small structured
    profile from the frontend form and runs it through the deterministic
    rule-based eligibility engine (rank_schemes_for_profile) -- scoring
    itself makes no LLM calls, so it responds instantly; only the optional
    display-translation step (when lang != "en") calls out to the LLM.

    Results are grouped into state-priority tiers (see classify_scheme_tier)
    so schemes naming the user's own state rank ahead of Central/nationwide
    schemes, which in turn rank ahead of schemes naming a different state --
    each result carries "state_scope" (0/1/2) and "state_scope_label" so the
    frontend can render a heading per group.

    Expected JSON body (all fields optional, but the more filled in, the
    better the matches):
      { "age": 28, "income": 250000, "gender": "female",
        "category": "OBC", "occupation": "farmer", "area": "rural",
        "state": "Rajasthan", "lang": "hi" }
    """
    data = request.get_json(force=True) or {}

    def _to_int(val):
        try:
            return int(val) if val not in (None, "") else None
        except (TypeError, ValueError):
            return None

    def _to_float(val):
        try:
            return float(val) if val not in (None, "") else None
        except (TypeError, ValueError):
            return None

    profile = {
        "age": _to_int(data.get("age")),
        "income": _to_float(data.get("income")),
        "gender": (data.get("gender") or "").strip(),
        "category": (data.get("category") or "").strip(),
        "occupation": (data.get("occupation") or "").strip().lower(),
        "area": (data.get("area") or "").strip(),
        "state": (data.get("state") or "").strip(),
    }
    lang = _normalize_lang(data.get("lang"))

    try:
        matches = rank_schemes_for_profile(profile, top_n=10, lang=lang)
        return jsonify({"matches": matches, "profile": profile})
    except Exception as e:
        print("Error in /api/find-schemes:", e)
        return jsonify({"error": "Something went wrong while finding schemes for you."}), 500


@app.route("/api/languages", methods=["GET"])
def api_languages():
    """List of supported languages for the language selector, plus the
    BCP-47 speech locale the frontend should use for mic input / read-aloud
    in that language."""
    return jsonify({
        "languages": [
            {"code": code, "name": info["name"], "speech_locale": info["speech_locale"]}
            for code, info in SUPPORTED_LANGUAGES.items()
        ]
    })


@app.route("/api/ui-strings", methods=["GET"])
def api_ui_strings():
    """Static UI copy (search placeholder, button labels, empty states, nav
    labels, etc.) for the Schemes / Find Schemes for Me / Profile tabs, in
    the requested language. Discovery's chat bubbles don't need this since
    every chat answer is already translated per-turn by translate_answer();
    this covers everything else in the UI that translate_answer never
    touches. Translated once per language then served from
    _translation_cache."""
    lang = _normalize_lang(request.args.get("lang"))
    if lang == "en":
        return jsonify({"strings": UI_STRINGS_EN})
    keys = list(UI_STRINGS_EN.keys())
    values = list(UI_STRINGS_EN.values())
    translated_values = translate_strings(values, lang)
    return jsonify({"strings": dict(zip(keys, translated_values))})


@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(force=True) or {}
    user_id = (data.get("user_id") or "").strip()
    message = (data.get("message") or "").strip()
    requested_language = (data.get("language") or "en").strip().lower()

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    if not message:
        return jsonify({"error": "message is required"}), 400

    try:
        # Detect the script of the incoming message itself. This lets a user
        # who typed/spoke in Hindi/Bengali/etc. get answered in that language
        # even if the language dropdown was left on the default "English".
        # An explicit dropdown choice other than English still always wins,
        # since that's a deliberate override of whatever they typed in.
        detected_lang = detect_query_script_language(message)
        output_language = requested_language if requested_language != "en" else (detected_lang or "en")

        # The retrieval/pinning pipeline is English-only -- translate a
        # non-English query into English before it goes anywhere near
        # chat_rag_with_memory(). If the message already looks like plain
        # Latin-script text, detected_lang is None and we skip this (no
        # need to round-trip English through translation).
        query_for_pipeline = message
        if detected_lang:
            query_for_pipeline = translate_query_to_english(message)

        answer = chat_rag_with_memory(user_id, query_for_pipeline)
        answer = translate_answer(answer, output_language)
        return jsonify({"answer": answer, "language": output_language})
    except Exception as e:
        print("Error in /api/chat:", e)
        return jsonify({"error": "Something went wrong while generating the answer."}), 500


if __name__ == "__main__":
    # use_reloader=False: Flask's debug reloader spawns a second process that
    # re-runs this whole file (including mem0's local Qdrant init), which
    # crashes with a "storage folder already locked" error. Since the reloader
    # is just a convenience for auto-restarting on code changes, we disable it
    # and restart manually instead.
    # threaded=False: mem0's history store uses a SQLite connection created in
    # the main thread at startup. Flask's dev server defaults to handling each
    # request in a new thread, and SQLite connections can't be used across
    # threads — that caused a "SQLite objects created in a thread..." error.
    # Running single-threaded keeps everything on the thread that initialized
    # mem0, at the cost of handling one request at a time (fine for local use).
    app.run(debug=True, use_reloader=False, threaded=True, host="0.0.0.0", port=5000)