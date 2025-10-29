import asyncio
import os
from datetime import datetime, timezone
from pathlib import Path
from agent_framework.azure import AzureAIAgentClient
from azure.identity.aio import AzureCliCredential

from sora_tools import generate_sora_video, combine_video_parts, set_project_folder
from file_loaders import load_script_ideas, load_base_instructions, load_remix_instructions

SORA_BASE_OUTPUT_DIR = Path(os.getenv("SORA_OUTPUT_DIR", Path(__file__).parent)).resolve()


def _setup_project_folder() -> Path:
    """Create and return a timestamped project folder for this agent run."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    project_folder = SORA_BASE_OUTPUT_DIR / "video_projects" / f"video_project_{timestamp}"
    project_folder.mkdir(parents=True, exist_ok=True)
    set_project_folder(project_folder)
    print(f"Project folder created: {project_folder}")
    return project_folder


async def main():
    # Setup project folder at agent start
    project_folder = _setup_project_folder()
    print(f"Video files will be saved to: {project_folder}\n")
    
    # Load script ideas and instructions from files
    script_ideas = load_script_ideas()
    base_instructions = load_base_instructions()
    remix_instructions = load_remix_instructions()
    
    # Append script ideas if available
    if script_ideas:
        instructions = f"{base_instructions}\n\n{remix_instructions}\n\n{script_ideas}"
    else:
        instructions = f"{base_instructions}\n\n{remix_instructions}"
        
    print("Agent Instructions:\n", instructions)
    async with (
        AzureCliCredential() as credential,
        AzureAIAgentClient(async_credential=credential).create_agent(
            deployment_name="gpt-5",
            store=True,
            api_version="2024-12-15-preview",
            credential=AzureCliCredential(),
            instructions=instructions,
            tools=[
                generate_sora_video,
                combine_video_parts
            ],
        ) as agent,
    ):
        result = await agent.run("create the video! " + instructions)
        print(result.text)
    

if __name__ == "__main__":
    asyncio.run(main())
