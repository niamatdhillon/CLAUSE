# CLAUSE

**AI-Powered HR Policy Intelligence** · *Every policy. Clearly understood.*

CLAUSE is a local-first policy research workspace. It supports accounts, policy document ingestion, metadata filters, saved conversations, source inspection, and optional local AI using Ollama and Sentence Transformers. It does not use a paid API provider.

## Run locally

Python 3.9–3.12:

```sh
python3 -m pip install -r requirements.txt
cp .env.example .env
# Edit .env, then load it into this shell:
set -a; . ./.env; set +a
python3 app.py
```

Open http://127.0.0.1:8501 and create an account. Each new account receives three clearly labelled **synthetic examples** (remote work, leave and grievance), authored for this demo and not representative of an employer. Users can ask about their own indexed library. An administrator can upload PDF, TXT or Markdown files (10 MB maximum), retry indexing and remove stored source files. Local persistence is in `data/clause.sqlite3` and account directories under `data/documents/`.

## Local AI setup (optional)

The audited environment did **not** have the Ollama executable/service, Sentence Transformers, PyTorch, a cached embedding model, or any model credentials installed. The application therefore runs with lexical evidence search only. No LLM synthesis was claimed or verified in that environment. When Ollama or the embedding model is unavailable, the employee experience says answer synthesis is unavailable and directs the user to inspect the evidence or contact an administrator.

1. Install Ollama for your operating system from [ollama.com/download](https://ollama.com/download), start its local service, and download a small chat model:

   ```sh
   ollama pull qwen2.5:3b
   ollama list
   ```

2. Install the optional local embedding dependency:

   ```sh
   python3 -m pip install -r requirements-embeddings.txt
   ```

3. Download/cache the Sentence Transformers model once on a machine allowed to access the model host, then run CLAUSE offline with its local cache:

   ```sh
   python3 -c 'from sentence_transformers import SentenceTransformer; SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")'
   ```

   The first embedding model load downloads model files unless they are already cached. To use a pre-downloaded model directory, set `CLAUSE_EMBEDDING_PATH` to it. The app sets `local_files_only=True`; it does not fetch embeddings from a hosted API at question time.

4. Configure and restart CLAUSE:

   ```sh
   export OLLAMA_HOST=http://127.0.0.1:11434
   export OLLAMA_MODEL=qwen2.5:3b
   export CLAUSE_ADMIN_EMAILS=you@example.com
   python3 app.py
   ```

   Register/sign in using the allowlisted email to access **Admin workspace**. Admin diagnostics show Ollama reachability/model availability and whether the local embedding package/model files are available. Existing documents need **Retry indexing** to generate vectors after embeddings are first configured. The retriever uses a local MiniLM semantic score when matching vectors exist, combined with lexical coverage; otherwise it remains a lexical baseline. Chunking starts at 900 characters with 140-character overlap. These are pragmatic defaults, not a claimed optimum.

The local Ollama chat request receives the question, recent conversation context and retrieved policy excerpts. The system prompt treats question/history/excerpts as untrusted data and instructs the model to use only retrieved policy evidence. Citation labels are checked against the retrieved evidence. Ollama failures are returned as actionable errors. This application does not silently fall back to an external or paid provider.

## Accounts and access control

- This is a local demonstration account system: salted PBKDF2-HMAC-SHA256 password hashes and opaque, hashed, HttpOnly, SameSite cookies with a 14-day expiry.
- Admin status comes only from the server-side `CLAUSE_ADMIN_EMAILS` allowlist. Employee-supplied role fields are ignored. Upload, re-index, remove, model diagnostics, settings and evaluation endpoints check the authenticated user's admin role server-side.
- Document and conversation queries are scoped by owner ID. This is local account isolation verified by the HTTP smoke test, not managed cloud authentication/RLS.
- There is no email verification or password reset, and no independent security audit or encryption-at-rest setup. Do not expose this local demo publicly for confidential HR records. Use HTTPS (`COOKIE_SECURE=1`), durable encrypted storage, backups, rate limiting, a managed identity provider and a privacy/security review before any sensitive deployment.

## Persistence

The app persists documents, extracted passages, vector records, user accounts and conversations on its local filesystem/SQLite database. Closing the browser or restarting the local server preserves them. This is **not cloud persistence** and is not durable on a host with ephemeral disk. Set `CLAUSE_DATA_DIR` to a backed-up persistent volume for a private long-running host. No external account isolation or cloud backup is configured.

## Corpus and provenance

Three included policies are synthetic examples, not real workplace rules or external documents. User uploads retain their submitted filename, category, optional publication year, and `User upload` provenance. No third-party corpus is redistributed.

## Evaluation

`evaluation/results.csv` contains ten small retrieval checks against synthetic sample documents: 9 answerable expected-source hits and one unanswerable control. This is a retrieval hit check, not answer accuracy, citation faithfulness, or generalization. Admin workspace labels the sample size/scope explicitly. Reproduce the check with:

```sh
python3 evaluate.py
```

## Tests

```sh
python3 -m unittest discover -s tests -v
```

For account, upload, conversation persistence and isolation flows, start CLAUSE with isolated data and an admin allowlist in one terminal:

```sh
CLAUSE_DATA_DIR=/tmp/clause-audit-data CLAUSE_ADMIN_EMAILS=clause-admin-smoke@example.test python3 app.py
```

Then run in another terminal:

```sh
python3 tests/http_smoke.py
```

## Deployment limitations

No public deployment or cloud storage/auth configuration is present. The app requires a long-running Python host with durable filesystem storage, a reachable local Ollama service, and a local embedding model cache. Do not use an ephemeral serverless filesystem. Do not claim a public service is persistent or private without independently configuring and testing those services.
