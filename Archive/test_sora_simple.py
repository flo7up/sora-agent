import json
import time
from pathlib import Path
from openai import OpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

SORA_ENDPOINT = "https://ai-ffollonier-0931.openai.azure.com/"
SORA_DEPLOYMENT = "sora-2"
POLL_INTERVAL = 5
MAX_POLLS = 120

# Initialize token provider and OpenAI client
token_provider = get_bearer_token_provider(
    DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
)

credential = DefaultAzureCredential()

client = OpenAI(
    base_url=f"{SORA_ENDPOINT}openai/v1/",
    api_key=token_provider,
)

def _get_headers() -> dict:
    """Get headers with fresh token."""
    token_response = credential.get_token("https://cognitiveservices.azure.com/.default")
    return {
        "Authorization": f"Bearer {token_response.token}",
        "Content-Type": "application/json",
    }

def test_sora_simple():
    """Complete test of Sora 2 video generation: submit → poll → download → save."""
    
    print(f"Endpoint: {SORA_ENDPOINT}")
    print(f"Model: {SORA_DEPLOYMENT}")
    print()
    
    try:
        # Step 1: Submit video generation request
        print("Step 1: Submitting video generation request...")
        video = client.videos.create(
            model=SORA_DEPLOYMENT,
            prompt="A cat sitting on a desk",
        )
        
        print(f"  Response type: {type(video)}")
        print(f"  ID: {video.id}")
        print(f"  Status: {video.status}")
        print(f"  Progress: {video.progress}")
        print()
        
        # Step 2: Poll for completion using OpenAI client
        print("Step 2: Polling for job completion...")
        polls = 0
        
        while polls < MAX_POLLS:
            polls += 1
            print(f"  Poll {polls}/{MAX_POLLS}...", end=" ", flush=True)
            time.sleep(POLL_INTERVAL)
            
            # Retrieve updated video status
            video = client.videos.retrieve(video.id)
            print(f"Status: {video.status}, Progress: {video.progress}%")
            
            # Stop if progress is 100% or status indicates completion
            if video.progress == 100 or video.status in {"succeeded", "completed"}:
                break
            
            if video.status in {"failed", "error"}:
                print(f"  ERROR: Job failed. Status: {video.status}")
                if video.error:
                    print(f"  Error details: {video.error}")
                return
        
        print("  Job completed!")
        print()
        
        # Step 3: Download and save video
        print("Step 3: Downloading and saving video...")
        output_dir = Path("./sora_output")
        output_dir.mkdir(exist_ok=True)
        
        # Download video content using the client
        output_file = output_dir / f"sora_video_{video.id}.mp4"
        content = client.videos.download_content(video.id, variant="video")
        content.write_to_file(str(output_file))
        
        print(f"  Saved to: {output_file.absolute()}")
        print()
        print("✓ Complete!")
            
    except Exception as e:
        print(f"Error: {type(e).__name__}")
        print(f"Message: {e}")

if __name__ == "__main__":
    test_sora_simple()
