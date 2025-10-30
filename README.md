# Sora Agent

## Overview
- Automates Azure OpenAI Sora video generation through an orchestrated agent workflow.
- Creates sequential clips that reuse the previous video’s final frame to preserve visual continuity.
- Accepts an optional starter image stored at `initial_image/` (or `initial_image.<ext>`) for the very first scene.
- Exposes helper tools to download clips, capture last frames, and concatenate all parts.

## Repository Structure
- `sora_agent.py` bootstraps an `AzureAIAgentClient`, prepares a timestamped project folder, and launches the agent run.
- `sora_tools.py` implements `generate_sora_video`, reference-frame extraction, and `combine_video_parts`.
- `file_loaders.py` reads optional prompt and instruction overlays from local text files.
- `video_projects/` (created at runtime) stores generated videos, extracted PNG frames, concatenation lists, and the final cut.

## Prerequisites
- Python 3.10 or later.
- Azure CLI authenticated against the subscription hosting your Azure OpenAI resource.
- `ffmpeg` and `ffprobe` available on the system `PATH` (required for frame extraction and concatenation).
- Network access to the configured Azure OpenAI endpoint (`SORA_ENDPOINT` inside `sora_tools.py`).

## Setup
1. Clone the repository and change into the project directory.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Sign in to Azure:

   ```bash
   az login
   ```

4. (Optional) Create any of the following files in the repository root to influence agent guidance:
   - `video_idea.txt` – seed ideas listed line by line (lines starting with `#` are ignored).
   - `instructions_base.txt` – default production instructions.
  - `instructions_remix.txt` – incremental-change guidance for follow-up clips.

5. (Optional) Place a starter reference image at:
   - `initial_image.png` / `.jpg` / `.jpeg` / `.webp`, **or**
   - `initial_image/` containing one of those formats (first file alphabetically is used).

## Workflow
1. Running the agent creates `video_projects/video_project_<timestamp>/` and stores all assets inside it.
2. First call to `generate_sora_video` expects a full prompt (characters, setting, style, camera). The optional starter image is uploaded as `input_reference`.
3. Each rendered clip is downloaded, and the final frame is extracted to `{clip_name}_last_frame.png`.
4. Subsequent calls provide only prompt deltas; the saved PNG becomes the `input_reference` automatically.
5. After all clips are produced, `combine_video_parts` concatenates every `.mp4` in chronological order into `final_video.mp4`.

## Usage
```bash
python sora_agent.py
```
- The agent prints job IDs, per-clip save paths, and the extracted reference PNG locations.
- Provide additional instructions or manual prompts by editing the text files or adjusting the agent message in `sora_agent.py`.

## Troubleshooting
- **Missing PNG frames**: confirm both `ffmpeg` and `ffprobe` are installed and reachable from the shell.
- **Azure authentication issues**: ensure `az account show` returns the intended account and subscription.
- **Concatenation failures**: inspect `parts_list.txt`, verify each listed clip exists, then rerun `combine_video_parts`.
- **Starter image ignored**: check naming/extension and confirm it lives alongside the repository files.
