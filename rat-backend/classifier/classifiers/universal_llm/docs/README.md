# Universal LLM Classifier

The `UniversalLlm` classifier enables automated, prompt-driven analysis across all scraped sources (organic web pages, AI search overviews, chatbot transcripts, and search citation links) using local or cloud Large Language Models.

---

## 🧠 Overview & Key Features

* **Multi-Provider Support**: Connects via OpenAI-compatible endpoints (`/v1`) to local instances (Ollama, vLLM, LocalAI) or cloud providers (OpenAI, OpenRouter, Groq, Mistral, Together AI).
* **Per-Study Configurable Tasks**: Analysis tasks, prompts, and models are configured per study in the database.
* **Atomic Distributed Locking**: Prevents race conditions across multi-worker server clusters using `db.lock_llm_indicator()`.
* **Duplicate Detection**: Skips re-querying identical source pages across studies/results.
* **Strict JSON Extraction**: Enforces strict JSON return values with regex fallback extraction and schema sanitation.
* **Secure API Key Storage**: Supports Fernet-encrypted keys using an environment master secret.

---

## ⚙️ Configuration Format

LLM tasks are stored as a JSON array within the study configuration (`db.get_study_llm_config(study_id)`).

### Example Configuration Schema

```json
[
  {
    "active": true,
    "display_name": "sentiment_and_topic",
    "target_type": "all",
    "base_url": "[http://127.0.0.1:11434/v1](http://127.0.0.1:11434/v1)",
    "model": "llama3.1:8b",
    "api_key": "",
    "max_context": 4000,
    "max_tokens": 300,
    "system_prompt": "You are a research assistant analyzing search results.",
    "prompt": "Evaluate the following text for the search query '{query}'. Return a JSON object with keys 'topic' (string) and 'sentiment' ('positive', 'neutral', or 'negative')."
  }
]

```

### Configuration Parameters

| Parameter | Type | Description |
| --- | --- | --- |
| `active` | `bool` | Enables or disables task execution. |
| `display_name` | `string` | Becomes the indicator prefix: `LLM_<display_name>`. |
| `target_type` | `string` | Filter targets: `all`, `organic`, `ai_overview`, `chatbot`, or `ai_source`. |
| `base_url` | `string` | OpenAI-compatible endpoint URL (e.g., `http://127.0.0.1:11434/v1` or `https://api.openai.com/v1`). |
| `model` | `string` | Model identifier (e.g., `llama3.2`, `gpt-4o-mini`, `mistral-small`). |
| `api_key` | `string` | Raw API key or Fernet-encrypted token (`gAAAA...`). |
| `max_context` | `int` | Character limit for extracted source text passed to the prompt. |
| `max_tokens` | `int` | Maximum tokens allowed for LLM output completion. |
| `system_prompt` | `string` | Base instructions prepended before strict JSON guardrails. |
| `prompt` | `string` | Task prompt. Supports `{query}` string interpolation. |

---

## 🔐 API Key Encryption Setup

To protect API tokens stored in the database, workers decrypt keys on the fly:

1. Generate an encryption key or define a strong string.
2. Add `LLM_SECRET_KEY` to your `.env` file on every worker node:
```env
LLM_SECRET_KEY=your-super-secret-master-key-here

```


3. If an encrypted token (`gAAAA...`) is retrieved from the database, `UniversalLlm` derives a Fernet key using SHA-256 and decrypts it dynamically during execution.

---

## 🛡️ Response Handling & Output

The classifier enforces valid JSON output:

1. **JSON Mode**: Sends `response_format: {"type": "json_object"}` where supported.
2. **Regex Parsing**: Isolates the JSON object between `{` and `}` if extraneous commentary is returned.
3. **Database Storage**: The validated JSON string is saved to `classifier_indicator` under `LLM_<display_name>`.

### Standard Status Codes in Indicators

* `source_failed`: The source had no text content or returned an HTTP error.


* `error_api`: The endpoint failed or refused the connection after 3 retries.
* `error_timeout`: The LLM request timed out (>30s).
* `error_invalid_json`: The model failed to provide valid JSON syntax after 3 attempts.

---

## 🚀 Execution

The LLM classifier is invoked automatically by the main runner:

```bash
python3 classifier_runner.py

```

*For local Ollama instances, the classifier automatically issues keep-alive unloads (`keep_alive: 0`) between large batches to free VRAM for subsequent jobs.*