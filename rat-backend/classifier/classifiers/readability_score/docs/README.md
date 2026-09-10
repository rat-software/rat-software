# RAT: Readability Scorer

The **Readability Scorer** is a dedicated analytical module for the RAT backend that calculates the linguistic complexity and readability of extracted web text
By determining how easily a human (or an AI language model) can process a document, this classifier provides a critical metric for content quality analysis. It leverages the Flesch Reading Ease formula and dynamically adjusts its algorithms based on automatic language detection[cite: 16].

---

## 🧠 1. How It Works

The readability scoring process follows a strict text extraction and analysis pipeline[cite: 15, 16]:

1. **Text Extraction & Cleaning**: The module inherits from the base `Classifier` and uses its text extraction capabilities to strip away all HTML, `<script>`, and `<style>` tags to isolate the main body text[cite: 15, 16].
2. **Length Validation**: Before running complex NLP tasks, the text is evaluated for length. Documents with fewer than **100 words** are immediately skipped[cite: 16].
3. **Language Detection**: The `langdetect` library evaluates the text block to determine the primary language[cite: 16]. 
4. **Score Calculation**: Using the `textstat` library, the Flesch Reading Ease score is calculated based on syllable counts, word lengths, and sentence structures specific to the detected language[cite: 16].

---

## 🧮 2. The Flesch Reading Ease Score

The module outputs a numerical float representing the Flesch Reading Ease[cite: 15]. The standard interpretation of the score is as follows:

* **90–100**: Very Easy (5th-grade level)
* **80–89**: Easy (6th-grade level)
* **70–79**: Fairly Easy (7th-grade level)
* **60–69**: Standard / Plain English (8th-9th-grade level) - *Often optimal for AI extractions*
* **50–59**: Fairly Difficult (10th-12th-grade level)
* **30–49**: Difficult (College level)
* **0–29**: Very Difficult (University graduate level / Academic papers)

---

## 🚦 3. Gatekeepers & Guardrails

To prevent calculation errors and invalid data, the module enforces the following strict constraints[cite: 15, 16]:

* **Minimum Word Count**: If the cleaned text contains fewer than **100 words**, the analysis is aborted with the error `text_too_short_or_unspaced`. The classification result is marked as `skipped_incompatible`[cite: 15, 16].
* **Language Support**: Currently, the analyzer explicitly supports **English (`en`)** and **German (`de`)** text[cite: 16]. If any other language is detected, it returns a `Language '[lang]' not supported` error, marking the result as `skipped_incompatible`[cite: 15, 16].
* **Math/Syllable Exceptions**: If the text contains malformed words that trigger "division by zero" or "syllable" calculation errors in `textstat`, the classifier catches the exception and outputs `"N/A"` for the score, marking the classification result as `language_not_supported`[cite: 15].

---

## 📋 4. Database Indicators

The classifier writes the following variables to the `classifier_indicator` and `classifier_result` tables in the database[cite: 15]:

| Indicator Key | Type | Description |
| :--- | :--- | :--- |
| `Reading Ease` | `float / string` | The calculated Flesch Reading Ease score (e.g., `65.42`). Outputs `"N/A"` if calculation fails mathematically[cite: 15]. |
| `exclusion_reason` | `string` | The specific reason a document was skipped (e.g., `text_too_short_or_unspaced`, `Language 'fr' not supported`)[cite: 15, 16]. |
| `reason` | `string` | Captures broader extraction errors or general Python exceptions caught during execution[cite: 15]. |

---

## 🚀 5. Execution

The Readability Scorer is a subclass of the main `Classifier` framework. It is automatically loaded and executed by the RAT task runner when activated[cite: 15]:

```bash
python3 classifier_runner.py
```
## 🧠 1. How It Works

The readability scoring process follows a strict text extraction and analysis pipeline[cite: 15, 16]:

1. **Text Extraction & Cleaning**: The module inherits from the base `Classifier` and uses its text extraction capabilities to strip away all HTML, `<script>`, and `<style>` tags to isolate the main body text[cite: 15, 16].
2. **Length Validation**: Before running complex NLP tasks, the text is evaluated for length. Documents with fewer than **100 words** are immediately skipped[cite: 16].
3. **Language Detection**: The `langdetect` library evaluates the text block to determine the primary language[cite: 16]. 
4. **Score Calculation**: Using the `textstat` library, the Flesch Reading Ease score is calculated based on syllable counts, word lengths, and sentence structures specific to the detected language[cite: 16].

---

## 🧮 2. The Flesch Reading Ease Score

The module outputs a numerical float representing the Flesch Reading Ease[cite: 15]. The standard interpretation of the score is as follows:

* **90–100**: Very Easy (5th-grade level)
* **80–89**: Easy (6th-grade level)
* **70–79**: Fairly Easy (7th-grade level)
* **60–69**: Standard / Plain English (8th-9th-grade level) - *Often optimal for AI extractions*
* **50–59**: Fairly Difficult (10th-12th-grade level)
* **30–49**: Difficult (College level)
* **0–29**: Very Difficult (University graduate level / Academic papers)

---

## 🚦 3. Gatekeepers & Guardrails

To prevent calculation errors and invalid data, the module enforces the following strict constraints[cite: 15, 16]:

* **Minimum Word Count**: If the cleaned text contains fewer than **100 words**, the analysis is aborted with the error `text_too_short_or_unspaced`. The classification result is marked as `skipped_incompatible`[cite: 15, 16].
* **Language Support**: Currently, the analyzer explicitly supports **English (`en`)** and **German (`de`)** text[cite: 16]. If any other language is detected, it returns a `Language '[lang]' not supported` error, marking the result as `skipped_incompatible`[cite: 15, 16].
* **Math/Syllable Exceptions**: If the text contains malformed words that trigger "division by zero" or "syllable" calculation errors in `textstat`, the classifier catches the exception and outputs `"N/A"` for the score, marking the classification result as `language_not_supported`[cite: 15].

---

## 📋 4. Database Indicators

The classifier writes the following variables to the `classifier_indicator` and `classifier_result` tables in the database[cite: 15]:

| Indicator Key | Type | Description |
| :--- | :--- | :--- |
| `Reading Ease` | `float / string` | The calculated Flesch Reading Ease score (e.g., `65.42`). Outputs `"N/A"` if calculation fails mathematically[cite: 15]. |
| `exclusion_reason` | `string` | The specific reason a document was skipped (e.g., `text_too_short_or_unspaced`, `Language 'fr' not supported`)[cite: 15, 16]. |
| `reason` | `string` | Captures broader extraction errors or general Python exceptions caught during execution[cite: 15]. |

---

## 🚀 5. Execution

The Readability Scorer is a subclass of the main `Classifier` framework. It is automatically loaded and executed by the RAT task runner when activated[cite: 15]:

```bash
python3 classifier_runner.py
```