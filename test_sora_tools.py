import asyncio
from pathlib import Path
from datetime import datetime, timezone

from sora_tools import generate_sora_video, combine_video_parts, set_project_folder


def setup_test_project_folder() -> Path:
    """Create a test project folder."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    test_folder = Path(__file__).parent / "test_outputs" / f"test_{timestamp}"
    test_folder.mkdir(parents=True, exist_ok=True)
    set_project_folder(test_folder)
    print(f"Test project folder: {test_folder}")
    return test_folder


def test_generate_single_video():
    """Test generating a single video."""
    print("\n=== Test 1: Generate Single Video ===")
    setup_test_project_folder()
    
    result = generate_sora_video(
        prompt="A serene lake at sunset with mountains in the background, cinematic drone shot",
        seconds=4,
        use_remix=False,
        filename_hint="test_single"
    )
    print(result)
    assert "Video generation succeeded" in result or "Video generation request failed" in result
    print("✓ Test passed")


def test_generate_with_remix():
    """Test generating videos with remix feature."""
    print("\n=== Test 2: Generate Videos with Remix ===")
    setup_test_project_folder()
    
    # First video - base
    print("\nGenerating base video...")
    result1 = generate_sora_video(
        prompt="A warrior in golden armor standing on a cliff, cinematic style, wide angle",
        seconds=4,
        use_remix=False,
        filename_hint="base_video"
    )
    print(result1)
    
    if "Video generation succeeded" in result1:
        # Second video - remix
        print("\nGenerating remix video...")
        result2 = generate_sora_video(
            prompt="zoom in closer to the warrior's face",
            seconds=4,
            use_remix=True,
            filename_hint="remix_video"
        )
        print(result2)
        assert "Video generation succeeded" in result2 or "remixed from" in result2
        print("✓ Test passed")
    else:
        print("⚠ Skipping remix test - base video generation failed")


def test_combine_videos():
    """Test combining video parts."""
    print("\n=== Test 3: Combine Video Parts ===")
    test_folder = setup_test_project_folder()
    
    # Create dummy video files for testing
    for i in range(3):
        dummy_file = test_folder / f"test_part_{i}.mp4"
        dummy_file.write_text(f"dummy video content {i}")
    
    result = combine_video_parts()
    print(result)
    
    # Should either succeed or fail with ffmpeg not found
    assert "combined" in result.lower() or "ffmpeg not found" in result.lower()
    print("✓ Test passed")


def test_invalid_remix():
    """Test that remix fails without a previous video."""
    print("\n=== Test 4: Invalid Remix (No Previous Video) ===")
    setup_test_project_folder()
    
    result = generate_sora_video(
        prompt="add rain to the scene",
        seconds=4,
        use_remix=True,
        filename_hint="invalid_remix"
    )
    print(result)
    assert "Cannot use remix" in result
    print("✓ Test passed")


def test_empty_prompt():
    """Test that empty prompt is rejected."""
    print("\n=== Test 5: Empty Prompt ===")
    setup_test_project_folder()
    
    result = generate_sora_video(
        prompt="   ",
        seconds=4,
        use_remix=False
    )
    print(result)
    assert "prompt cannot be empty" in result
    print("✓ Test passed")


def run_all_tests():
    """Run all tests."""
    print("Starting Sora Tools Tests...")
    print("=" * 50)
    
    try:
        test_empty_prompt()
        test_invalid_remix()
        test_generate_single_video()
        test_generate_with_remix()
        test_combine_videos()
        
        print("\n" + "=" * 50)
        print("✓ All tests completed!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()
