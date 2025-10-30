import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Optional

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import OpenAI
from pydantic import Field

from agent_framework import ai_function

# Global variable to store the current project folder for this agent run
_current_project_folder: Path = None
_last_reference_frame: Optional[Path] = None
# Global variable to store the last generated video ID for remix feature
_last_video_id: str = None

# Sora configuration
SORA_ENDPOINT = "https://ai-ffollonier-0931.openai.azure.com/"
SORA_DEPLOYMENT = "sora-2"
SORA_DEFAULT_POLL_INTERVAL = 5
SORA_MAX_POLLS = 60
SORA_DEFAULT_SIZE = "1280x720"

_credential = DefaultAzureCredential()

# Initialize OpenAI client with token provider
token_provider = get_bearer_token_provider(
    _credential, "https://cognitiveservices.azure.com/.default"
)

client = OpenAI(
    base_url=f"{SORA_ENDPOINT}openai/v1/",
    api_key=token_provider,
)


def _sanitize_filename_fragment(fragment: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in ("-", "_") else "_" for char in fragment.strip())
    return cleaned or "sora_video"


def _get_video_frame_count(video_path: Path) -> Optional[int]:
    probe_variants = [
        (
            "-count_frames",
            "-show_entries",
            "stream=nb_read_frames",
        ),
        (
            "-show_entries",
            "stream=nb_frames",
        ),
    ]
    for variant in probe_variants:
        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            *variant,
            "-of",
            "default=nokey=1:noprint_wrappers=1",
            str(video_path),
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        except FileNotFoundError:
            print("ffprobe not found. Unable to compute frame count.")
            return None
        except subprocess.CalledProcessError:
            continue
        value = result.stdout.strip()
        if value.isdigit():
            return int(value)
    return None


def _extract_last_frame(video_path: Path) -> Optional[Path]:
    output_path = video_path.with_name(f"{video_path.stem}_last_frame.png")
    frame_count = _get_video_frame_count(video_path)
    if frame_count and frame_count > 0:
        frame_index = frame_count - 1
        cmd = [
            "ffmpeg",
            "-i",
            str(video_path),
            "-vf",
            f"select=eq(n\\,{frame_index})",
            "-vframes",
            "1",
            "-vsync",
            "vfr",
            "-y",
            str(output_path),
        ]
    else:
        cmd = [
            "ffmpeg",
            "-sseof",
            "-1",
            "-i",
            str(video_path),
            "-vframes",
            "1",
            "-vsync",
            "vfr",
            "-y",
            str(output_path),
        ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except FileNotFoundError:
        print("ffmpeg not found. Unable to extract last frame.")
        return None
    except subprocess.CalledProcessError as exc:
        print(f"Failed to extract last frame from {video_path}: {exc.stderr or exc.stdout}")
        return None
    if output_path.exists():
        return output_path
    if frame_count:
        print(f"Last frame extraction produced no output for {video_path} (frame index {frame_count - 1}).")
    else:
        print(f"Last frame extraction fallback produced no output for {video_path}.")
    return None


def set_project_folder(folder: Path):
    """Set the current project folder for video generation."""
    global _current_project_folder, _last_reference_frame
    _current_project_folder = folder
    _last_reference_frame = None


@ai_function(
    name="generate_sora_video",
    description=(
        "Creates a video with Azure OpenAI Sora. Provide a full prompt for the first video, then only describe changes. "
        "The tool automatically sends the last frame from the previous video as input_reference to maintain continuity. "
        "The use_remix flag is deprecated and ignored."
    ),
)
def generate_sora_video(
    prompt: Annotated[str, Field(description="For first video: full scene description. For subsequent videos: describe only the changes from the previous video.")],
    seconds: Annotated[int, Field(description="Desired video length in seconds (1-60).", ge=1, le=60)] = 12,
    use_remix: Annotated[bool, Field(description="Deprecated. Kept for backward compatibility.")] = False,
    poll_interval_seconds: Annotated[
        int, Field(description="Seconds between status checks.", ge=1, le=30)
    ] = SORA_DEFAULT_POLL_INTERVAL,
    filename_hint: Annotated[
        str, Field(description="Optional prefix for the generated file name.", max_length=64)
    ] = "sora_video",
) -> str:
    """Generate one Sora video and save it to the project folder.

    The last frame of each completed video is saved as a PNG and automatically reused as the
    reference image for the next call.
    """
    global _current_project_folder, _last_reference_frame
    
    if _current_project_folder is None:
        return "Error: Project folder not initialized. Agent setup failed."
    
    prompt = prompt.strip()
    if not prompt:
        return "Video generation aborted: the prompt cannot be empty."
    
    if use_remix:
        print("Note: use_remix is deprecated; reference images are applied automatically.")

    # Prepare video creation parameters
    create_params = {
        "model": SORA_DEPLOYMENT,
        "prompt": prompt,
        "seconds": str(seconds),
        "size": SORA_DEFAULT_SIZE,
    }
    
    video = None
    job_id = None
    reference_file = None
    try:
        # Attach the last reference frame if available
        if _last_reference_frame and _last_reference_frame.exists():
            reference_file = open(_last_reference_frame, "rb")
            create_params["input_reference"] = reference_file
            print(f"Using reference image for video generation: {_last_reference_frame}")
        
        # Submit the video creation request
        video = client.videos.create(**create_params)
        
        job_id = video.id
        if not job_id:
            return "Video generation failed: no job ID returned."
            
    except Exception as exc:
        return f"Video generation request failed: {exc}"
    finally:
        if reference_file:
            reference_file.close()

    # Step 2: Poll for completion using OpenAI client
    polls = 0
    
    while polls < SORA_MAX_POLLS:
        polls += 1
        time.sleep(poll_interval_seconds)
        
        try:
            # Retrieve updated video status
            video = client.videos.retrieve(video.id)
            
            # Stop if progress is 100% or status indicates completion
            if video.progress == 100 or video.status in {"succeeded", "completed"}:
                break
            
            if video.status in {"failed", "error"}:
                error_msg = f"Job failed. Status: {video.status}"
                if video.error:
                    error_msg += f". Error: {video.error}"
                return error_msg
                
        except Exception as exc:
            return f"Polling video job {job_id} failed: {exc}"

    # Step 3: Download and save video to project folder
    sanitized_hint = _sanitize_filename_fragment(filename_hint)
    timestamp_suffix = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")

    try:
        # Download video content using the client
        unique_suffix = f"{timestamp_suffix}-{uuid.uuid4().hex[:6]}"
        filename = f"{sanitized_hint}-{unique_suffix}.mp4"
        output_path = _current_project_folder / filename
        
        content = client.videos.download_content(video.id, variant="video")
        content.write_to_file(str(output_path))
        
        # Extract and save the last frame as a reference for the next video
        last_frame_path = _extract_last_frame(output_path)
        if last_frame_path:
            _last_reference_frame = last_frame_path
        message = (
            f"Video generation succeeded for job {job_id}.\n"
            f"Video ID: {video.id}\n"
            f"Saved: {output_path}"
        )
        if last_frame_path:
            message += f"\nLast frame saved: {last_frame_path}"
        else:
            message += "\nLast frame unavailable; continuing with prior reference if available."
        return message
        
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
