import subprocess
from pathlib import Path

def combine_two_videos(input_folder: str = "combine_input", output_name: str = "combined_output.mp4") -> str:
    """Combine two MP4 files from the input folder into a single video using ffmpeg."""
    input_path = Path(input_folder)
    
    if not input_path.exists():
        return f"Error: Input folder not found: {input_path}"
    
    # Find all mp4 files
    video_files = sorted(input_path.glob("*.mp4"))
    
    if len(video_files) < 2:
        return f"Error: Expected at least 2 MP4 files, found {len(video_files)}"
    
    # Use only the first two videos
    video_files = video_files[:2]
    
    # Create a text file listing the two parts for ffmpeg
    list_file = input_path / "combine_list.txt"
    with open(list_file, "w") as f:
        for video in video_files:
            f.write(f"file '{video.absolute()}'\n")
    
    output_path = input_path / output_name
    
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
            return f"Successfully combined 2 videos into: {output_path}"
        else:
            return f"Failed to combine videos. Error: {result.stderr}"
    
    except FileNotFoundError:
        return "Error: ffmpeg not found. Please install ffmpeg."
    except Exception as e:
        return f"Error combining videos: {str(e)}"


if __name__ == "__main__":
    result = combine_two_videos()
    print(result)
