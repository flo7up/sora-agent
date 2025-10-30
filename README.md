# Sora Agent

Generate short-form videos using Azure OpenAI Sora and the Agent Framework for Azure AI. The agent orchestrates prompt creation, remix flows, and combines generated clips into a final deliverable.

## Features
- Async agent workflow driven by `AzureAIAgentClient`
- Tooling for Sora video generation and remixing
- Automatic project-folder management with timestamped outputs
- Optional ffmpeg-based concatenation of generated clips
- Test helpers for exercising video generation and error handling

## Requirements
- Python 3.10 or later
- Azure CLI authenticated against a subscription with access to Azure OpenAI
- ffmpeg installed and available on the system `PATH` (for video concatenation)

Install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade -r requirements.txt
```

## Configuration
The project reads configuration values from environment variables. Populate them via a `.env`-style file excluded from version control or export them in your shell before running the agent.

| Variable | Description |
| --- | --- |
| `SORA_ENDPOINT` | Base URL for Azure OpenAI Sora (e.g. `https://<resource-name>.openai.azure.com/`). Prefer setting this at runtime rather than hardcoding it. |
| `SORA_DEPLOYMENT` | Name of the deployed Sora model (e.g. `sora-2`). |
| `SORA_OUTPUT_DIR` | Optional root folder for generated project directories. Defaults to the repo folder. |
| `AZURE_OPENAI_API_KEY` | **Do not commit**. Azure OpenAI API key when using key-based auth. |
| `AZURE_OPENAI_API_VERSION` | API version string to call. |
| `AZURE_AI_PROJECT_ENDPOINT` | Project endpoint when integrating with Azure AI Studio projects. |
| `AZURE_AI_MODEL_DEPLOYMENT_NAME` | Default text model deployment for responses. |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | Optional Application Insights connection string for telemetry. |

The sample `._env` file shows expected variable names but contains placeholder values only. Replace placeholders locally and keep real keys out of source control.

## Usage
Run the agent (requires Azure CLI login and appropriate role assignments):

```powershell
az login
python sora_agent.py
```

Generated videos and intermediate files are written to `video_projects/` with a timestamped subdirectory.

## Tests
The `test_sora_tools.py` module includes sanity checks and live-call exercises. To run them:

```powershell
pytest test_sora_tools.py
```

Live-call tests require Sora access and may consume quota. Skip or adjust as needed.

## Project Structure
- `sora_agent.py` – Entry point for the Azure AI agent orchestration.
- `sora_tools.py` – Tool implementations for generating and combining Sora videos.
- `file_loaders.py` – Helpers for loading prompt instruction files.
- `instructions_base.txt` / `instructions_remix.txt` – Human-authored guidance supplied to the agent.
- `Archive/` – Legacy experiments and scripts kept for reference.

## Security
- Do not hardcode API keys or sensitive identifiers in source files.
- Review any Azure resource names or endpoints before publishing; convert to environment-driven settings when possible.
- Add your secrets file (e.g. `.env`) to `.gitignore` so it never leaves your local environment.
