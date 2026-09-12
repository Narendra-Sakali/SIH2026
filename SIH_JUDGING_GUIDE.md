# TransformAI: SIH Internal Hackathon Judging Guide

## 1. One-line pitch

TransformAI is a privacy-oriented, locally deployable AI content engine that converts one source document and one imperfect user request into a refined prompt and multiple audience-specific communication artefacts.

## 2. Problem statement

Government, research, security and institutional teams often have the information, but not the time to convert it into the right communication format. The same report may need to become an executive brief, public advisory, social-media post, presentation, infographic, video package and detailed report.

The current process is manual, repetitive and inconsistent. Users may also write incomplete prompts, which causes generic or poorly structured AI output.

## 3. Proposed solution

TransformAI provides a guided workflow:

1. Upload a PDF, DOCX or TXT file, or paste source material.
2. Enter a raw or incomplete request.
3. Select audience, tone, language, objective and detail level.
4. Ask the local AI model to refine the request into a clear, actionable prompt.
5. Select one or more output formats.
6. Generate all selected artefacts in one model call and view them in separate tabs.

The system keeps the source context, prompt intent and communication requirements together throughout the workflow.

## 4. Primary users and use cases

### Government and public administration

- Convert policy notes into executive summaries and public advisories.
- Prepare decision-maker briefs from long reports.
- Translate official communication into Hindi or Telugu.

### Security and intelligence communication

- Turn incident descriptions into structured advisories.
- Prepare internal briefs, risk communication and awareness content.
- Keep sensitive source material on a locally controlled machine when required.

### Education and research

- Convert research papers into presentations, reports and student-friendly explanations.
- Produce multiple communication levels from the same evidence.

### Emergency and public-awareness teams

- Create concise warnings, social posts and video scripts from a situation report.
- Adapt tone and audience without rewriting the source manually.

### Institutional communication teams

- Generate consistent LinkedIn posts, X threads, reports and presentations from approved source material.
- Reduce repetitive drafting work while retaining human review before publication.

## 5. What is implemented today

### Frontend

- Single-page HTML/CSS/JavaScript interface.
- File upload for `.pdf`, `.docx` and `.txt`.
- Manual source-text entry.
- Audience, tone, language, objective and detail controls.
- Multi-select output formats.
- Prompt refinement step with copy action.
- Output tabs and download action in the interface.

### Backend

- FastAPI service in `backend/main.py`.
- `POST /api/refine-prompt` for prompt improvement.
- `POST /api/transform` for multi-output generation.
- `GET /health` and `GET /` for service status.
- PDF extraction through `pypdf`.
- DOCX extraction through `python-docx`.
- TXT extraction through Python file I/O.
- CORS enabled for the local frontend.
- Uploaded files stored in `backend/uploads/`.

## 6. Architecture

```text
User
  |
  v
Frontend: index.html
  |  FormData: source, file, settings, raw/refined prompt
  v
FastAPI backend
  |
  +--> PDF/DOCX/TXT text extraction
  |
  +--> Context builder: user text + uploaded text
  |
  +--> Prompt refinement request
  |       |
  |       v
  |   Ollama local API
  |       |
  |       v
  |   Qwen3 1.7B
  |
  +--> Multi-output generation request
          |
          v
      Parser separates labelled outputs
          |
          v
Frontend output tabs
```

## 7. Models and how they are used

### Current model

- Model: `qwen3:1.7b`
- Runtime: Ollama
- Access method: OpenAI-compatible client pointed at `http://localhost:11434/v1`
- Location: local machine, rather than a hosted cloud inference endpoint
- Generation settings in code: temperature `0.4`; refinement limit `1000` tokens; transformation limit `2500` tokens

### Is the model trained in this project?

No. The repository currently does **not** train, fine-tune or update Qwen weights. It uses a pretrained Qwen model supplied through Ollama.

The project improves task performance through:

- Structured system instructions.
- A two-stage prompt workflow.
- Explicit audience, tone, language, objective and detail controls.
- Source-document context injection.
- Output-specific instructions.
- Mandatory output headings so the response can be parsed.
- A single generation call for all selected artefacts, reducing repeated inference.

This should be described to judges as **prompt engineering and controlled inference**, not model training.

### Why a small local model?

Qwen3 1.7B is suitable for an offline prototype because it is lightweight, fast to run on development hardware and adequate for controlled transformation tasks. A larger model can be substituted through Ollama if quality or context-length testing shows a need.

## 8. Prompting and inference flow

### Stage 1: Prompt refinement

The backend sends the raw request, source context and selected controls to Qwen with instructions to:

- Preserve the user's intent.
- Remove ambiguity.
- Add missing output requirements.
- Include audience, tone, language and objective.
- Return only the refined prompt.

### Stage 2: Content transformation

The refined prompt and source context are sent with one instruction block per selected output. The model is required to:

- Generate every requested format.
- Use exact section headings such as `[Executive Summary]`.
- Use source material where appropriate.
- Avoid inventing important facts.
- Return only generated content.

`parse_outputs()` separates the labelled sections and returns them to the frontend as a JSON object.

## 9. Functional requirements

