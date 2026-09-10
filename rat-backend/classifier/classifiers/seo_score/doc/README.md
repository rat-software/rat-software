# RAT: Traditional SEO Scorer

The **SEO Scorer** is an analytical module for the RAT backend designed to evaluate classical Search Engine Optimization (SEO) metrics for web documents. 

While the GEO scorer focuses on Generative AI systems, the SEO Scorer evaluates how well a page is optimized for traditional search engine algorithms (like the classic Google PageRank and crawler-based heuristics).

---

## 📊 1. The SEO Scoring Model

The scorer calculates a total score between **0 and 100 points** based on four weighted categories, with an additional bonus applied for detected analytics tools:

$$\\text{Total Score} = (0.35 \\cdot \\text{Tech}) + (0.30 \\cdot \\text{Content}) + (0.20 \\cdot \\text{UX}) + (0.15 \\cdot \\text{Meta}) + \\text{Analytics Boost}$$



```
                             ┌──────────────────────────────────────────────────────────┐
                             │                 Total SEO Score (0-100)                  │
                             └────────────────────────────┬─────────────────────────────┘
                                                          │
     ┌────────────────────────────┬───────────────────────┴───────────────┬────────────────────────────┐
     │ (35%)                      │ (30%)                                 │ (20%)                      │ (15%)

```

┌────────┴─────────────┐   ┌──────────┴───────────────┐            ┌──────────┴───────────────┐ ┌──────────┴─────────────┐
│    Technical SEO     │   │     Content Quality      │            │     User Experience      │ │     Meta Elements      │
├──────────────────────┤   ├──────────────────────────┤            ├──────────────────────────┤ ├──────────────────────┤
│ • HTTPS & Canonical  │   │ • Keyword Optimization   │            │ • Page Load Time         │ │ • Title Tag            │
│ • Robots.txt         │   │ • Content Length         │            │ • Mobile Viewport        │ │ • Meta Description     │
│ • Sitemap            │   │ • Heading Structure      │            │ • Navigation Analysis    │ │ • Social Tags (OG)     │
│ • Structured Data    │   │ • Link Quality           │            │ • SSL Security           │ │ • H1 Presence          │
│ • Caching Tools      │   │ • Image Optimization     │            │ • Micro Tools            │ └──────────────────────┘
└──────────────────────┘   └──────────────────────────┘            └──────────────────────────┘

