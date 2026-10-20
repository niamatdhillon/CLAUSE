# 🧭 CLAUSE

**AI-Powered HR Policy Intelligence.** *Every policy. Clearly understood.*

CLAUSE is a local-first workspace for exploring HR policy documents. It brings together a conversational interface, a searchable policy library, metadata-filtered retrieval and source inspection, with optional local AI integrations.

## ✨ What is CLAUSE?

CLAUSE helps users find relevant information in workplace policy documents. Users can search in natural language, inspect matching excerpts and revisit saved conversations.

CLAUSE brings together:

- 📄 **Document Intelligence** — Upload and organise PDF, TXT and Markdown policy documents.
- 🔎 **Policy Retrieval** — Find relevant passages using lexical search, with optional local semantic retrieval.
- 💬 **Conversational Search** — Ask policy questions and keep discussions in saved conversations.
- 📚 **Source Evidence** — Inspect retrieved excerpts and available document and page details.
- 🏷️ **Metadata Filtering** — Filter retrieval by document category and publication year when available.
- 🗂️ **Policy Library** — Search, inspect, re-index and remove documents.
- 👤 **Accounts** — Register, sign in and sign out, with documents and conversations scoped to the signed-in account.
- 🛠️ **Admin Workspace** — Restrict document management, model diagnostics and retrieval evaluation to authorised accounts.

## 🚀 The Vision

Workplace policies often contain important information buried in lengthy documents.

CLAUSE explores how retrieval systems and language models can make policy information easier to find and understand by connecting natural-language questions with documentary evidence.

The goal is simple: **less time searching, clearer explanations and evidence users can inspect.**

## 🧠 How It Works

CLAUSE is designed around a retrieval-augmented generation (RAG) workflow:

1. **Ingest** — Extract text and available page information from uploaded policy documents.
2. **Chunk** — Split documents into overlapping passages. The current defaults are 900 characters with 140 characters of overlap.
3. **Index** — Store documents, passages and metadata in a local SQLite database. Optional local Sentence Transformers embeddings can add semantic retrieval.
4. **Retrieve** — Search for relevant passages, applying the selected document metadata filters.
5. **Generate** — When a local Ollama model is installed and reachable, use retrieved evidence to generate a grounded answer.
6. **Cite** — Show source references and expandable excerpts so users can inspect the supporting text.

When the local AI components are unavailable, CLAUSE can still retrieve and display evidence, but it does not generate a synthesized answer. It communicates that limitation instead of making one up.

## 🎨 Product Experience

CLAUSE centres on the conversation and policy evidence in a responsive blue-and-white interface.

Its design includes:

- A custom compass-inspired SVG identity.
- Midnight navy typography with cobalt and blue-violet accents.
- Subtle atmospheric lighting, layered surfaces and restrained glass effects.
- A focused chat experience with suggested questions and readable answers.
- Expandable source excerpts with available document metadata.
- Separate employee and restricted admin navigation.

## 🛠️ Technology Stack

The project uses:

- **Python** — Application server, document processing and retrieval logic.
- **HTML, CSS and JavaScript** — Custom responsive web interface.
- **SQLite** — Local accounts, documents, passages, optional vectors and conversation persistence.
- **PyMuPDF** — PDF text extraction.
- **Ollama** — Optional local language-model inference.
- **Sentence Transformers** — Optional local text embeddings using `all-MiniLM-L6-v2`.
- **Lexical retrieval** — Baseline search that works without the optional embedding model.

CLAUSE does not use Streamlit, ChromaDB, a paid model API or a hosted database in the current implementation.

## 🔬 Research & Evaluation

CLAUSE includes a small retrieval evaluation suite. Its current CSV contains **10 checks** against the synthetic sample policies: nine answerable questions with expected-source hits and one unanswerable control.

These checks measure retrieval behavior only. They are not a measure of answer accuracy, citation faithfulness or performance on a broad policy corpus. Run the evaluation with:

```sh
python3 evaluate.py
```

The automated unit suite can be run with:

```sh
python3 -m unittest discover -s tests -v
```

The audited build passed 11 unit tests, JavaScript syntax validation, an HTTP smoke flow and a local browser walkthrough. Ollama and the embedding model were unavailable during that audit, so local answer generation and semantic retrieval still need setup and verification.

## 🚧 Current Status

CLAUSE is an **internship demonstration project** exploring local RAG for HR policy search.

The application supports local accounts, document ingestion, metadata-filtered retrieval, source inspection, saved conversations and restricted admin tools. Its three included policy documents are synthetic examples—not policies from a real employer.

Data persists in local SQLite and document files, including across browser closure and local server restarts. It is not cloud persistence, and the current application has not been deployed publicly. The local account system has no email verification or password reset. Do not use the demo with confidential employee data or expose it publicly without appropriate security and privacy review.

Local Ollama generation and semantic retrieval depend on installing and configuring their respective components. Until then, CLAUSE operates in retrieval-only mode.

## 🌟 Project Goal

To demonstrate how document retrieval and locally run AI models can make policy information more searchable, understandable and traceable to its source.

**CLAUSE — Every policy. Clearly understood.**