- Accept PDF, DOCX and TXT source files.
- Accept pasted source content.
- Reject unsupported file extensions.
- Refine incomplete prompts before generation.
- Support configurable audience, tone, language, objective and detail level.
- Generate multiple output formats in one workflow.
- Return structured output sections to the UI.
- Expose health status for local deployment checks.
- Show actionable errors when the AI runtime is unavailable.

## 10. Non-functional requirements

- **Privacy:** local inference through Ollama; no required external AI API key.
- **Usability:** guided four-step workflow and selectable output formats.
- **Performance:** lightweight model and one generation call for multiple outputs.
- **Maintainability:** output instructions are isolated in `get_output_instruction()`.
- **Extensibility:** new formats can be added to the instruction map and frontend options.
- **Reliability:** source extraction, validation and model errors are handled at the API boundary.
- **Language support:** English, Hindi and Telugu controls are exposed in the UI.

## 11. Demo script for the judging panel

Use a short security or public-policy report as the input. A reliable live sequence is:

1. Open the frontend and show that the AI engine is local.
2. Upload `thanmay.docx` or paste a short incident/report summary.
3. Enter: `make this useful for officials and the public`.
4. Select `Government Officials`, `Professional`, `English`, and `Brief Decision Makers`.
5. Select `Executive Summary`, `Advisory`, `Presentation` and `LinkedIn Post`.
6. Click **Improve Prompt** and show the refined prompt.
7. Click **Transform Content**.
8. Move through the output tabs and explain that one source has become multiple controlled artefacts.
9. Change the language to Hindi or Telugu and demonstrate audience adaptation if time permits.

## 12. Suggested 90-second explanation

> TransformAI addresses a practical communication bottleneck. Teams receive reports and incident information, but converting the same source into different formats for officials, technical users and the public takes time and often produces inconsistent results. Our system accepts a document or pasted text, understands an incomplete request, refines it into a structured prompt, and generates multiple communication artefacts in one workflow. The solution runs a pretrained Qwen3 1.7B model locally through Ollama, so the prototype does not require a cloud AI key and is better suited to sensitive institutional material. We are not claiming that the model is trained by this repository; our current contribution is controlled prompt engineering, document context extraction, output constraints and a usable multi-format workflow. The architecture is modular, so future versions can add retrieval, evaluation datasets, fine-tuning and deployment-grade access controls.

## 13. What makes the solution valuable

- One source, many communication formats.
- Better results from poor or incomplete user prompts.
- Local-first inference for sensitive documents.
- Audience and language adaptation.
- Reduced repetitive drafting effort.
- Clear separation between source context, prompt refinement and final generation.

## 14. Current limitations to state honestly

- The prototype has no authentication or role-based access control.
- Uploaded files are stored locally and are not automatically deleted.
- Scanned PDFs require OCR, which is not currently included.
- Generated text still requires human fact-checking and approval.
- There is no automated quality, hallucination or bias benchmark yet.
- The current repository has no training or fine-tuning dataset.
- The frontend is a static page and the backend is intended for local/demo deployment.

## 15. Roadmap after the internal hackathon

### Phase 1: production hardening

- Add authentication, role-based access and audit logs.
- Validate file size and content, sanitize filenames and delete temporary files.
- Add structured logging and configurable CORS.
- Add OCR for scanned documents.

### Phase 2: evidence-grounded generation

- Add chunking and embeddings.
- Store document vectors in a local vector database.
- Retrieve only relevant source passages for each output.
- Add citations or source references to generated artefacts.

### Phase 3: evaluation and model adaptation

- Build a representative, permissioned dataset of source-to-output examples.
- Define metrics for factuality, format compliance, language quality, latency and reviewer acceptance.
- Compare prompt-only inference with parameter-efficient fine-tuning such as LoRA when data and compute justify it.
- Keep a human review loop and regression test set for every model or prompt change.

## 16. Setup for a live demo

### Start Ollama and install the model

```powershell
ollama serve
ollama pull qwen3:1.7b
```

### Install backend dependencies

```powershell
cd backend
python -m pip install -r requirements.txt
```

### Start the API

```powershell
python main.py
```

The API runs at `http://127.0.0.1:8000`. Open `frontend/index.html` in a browser after the backend and Ollama are running.

## 17. Likely judge questions

**What is novel here?**

The focus is an end-to-end local-first workflow that turns unstructured source material and weak requests into several audience-specific deliverables, with an explicit prompt-refinement stage and structured output parsing.

**Why not call a cloud model?**

Institutional and security-related documents may not be allowed to leave a controlled environment. Ollama enables a local deployment path and avoids a mandatory external API key.

**Where is the training data?**

There is no training data in the current prototype. Qwen is pretrained. We use prompt engineering and contextual conditioning today; a permissioned domain dataset and evaluation protocol are planned for later fine-tuning.

**Can the output be trusted automatically?**

No. It is an assistive drafting system. Human review remains necessary, especially for official, security, medical or emergency communication. Future retrieval and citation support will improve traceability.

**How can this scale?**

The UI, API, extraction layer, model adapter and output instruction map are separate concerns. The local model adapter can be replaced with a larger local model or controlled enterprise inference service without changing the workflow contract.
