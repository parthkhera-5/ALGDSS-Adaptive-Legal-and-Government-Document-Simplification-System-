# Citizen Services — Government Schemes RAG Assistant

A Flask web app that helps Indian citizens discover government schemes they may be eligible for. It combines a retrieval-augmented chatbot (FAISS + Groq LLMs, with a live web-search fallback) with a deterministic rule-based eligibility matcher, a browsable scheme catalogue, and full multi-language support across 11 Indian languages — including voice input and read-aloud output.

---

## Features

**Discovery (AI chat)**
- Local semantic retrieval over a scheme dataset using `BAAI/bge-small-en-v1.5` embeddings and a FAISS `IndexFlatIP` index (cosine similarity on normalized vectors).
- Automatic web-search fallback (DuckDuckGo, restricted to `gov.in` / `india.gov.in` / `wikipedia.org`) when local retrieval is weak or empty.
- Conversation topic pinning: follow-ups like *"what's its eligibility?"* resolve against the scheme discussed in the previous turn, whether that scheme came from the local dataset or from the web.
- Focus detection — the answer is formatted specifically for eligibility / benefits / application questions instead of always dumping the full template.
- Dedicated multi-scheme evaluation path for *"list all schemes I'm eligible for"* style questions.
- Long-term per-user memory via `mem0` (local Qdrant + SQLite history), kept separate from the deterministic in-process topic tracker.

**For You (personalized matching)**
- Rule-based eligibility engine that scores every scheme against a small structured profile (age, income, gender, social category, occupation, rural/urban, state).
- No LLM calls in the scoring path, so ranking is instant and fully reproducible.
- Every point awarded is paired with a plain-language reason, surfaced in the UI as "Why this matches you".
- State-priority tiering: schemes naming the user's own state rank above Central/National schemes, which rank above schemes specific to a different state.

**Schemes & Profile**
- Browse, search, and filter the full dataset by name, category, or tag.
- Scheme detail modal showing the same fields the chatbot cites.
- Save schemes to a local bookmark list (localStorage), surfaced on the Profile tab.

**Multi-language**
- English, Hindi, Bengali, Tamil, Telugu, Marathi, Gujarati, Kannada, Malayalam, Punjabi, Urdu.
- Incoming queries are script-detected and translated to English *before* entering the retrieval pipeline (which is English-only), then the finished answer is translated back.
- Translation covers the chat answers, the Schemes tab, the For You results, and all static UI copy.
- Voice input via the Web Speech API in the selected language, plus read-aloud with play/pause and skip-ahead controls.
- RTL layout for Urdu.

---

## Architecture

```
User message
   ↓
Script detection → translate to English (if needed)
   ↓
Topic memory: pin / pronoun rewrite / unpin check
   ↓
FAISS retrieval over scheme chunks
   ↓                          ↓
strong match              weak or empty
   ↓                          ↓
answer from scheme      web search fallback
profile chunks          (gov.in / wikipedia)
   ↓                          ↓
        translate answer to output language
   ↓
Reply + save topic to last_scheme and mem0
```

The **For You** engine is a completely separate path (`/api/find-schemes` → `rank_schemes_for_profile`) with no FAISS, no retrieval, and no LLM calls in the scoring itself — so chat behaviour and matching behaviour can't regress each other.

**Chunking strategy:** each scheme row becomes four chunks — `overview`, `eligibility`, `benefits`, `application` — so retrieval can target the specific section a question is about, while answer generation still receives the scheme's full profile for context.

**Model split:** `openai/gpt-oss-120b` handles answer generation only. Every auxiliary task (query translation, answer translation, pronoun rewriting, focus classification, UI-string translation) routes through the smaller `openai/gpt-oss-20b` via `invoke_light()`, which retries and transparently falls back to the main model if the light model errors or returns empty content.

---

## Project structure

```
.
├── app.py                  # Flask backend — retrieval, matching, translation, all API routes
├── requirements.txt
├── .env                    # GROQ_API_KEY lives here (not committed)
├── data/
│   └── updated_data.csv    # scheme dataset
├── templates/
│   └── index.html          # entire frontend (HTML + CSS + JS, single file)
├── cache/                  # auto-generated on first run
│   ├── embeddings.npy
│   ├── faiss_index.bin
│   └── cache_meta.txt
└── mem0_store/             # auto-generated on first run
    ├── qdrant/
    └── mem0_history.db
```

---

## Dataset format

`data/updated_data.csv` must contain these columns:

| Column | Description |
| --- | --- |
| `scheme_name` | Full official name of the scheme |
| `slug` | Unique URL-safe identifier |
| `schemeCategory` | Category, e.g. Agriculture, Education, Health |
| `tags` | Comma-separated keywords |
| `details` | Long description / objective |
| `eligibility` | Eligibility criteria as free text |
| `benefits` | What the applicant receives |
| `application` | How to apply |
| `documents` | Documents required |

