import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import OpenAI
from pydantic import Field

from agent_framework import ai_function

# Global variable to store the current project folder for this agent run
_current_project_folder: Path = None
# Global variable to store the last generated video ID for remix feature
_last_video_id: str = None

# Sora configuration
SORA_ENDPOINT = "https://ai-ffollonier-0931.openai.azure.com/"
SORA_DEPLOYMENT = "sora-2"
SORA_API_VERSION = "2024-12-01-preview"  # Updated API version for Sora
SORA_DEFAULT_POLL_INTERVAL = 5
SORA_MAX_POLLS = 60

_credential = DefaultAzureCredential()

# Initialize OpenAI client with token provider for Azure
token_provider = get_bearer_token_provider(
    _credential, "https://cognitiveservices.azure.com/.default"
)

# Use OpenAI client with Azure endpoint (not AzureOpenAI)
client = OpenAI(
    base_url=f"{SORA_ENDPOINT}openai/v1/",
    api_key=token_provider,
    default_headers={
        "api-version": SORA_API_VERSION
    }
)


def _sanitize_filename_fragment(fragment: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in ("-", "_") else "_" for char in fragment.strip())
    return cleaned or "sora_video"


def set_project_folder(folder: Path):
    """Set the current project folder for video generation."""
    global _current_project_folder
    _current_project_folder = folder


@ai_function(
    name="generate_sora_video",
    description=(
        "Creates a video with Azure OpenAI Sora. For the FIRST video in a series, provide a complete, "
        "vivid prompt describing the full scene. The function returns a video ID that should be used "
        "for subsequent videos. For SUBSEQUENT videos (2nd, 3rd, etc.), describe only the CHANGES "
        "you want to make from the previous video (e.g., 'change camera angle to overhead', "
        "'add rain to the scene', 'shift time to sunset'). This ensures consistency across videos. "
        "Set use_remix=True for subsequent videos to maintain visual consistency."
    ),
)
def generate_sora_video(
    prompt: Annotated[str, Field(description="For first video: full scene description. For subsequent videos: describe only the changes from the previous video.")],
    seconds: Annotated[int, Field(description="Desired video length in seconds (4, 8, or 12).")] = 12,
    use_remix: Annotated[bool, Field(description="Set to True to remix the previous video with changes. False for first video.")] = False,
    poll_interval_seconds: Annotated[
        int, Field(description="Seconds between status checks.", ge=1, le=30)
    ] = SORA_DEFAULT_POLL_INTERVAL,
    filename_hint: Annotated[
        str, Field(description="Optional prefix for the generated file name.", max_length=64)
    ] = "sora_video",
) -> str:
    """Generate one Sora video and save it to the project folder.
    
    Note: The 'seconds' parameter only accepts values of 4, 8, or 12. Other values will be rejected by the API.
    For remix: The first video establishes the base. Subsequent videos should use use_remix=True and 
    describe only changes to maintain consistency.
    """
    global _current_project_folder, _last_video_id
    
    if _current_project_folder is None:
        return "Error: Project folder not initialized. Agent setup failed."
    
    prompt = prompt.strip()
    if not prompt:
        return "Video generation aborted: the prompt cannot be empty."
    
    # Validate seconds parameter
    if seconds not in [4, 8, 12]:
        return f"Error: 'seconds' must be 4, 8, or 12. Got: {seconds}"
    
    # Check if remix is requested but no previous video exists
    if use_remix and not _last_video_id:
        return "Cannot use remix: no previous video ID available. Generate the first video without remix."

    try:
        # Step 1: Submit video generation request
        create_params = {
            "model": "sora-2",
            "prompt": prompt,
            "seconds": str(seconds),
        }
        
        # Add remix_video_id if using remix feature
        if use_remix and _last_video_id:
            create_params["remix_video_id"] = _last_video_id
            print(f"Using remix with video ID: {_last_video_id}")
        
        # Use the videos.create endpoint
        video = client.videos.create(**create_params)
        
        job_id = video.id
        if not job_id:
            return "Video generation failed: no job ID returned."
            
    except Exception as exc:
        return f"Video generation request failed: {exc}"

    # Step 2: Poll for completion
    polls = 0
    
    while polls < SORA_MAX_POLLS:
        polls += 1
        time.sleep(poll_interval_seconds)
        
        try:
            # Retrieve updated video status
            video = client.videos.retrieve(job_id)
            
            # Check status
            status = getattr(video, 'status', None)
            
            if status in {"succeeded", "completed"}:
                break
            
            if status in {"failed", "error", "cancelled"}:
                error_msg = f"Job failed. Status: {status}"
                if hasattr(video, 'error') and video.error:
                    error_msg += f". Error: {video.error}"
                return error_msg
                
        except Exception as exc:
            return f"Polling video job {job_id} failed: {exc}"

    # Step 3: Download and save video to project folder
    sanitized_hint = _sanitize_filename_fragment(filename_hint)
    timestamp_suffix = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")

    try:
        # Download video content
        unique_suffix = f"{timestamp_suffix}-{uuid.uuid4().hex[:6]}"
        remix_prefix = "remix_" if use_remix else ""
        filename = f"{remix_prefix}{sanitized_hint}-{unique_suffix}.mp4"
        output_path = _current_project_folder / filename
        
        # Get video URL and download
        if hasattr(video, 'output') and video.output:
            video_url = video.output[0] if isinstance(video.output, list) else video.output
            
            # Download the video file
            import requests
            response = requests.get(video_url, headers={"Authorization": f"Bearer {token_provider()}"})
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
        else:
            return f"Video generation completed but no output URL available for job {job_id}"
        
        # Store the video ID for future remix operations
        _last_video_id = job_id
        
        remix_note = f" (remixed from previous video)" if use_remix else " (base video for remix)"
        
        return (
            f"Video generation succeeded for job {job_id}{remix_note}.\n"
            f"Video ID: {job_id}\n"
            f"Saved: {output_path}\n"
            f"This video ID can be used for remixing subsequent videos."
        )
        
    except Exception as exc:
        return f"Failed to download and save video {job_id}: {exc}"


@ai_function(
    name="combine_video_parts",
    description="Combines all video files in the project folder into a single final video",
)
def combine_video_parts() -> str:
    """Combine all video parts in the project folder into a single video using ffmpeg."""
    global _current_project_folder
    
    if _current_project_folder is None:
        return "Error: Project folder not initialized."
    
    project_path = _current_project_folder
    if not project_path.exists():
        return f"Project folder not found: {project_path}"

    # Find all mp4 files
    video_parts = sorted(project_path.glob("*.mp4"))
    if not video_parts:
        return f"No video files found in {project_path}"

    # Create a text file listing all parts for ffmpeg
    list_file = project_path / "parts_list.txt"
    with open(list_file, "w") as f:
        for part in video_parts:
            f.write(f"file '{part.absolute()}'\n")

    # Combine videos using ffmpeg
    output_path = project_path / "final_video.mp4"

    try:
        # Check if ffmpeg is available
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)

        # Combine videos
        cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_file),
            "-c", "copy",
            "-y",
            str(output_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            return f"Successfully combined {len(video_parts)} video parts into: {output_path}"
        else:
            return f"Failed to combine videos. Error: {result.stderr}"

    except FileNotFoundError:
        return (
            f"ffmpeg not found. Please install ffmpeg to combine videos.\n"
            f"Video parts are saved in: {project_path}\n"
            f"Parts found: {', '.join([p.name for p in video_parts])}"
        )
    except Exception as e:
        return f"Error combining videos: {str(e)}"
