# Guardrails Validation Service

A standalone, reusable validation framework wrapping `guardrails-ai`.

## Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   > **Note**: Guardrails Hub validators are NOT included in pip requirements and must be installed separately.

2. Install Guardrails PII validator:
   ```bash
   guardrails hub install hub://guardrails/detect_pii
   ```
3. Install SpaCy model (required for PII):
   ```bash
   python -m spacy download en_core_web_lg
   ```

## Configuration
Set environment variables for LLM support:
- `VALIDATION_LLM_PROVIDER`: `openai`, `ollama` or `groq`
- `VALIDATION_LLM_MODEL`: e.g. `gpt-3.5-turbo`, `llama3-70b-8192`
- `OPENAI_API_KEY`: Your OpenAI key
- `OLLAMA_BASE_URL`: if using Ollama (default `http://localhost:11434`)
- `GROQ_API_KEY`: Your Groq API Key


## Usage
Run the server:
```bash
uvicorn guardrails_server:app --reload
```
Or run directly with Python:
```bash
python guardrails_server.py
```

## API
### POST /validate
Payload:
```json
{
  "text": "Text to validate",
  "context": [{"id": "c1", "text": "Context..."}],
  "validators": [
    {"name": "detect_pii", "mode": "redact"},
    {"name": "grounded_in_context", "parameters": {"threshold": 0.7}},
    {"name": "citations_present"}
  ]
}
```

Response:
```json
{
  "passed": false,
  "errors": [
    {"validator": "citations_present", "message": "Text is missing citations..."}
  ],
  "validated_text": "Text to validate"
}
```

## Testing
- Import `guardrails_collection.json` into Postman.
- Or use `curl` commands.
