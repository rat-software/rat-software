# RAT: Generative Engine Optimization (GEO) Scorer

The **GEO Scorer** is an empirical analytical module for the RAT backend designed to evaluate how well web documents are optimized for generative AI systems (e.g., Google AI Overviews, Perplexity, SearchGPT).

Unlike traditional SEO tools that focus strictly on keyword positions and backlink volume, the GEO Scorer assesses machine readability, structural scannability, factual density, semantic embedding similarity, and authority signals required by Retrieval-Augmented Generation (RAG) pipelines.

---

## 📊 1. The GEO Scoring Model

The scorer calculates a total score between **0 and 100 points** based on four weighted dimensions:

$$\text{GEO Score} = 0.40 \cdot \text{Authority} + 0.30 \cdot \text{Semantics} + 0.20 \cdot \text{Structure} + 0.10 \cdot \text{Technical}$$


```

```
                             ┌──────────────────────────────────────────────────────────┐
                             │                 Total GEO Score (0-100)                  │
                             └────────────────────────────┬─────────────────────────────┘
                                                          │
     ┌────────────────────────────┬───────────────────────┴───────────────┬────────────────────────────┐
     │ (40%)                      │ (30%)                                 │ (20%)                      │ (10%)

```

┌────────┴─────────────┐   ┌──────────┴───────────────┐            ┌──────────┴───────────────┐ ┌──────────┴─────────────┐
│  Authority & Trust   │   │ Semantics & Readability  │            │  Structure & Formatting  │ │   Technical Baseline   │
├──────────────────────┤   ├──────────────────────────┤            ├──────────────────────────┤ ├──────────────────────┤
│ • Vector Similarity  │   │ • Paragraph Architecture │            │ • Content Length         │ │ • HTTPS Encryption   │
│ • Named Entities     │   │ • Flesch Reading Ease    │            │ • Heading Hierarchy (H1) │ │ • Fast Page Load     │
│ • Statistics & Years │   │ • Q&A / FAQ Elements     │            │ • Tables & Bullet Lists  │ │ • Microdata / JSON-LD│
│ • High-Trust Links   │   │ • Keyword Over-Opt.      │            │ • Title & Meta Desc.     │ └──────────────────────┘
│ • Author & Citations │   └──────────────────────────┘            └──────────────────────────┘
└──────────────────────┘

```

---

## 🧮 2. Scoring Categories & Logic

### A. Authority & Trust (Weight: 40%)
Evaluates whether the content provides factual evidence and verifiable credibility:
* **Semantic Vector Overlap**: For AI source citations (`result_ai_source`), computes cosine similarity between the generated AI snippet and chunked source text using Sentence Transformers (`paraphrase-multilingual-MiniLM-L12-v2`).
* **Named Entities (NER)**: Counts unique organizations, persons, and locations via language-specific spaCy models.
* **Statistical Density**: Detects unique percentages (`%`) and historical year occurrences (`1950–2039`).
* **High-Trust Outbound Links**: Identifies citations to trusted domains (`.edu`, `.gov`, `wikipedia.org`, `nature.com`, `sciencedirect.com`).
* **E-E-A-T Evidence**: Checks for `<blockquote>` elements, quotation marks, `rel="author"` attributes, and publisher markup.

### B. Semantics & Readability (Weight: 30%)
Measures how cleanly an LLM can parse and summarize information without hallucinations:
* **Paragraph Architecture**: Rewards concise paragraphs (optimal: 30–70 words per `<p>`).
* **Flesch Reading Ease**: Multilingual readability scoring calibrated via `textstat` (optimal target: 60–75).
* **Q&A Formats**: Identifies structured `FAQPage` JSON-LD schemas and conversational heading questions (e.g., `<h2>...?</h2>`).
* **Keyword Stuffing Penalty**: Deducts 20 points from the category score if keyword density exceeds 3.0%.

### C. Structure & Formatting (Weight: 20%)
Assesses structural hierarchy and data extractability:
* **Content Length**: Rewards deep, informative content (300 to 1500+ words).
* **Heading Hierarchy**: Checks for single `<h1>` usage and consistent `<h2>`/`<h3>` subheadings.
* **Information Density**: Rewards tables (`<table>`) and bulleted/numbered lists (`<ul>`, `<ol>`) for easy machine extraction.
* **Metadata Alignment**: Evaluates relevance and length of `<title>` and `<meta name="description">`.