```

---

## 🧮 2. Scoring Categories & Logic (Concrete Thresholds)

### A. Technical SEO (Weight: 35%)
Evaluates the foundational technical configuration that allows search engines to crawl and index the site:
* **HTTPS**: Checks for a secure connection.
* **Indexability & Crawling**: Checks for `robots.txt` and `sitemap`.
* **Canonicalization**: Identifies `canonical` tags to prevent duplicate content.
* **Structured Data**: Looks for `application/ld+json` or `schema.org`.
* **Tool Bonuses**: Awards extra points (+10 for caching tools, +5 for micro tools) based on detected plugins.

### B. Content Quality (Weight: 30%)
Evaluates the depth, structure, and relevance of the on-page content:
* **Content Length**: Articles with 1500+ words yield a perfect 100 points. The tiers descend to 1000+ words (80 points), 500+ words (60 points), and 300+ words (40 points), scaling linearly for word counts below 300.
* **Heading Structure**: The system requires exactly one `<h1>` tag to award the base 40 points. Additional points are awarded for `<h2>`/`<h3>` usage (+30 points) and `<h4>`-`<h6>` usage (+30 points).
* **Link Quality**: The ideal internal-to-total link ratio is 60%–80% (+50 points). Pages are additionally rewarded for having 10 or more total links (+50 points).
* **Keyword Optimization**: Checks for the exact keyword in the URL, Title, Meta Description, and Headers (+25 points each). Uses exact phrase matching across Unicode word characters for density calculations[cite: 12].
* **Image Optimization**: Calculates the exact percentage of `<img>` tags on the page that successfully utilize an `alt` attribute.
* **Missing Meta Penalty**: Deducts 20 points from the content score if basic meta elements (title/description) are missing.

### C. User Experience (UX) (Weight: 20%)
Assesses factors that impact how a user interacts with the page:
* **Page Load Speed**: Measured via an undetectable headless Chrome browser (Selenium) using the `domContentLoadedEventEnd` metric to capture the exact moment text and HTML are ready, with a strict 10-second timeout[cite: 12]. Fast loading (<2s) awards 40 points, medium (2-3s) awards 30 points, and acceptable (3-4s) awards 20 points.
* **Navigation**: Awards points based on the presence of structural HTML5 elements: `<nav>`/`<menu>` (+40 points), `<footer>` (+30 points), and `<form>` (+30 points).
* **Mobile Friendliness & Security**: Checks for mobile `viewport` meta tags (+20 points) and enforces HTTPS security (+20 points).

### D. Meta Elements (Weight: 15%)
Evaluates the presence and quality of HTML head elements:
* **Title Optimization**: The optimal title length is exactly 50–60 characters (100 points). Scores drop to 80 points for 40–70 characters, 60 points for 30–80 characters, and 40 points for any other length. A 30-point penalty is strictly applied for generic titles like 'home', 'page', or 'untitled'.
* **Meta Description**: The optimal length is 150–160 characters (100 points), dropping in tiers down to 40 points for extreme lengths. Generic descriptions like 'website description' trigger a 30-point penalty.
* **Social Tags**: Awards 50 points for the presence of Open Graph (`og:`) tags and another 50 points for Twitter card (`twitter:`) tags.
* **H1 Tag**: Enforces the presence of an `<h1>` tag; penalizes by 10 points if missing.

### 🌟 Bonus and Overrides
* **Analytics Boost**: Adds +5 points to the final score if analytics plugins are detected.
* **Perfect Score Override**: If explicit SEO plugins (e.g., Yoast, RankMath) are detected via `tools_seo`, the module assumes a highly optimized page and immediately returns a perfect score of 100.

---

## 🚦 3. Gatekeepers & Guardrails

1. **Non-HTML Exclusion**:
   * Documents like PDFs or non-HTML content types are automatically excluded from SEO scoring, logged with an `excluded` status and an `exclusion_reason`.
2. **HTTP Errors**:
   * Any result with a non-200 status code or an explicit `error_code` is skipped during processing.

---

## 🏷️ 4. Classification Thresholds

The calculated total score maps to the following classical SEO optimization tiers:

| Score Range | Classification Tag | Description |
| :--- | :--- | :--- |
| **75.0 – 100.0** | `most_probably_optimized` | Excellent technical setup, strong content, and complete metadata. |
| **45.0 – 74.9** | `probably_optimized` | Good baseline SEO, but missing some technical or content enhancements. |
| **20.0 – 44.9** | `probably_not_optimized` | Weak content, poor loading speeds, or missing key meta elements. |
| **0.0 – 19.9** | `most_probably_not_optimized` | Critical SEO failures (e.g., missing titles, no HTTPS, extremely slow). |

---

## 📋 5. Indicator Reference

The classifier writes the following variables to the `classifier_indicator` and `classifier_result` tables in the database:

| Indicator Key | Type | Description |
| :--- | :--- | :--- |
| `seo_classification` | `string` | Categorical rating tier. |
| `category_technical_seo` | `float` | Category score (0–100). |
| `category_content_quality` | `float` | Category score (0–100). |
| `category_user_experience` | `float` | Category score (0–100). |
| `category_meta_elements` | `float` | Category score (0–100). |
| `analysis_explanation` | `string` | Human-readable score breakdown and tool detection notices. |
| `title_score` / `description_score` | `float` | Quality scores for title and description tags. |
| `internal_links` / `external_links` | `int` | Link counts extracted from the HTML. |
| `tools_analytics` / `tools_seo` | `list` | Detected technology stacks and plugins. |
| `loading_time` | `float` | Page load time. |
| `https` / `robots_txt` / `sitemap` | `bool` | Technical configuration flags. |
| `keyword_optimization_score` | `float` | Score based on target query placement. |

---

## 🚀 6. Execution

The SEO Scorer is a subclass of the main `Classifier` framework. It is automatically loaded and executed by the RAT task runner when activated:

```bash
python3 classifier_runner.py

```