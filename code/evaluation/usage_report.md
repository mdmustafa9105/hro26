# Token Usage & Computational Cost Report

## 1. Overview & Execution Architecture

This report details the computational and token usage for the Deletion-Audit Engine across all 518 evaluation requests in `dataset/deletion_requests.csv` that generated `output.csv`.

The final evaluation pipeline runs entirely locally, deterministically, and offline without calling any external commercial LLM APIs or cloud inference services:
1. **Multilingual Request Classification**: Implemented via a deterministic rule-based and regular-expression intent classifier (`RequestClassifier`) that detects deletion authorization versus access, export, or correction requests across multiple languages.
2. **Document & Image Parsing**: Uses `pypdf` for local text extraction from PDF documents and Windows Media OCR via `winsdk` (`winsdk.windows.media.ocr.OcrEngine`) for application screenshots.
3. **Structured Evidence Correlation**: Uses deterministic multi-system indexing (SQLite SQL snapshots, JSON manifests, and distributed service logs) with trace-ID and entity linking.

---

## 2. Model Inference & Token Accounting

During the final full-dataset evaluation run that produced `output.csv`, zero cloud model calls were executed:

| Metric | Evaluation Engine Value |
| :--- | :--- |
| **Model Providers** | None (Local deterministic engine) |
| **Model Names** | None |
| **Model-Call Counts** | **0** |
| **Input Tokens** | **0** |
| **Output Tokens** | **0** |
| **Total Tokens** | **0** |
| **Average Tokens Per Request** | **0.0** |
| **Estimated Total Inference Cost** | **$0.00** |
| **Estimated Cost Per Request** | **$0.00** |

---

## 3. Development Tooling Note

During the engineering, iterative design, debugging, and audit of the pipeline, interactive AI developer assistants were utilized:
- **Harnesses & Environments**: OpenCode and Google Antigravity.
- **Underlying Models**: Gemini 3.8 Flash (High) and Claude coding models accessed via developer IDE tooling.

Because these tools served as developer-facing pairing and coding assistants rather than runtime inference components of the pipeline, no artificial token numbers or costs are assigned to the evaluation run itself. The generated submission artifacts and evaluation script execute 100% locally and cost-free.