### D. Technical Baseline (Weight: 10%)
Ensures technical accessibility for automated indexing:
* **HTTPS**: Encrypted connection protocol.
* **Page Load Speed**: Performance timing via browser execution.
* **Structured Data**: Detection of JSON-LD blocks (`<script type="application/ld+json">`) and Microdata (`itemscope`, `itemprop`).

---

## 🚦 3. Gatekeepers & Research Guardrails

1. **Critical Load Time Gatekeeper**:
   * If real browser rendering time exceeds **10.0 seconds**, the total score is set to `0` and classified as `poorly_geo_optimized`.
2. **Non-HTML Exclusion**:
   * Binary assets and PDF files are excluded from scoring and logged with an exclusion notice.
3. **The `robots.txt` AI Crawler Policy**:
   * While AI bot blocks (`GPTBot`, `ClaudeBot`, `Google-Extended`) are recorded (`robots_txt = 1`), they **do not reduce the score to 0**. This preserves empirical validity when analyzing pages that were nonetheless indexed or cited by search engines.
4. **Organic vs. AI Citation Separation**:
   * When evaluating organic search results (`result`), AI-specific indicators like `ai_semantic_similarity_percentage` and `ai_overview_word_count` are stored as `"N/A - Organic search result (no AI segment)"` rather than `0`, preventing statistical distortion in research evaluations.

---

## 🏷️ 4. Classification Thresholds

The calculated total score is mapped to qualitative classification tiers:

| Score Range | Classification Tag | Description |
| :--- | :--- | :--- |
| **75.0 – 100.0** | `highly_geo_optimized` | Optimal structure, high entity density, and clear factual evidence. |
| **45.0 – 74.9** | `probably_geo_optimized` | Good readability and baseline markup; some structural or trust gaps. |
| **20.0 – 44.9** | `probably_not_geo_optimized` | Hard to extract, missing structured data, or weak authority signals. |
| **0.0 – 19.9** | `poorly_geo_optimized` | Failed technical gatekeeper, missing content, or unstructured text. |

---

## 📋 5. Indicator Reference

The classifier writes the following variables to `classifier_indicator` and `classifier_result`:

| Indicator Key | Type | Description |
| :--- | :--- | :--- |
| `geo_classification` | `string` | Categorical rating tier. |
| `category_structure_formatting` | `float` | Category score (0–100). |
| `category_authority_trust` | `float` | Category score (0–100). |
| `category_semantics_readability` | `float` | Category score (0–100). |
| `category_technical_baseline` | `float` | Category score (0–100). |
| `geo_explanation` | `string` | Human-readable score breakdown and diagnostic warnings. |
| `ai_semantic_similarity_percentage` | `float / string` | Cosine similarity between AI snippet and source chunks. |
| `ai_overview_word_count` | `int / string` | Word count of the corresponding AI overview text. |
| `word_count` / `character_count` | `int` | Visible body text volume. |
| `p_count` / `avg_words_per_p` | `int / float` | Paragraph quantity and word density. |
| `readability_score` | `float` | Flesch Reading Ease score. |
| `schema_faq_present` / `semantic_qa_count` | `int` | Count of FAQ schemas and explicit `Q&A` headers. |
| `high_trust_links` | `int` | Links pointing to verified academic/governmental domains. |
| `organizations_count` | `int` | Count of distinct named entities detected via spaCy. |
| `percentage_count` / `year_count` | `int` | Distinct statistics and historical date citations. |
| `loading_time` | `float` | Page load time in seconds (via browser performance timing). |
| `robots_txt` | `int` | AI crawler blocking status (`1` = blocked, `0` = allowed). |
| `keyword_density` | `float` | Query keyword frequency ratio (penalty trigger above 3.0%). |

---

## ⚙️ 6. Dependencies & Installation

In addition to standard backend packages, the GEO Scorer requires NLP and sentence embedding libraries:

```bash
# CPU-optimized PyTorch build
pip install torch torchvision torchaudio --index-url [https://download.pytorch.org/whl/cpu](https://download.pytorch.org/whl/cpu)

# Sentence embeddings, NLP, and text statistics
pip install sentence-transformers scikit-learn spacy textstat langdetect seleniumbase beautifulsoup4 lxml

```

Note: SpaCy language models (e.g., `de_core_news_sm`, `en_core_web_sm`) are downloaded automatically on first run based on language detection.

---

## 🚀 7. Execution

The GEO Scorer integrates with the RAT runner architecture and executes automatically when activated in the database:

```bash
python3 classifier_runner.py

```

