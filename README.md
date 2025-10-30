# Sora Agent

## Overview
- Generate short-form videos using Azure OpenAI Sora and the Agent Framework for Azure AI. The agent orchestrates prompt creation, remix flows, and combines generated clips into a final deliverable.
- Automates multi-part video creation with Azure OpenAI Sora and stitches the outputs into a final cut.
- Uses an Azure-hosted GPT agent to orchestrate scene prompts, monitor job status, and manage downloads.
- Extracts the last frame of each rendered clip and feeds it as the reference image for the next video to keep visual continuity.

## Key Components
- `sora_agent.py` bootstraps the run, creates a timestamped project workspace, and launches the Azure AI Agent with available tools.
- `sora_tools.py` provides functions to:
  - generate videos (`generate_sora_video`) with automatic reference-frame reuse,
  - combine the produced clips (`combine_video_parts`),
  - maintain per-run context (project directory, latest frame asset).
- `file_loaders.py` loads optional instruction overlays from local text files.

## Prerequisites
- Python 3.10+
- Azure CLI login with sufficient access to your Azure OpenAI resource.
- Environment variables:
  - `AZURE_OPENAI_ENDPOINT` / credentials handled through `DefaultAzureCredential`.
  - Optional `SORA_OUTPUT_DIR` to override the default output location.
- `ffmpeg` and `ffprobe` available on the system `PATH` for frame extraction and concatenation.

## Setup
1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```
2. Log in with Azure CLI:

   ```bash
   az login
   ```

3. (Optional) Create `video_idea.txt`, `instructions_base.txt`, and `instructions_remix.txt` to seed agent prompts.

## Workflow
1. Agent creates a timestamped project directory under `video_projects/`.
2. First clip: provide a full prompt (characters, style, camera). The rendered video’s last frame is saved beside the clip.
3. Subsequent clips: pass only incremental changes; the saved PNG is uploaded as `input_reference` for continuity.
4. Repeat until all scenes are generated.
5. Call `combine_video_parts` to concatenate every `.mp4` into `final_video.mp4`.

## Running the Agent
```bash
python sora_agent.py
```
- The agent prints progress, job IDs, saved video paths, and extracted reference frames.
- Final status includes the combined video output path.

## Customization Tips
- Adjust `SORA_DEFAULT_SIZE` or `seconds` in `sora_tools.py` to match project requirements.
- Modify instruction files to steer the GPT agent’s storytelling style.
- Manually supply prompts via `generate_sora_video` if integrating with other orchestration logic.

## Troubleshooting
- Missing reference PNGs usually indicate `ffmpeg`/`ffprobe` configuration issues—confirm both binaries are accessible.
- Azure authentication errors: ensure `az account show` reflects the intended subscription and resource access.
- Video concatenation failures: inspect `parts_list.txt` and re-run `combine_video_parts` after verifying each clip.

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