Two optional columns are auto-detected if present and degrade gracefully if absent:
- **Level** — any of `level`, `Level`, `scheme_level`, `govt_level`, `government_level`. Used for Central/National tier classification.
- **Link** — any of `link`, `url`, `official_link`, `apply_link`, `website`, `scheme_link`. Shown as the "Official link" button in the detail modal.

The eligibility text is parsed with regexes for age ranges (`18-40 years`, `above 21 years`, `up to 60 years`) and income ceilings (`income below Rs. 2.5 lakh`), so the more structured that text is, the better the matching engine performs.

---

## Setup

**1. Clone and create a virtual environment**

```bash
git clone <your-repo-url>
cd <repo>
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

**3. Add your dataset**

Place your CSV at `data/updated_data.csv` (or set `DATA_PATH` in `.env` to point elsewhere).

**4. Configure environment variables**

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

Get a free key at [console.groq.com](https://console.groq.com). Optional overrides:

```env
DATA_PATH=data/updated_data.csv
EMBED_CACHE_DIR=./cache
MEM0_QDRANT_PATH=./mem0_store/qdrant
MEM0_HISTORY_DB=./mem0_store/mem0_history.db
```

**5. Run**

```bash
python app.py
```

Open [http://localhost:5000](http://localhost:5000).

> The first run downloads the embedding model and encodes every chunk — this takes a minute or two. The embeddings and FAISS index are then cached in `cache/`, so subsequent startups are near-instant. The cache auto-invalidates when the number of chunks changes (i.e. when you edit the CSV).

---

## API reference

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/` | Serves the single-page frontend |
| `POST` | `/api/chat` | Chat pipeline. Body: `{ user_id, message, language }` → `{ answer, language }` |
| `GET` | `/api/schemes` | Browse/search. Params: `search`, `category`, `lang` |
| `GET` | `/api/schemes/categories` | Distinct categories as `{ value, label }` pairs |
| `GET` | `/api/schemes/<slug>` | Full scheme profile. Param: `lang` |
| `POST` | `/api/find-schemes` | Personalized matching. Body: profile fields + `lang` |
| `GET` | `/api/languages` | Supported languages + BCP-47 speech locales |
| `GET` | `/api/ui-strings` | Translated static UI copy. Param: `lang` |

**Example — personalized matching**

```bash
curl -X POST http://localhost:5000/api/find-schemes \
  -H "Content-Type: application/json" \
  -d '{"age": 28, "income": 250000, "gender": "female",
       "category": "OBC", "occupation": "farmer",
       "area": "rural", "state": "Rajasthan", "lang": "hi"}'
```

Each match returns a `score`, a list of `reasons`, and a `state_scope` tier (`0` = your state, `1` = Central/general, `2` = other states) with a matching `state_scope_label`.

---

## Notable implementation details

**Category filter values stay in English.** `/api/schemes/categories` returns `{ value, label }` pairs — the value is the untranslated English category used for filtering, the label is what the user sees. Sending a translated string back as a filter would match nothing, since `/api/schemes` always matches against the English dataset.

**Translation is batched and cached.** `translate_strings()` sends 25 strings per LLM call and caches every result in-process keyed by `(lang, source_string)`. The dataset is static for the process lifetime, so each string is translated at most once per language.

**Reasoning models need an output budget.** The `openai/gpt-oss-*` models spend tokens on a hidden reasoning pass first. `max_tokens=4096` and `reasoning_effort="low"` are set on the light model — without them a successful API call can return completely empty content, which previously showed up as blank chat bubbles on non-English answers.

**New-topic detection.** A query like *"what is X"* with no pronoun always unpins the current topic, even when X isn't in the local dataset and the semantic check comes up empty. Without this, the web-search fallback query would get the wrong scheme name prepended to it and return an unrelated answer.

**Timeouts are explicit.** Both LLM clients set a timeout (60s main, 20s light) and `max_retries=2`. Without them a stalled Groq response can hang a request indefinitely.

---

## Known limitations

- No account system — user IDs and saved schemes live in the browser's `localStorage`.
- Search matches against the English dataset text only; searching in a translated language won't match.
- The translation cache is unbounded and in-process. For a large dataset or many languages, add an LRU cap or precompute translations into the CSV.
- Loading the Schemes tab in a new language with no filter applied translates the whole dataset on that first request. Add pagination to `/api/schemes` if the dataset grows large.
- The Flask dev server is used as-is. For deployment, put it behind Gunicorn or another WSGI server and move `mem0`'s SQLite history to a thread-safe store.
- Voice input depends on the browser's Web Speech API — Chrome and Edge support the Indian language locales most reliably; Firefox and Safari support is limited.

---

## Disclaimer

Scheme information comes from the bundled dataset and public web sources. It is a starting point for discovery, not an official eligibility determination. Always confirm final eligibility and application details on the scheme's official government page before applying.
