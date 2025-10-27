from pathlib import Path


def _load_text_file(
    default_filename: str,
    filepath: Path = None,
    not_found_message: str = None,
    filter_comments: bool = False,
    base_dir: Path = None
) -> str:
    """Load content from a text file.
    
    Args:
        default_filename: Default filename to use if filepath is None
        filepath: Optional custom file path
        not_found_message: Custom message for FileNotFoundError
        filter_comments: If True, filter out lines starting with #
        base_dir: Base directory for resolving default_filename
    
    Returns:
        File content as string, or empty string on error
    """
    if filepath is None:
        if base_dir is None:
            base_dir = Path(__file__).parent
        filepath = base_dir / default_filename
    
    if not_found_message is None:
        not_found_message = f"Warning: {filepath} not found."
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            
            if filter_comments:
                lines = [line for line in content.splitlines() if not line.strip().startswith("#")]
                return "\n".join(lines).strip()
            
            return content
    except FileNotFoundError:
        print(not_found_message)
        return ""
    except Exception as e:
        print(f"Warning: Could not load file {filepath}: {e}")
        return ""


def load_script_ideas(filepath: Path = None, base_dir: Path = None) -> str:
    """Load video script ideas from a text file."""
    return _load_text_file(
        "video_script_ideas.txt",
        filepath,
        filter_comments=True,
        not_found_message="Warning: video_script_ideas.txt not found. Create this file to add custom script ideas.",
        base_dir=base_dir
    )


def load_base_instructions(filepath: Path = None, base_dir: Path = None) -> str:
    """Load base instructions from a text file."""
    return _load_text_file(
        "base_instructions.txt",
        filepath,
        not_found_message="Warning: base_instructions.txt not found. Create this file to add custom base instructions.",
        base_dir=base_dir
    )


def load_remix_instructions(filepath: Path = None, base_dir: Path = None) -> str:
    """Load remix instructions from a text file."""
    return _load_text_file(
        "remix_instructions.txt",
        filepath,
        not_found_message="Warning: remix_instructions.txt not found. Using default remix behavior.",
        base_dir=base_dir
    )
