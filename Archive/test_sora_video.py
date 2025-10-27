#!/usr/bin/env python3
"""
Test script for the Sora video generation function.
Run this script to test video generation without the full agent framework.
"""

import sys
import os
import argparse
from pathlib import Path

# Import the video generation function from the main module
try:
    from sora_agent import generate_sora_video
except ImportError as e:
    print(f"Error importing sora_agent: {e}")
    print("Make sure sora_agent.py is in the same directory")
    sys.exit(1)


def test_basic_generation():
    """Test with basic parameters."""
    print("\n=== Test 1: Basic Generation ===")
    result = generate_sora_video(
        prompt="A serene beach at sunset with gentle waves",
        seconds=5,
        variants=1,
        filename_hint="test_basic"
    )
    print(f"Result: {result}")
    return result


def test_multiple_variants():
    """Test generating multiple variants."""
    print("\n=== Test 2: Multiple Variants ===")
    result = generate_sora_video(
        prompt="A futuristic cityscape with flying vehicles",
        seconds=10,
        variants=2,
        filename_hint="test_variants"
    )
    print(f"Result: {result}")
    return result


def test_custom_resolution():
    """Test with custom resolution."""
    print("\n=== Test 3: Custom Resolution ===")
    result = generate_sora_video(
        prompt="A butterfly landing on a colorful flower in slow motion",
        seconds=8,
        variants=1,
        filename_hint="test_lowres"
    )
    print(f"Result: {result}")
    return result


def test_long_video():
    """Test with longer duration."""
    print("\n=== Test 4: Longer Duration ===")
    result = generate_sora_video(
        prompt="Time-lapse of clouds moving across a mountain landscape",
        seconds=20,
        variants=1,
        filename_hint="test_long"
    )
    print(f"Result: {result}")
    return result


def test_quick():
    """Quick test with minimal parameters."""
    print("\n=== Quick Test (3 seconds) ===")
    result = generate_sora_video(
        prompt="A simple rotating cube with glowing edges",
        seconds=4,
        variants=1,
        filename_hint="test_quick"
    )
    print(f"Result: {result}")
    return result


def custom_test(args):
    """Run a custom test with command-line arguments."""
    print(f"\n=== Custom Test ===")
    print(f"Prompt: {args.prompt}")
    print(f"Duration: {args.seconds} seconds")
    print(f"Resolution: {args.width}x{args.height}")
    print(f"Variants: {args.variants}")
    
    result = generate_sora_video(
        prompt=args.prompt,
        seconds=args.seconds,
        variants=args.variants,
        filename_hint=args.filename or "custom_test"
    )
    print(f"\nResult: {result}")
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Test Sora video generation function",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick 3-second test
  python test_sora_video.py --quick
  
  # Run all predefined tests
  python test_sora_video.py --all
  
  # Run a specific test
  python test_sora_video.py --test basic
  
  # Custom video generation
  python test_sora_video.py --custom "A cat playing piano" --seconds 10
  
  # Custom with all parameters
  python test_sora_video.py --custom "Northern lights dancing" --seconds 15 --width 1920 --height 1080 --variants 2
        """
    )
    
    # Test selection arguments
    parser.add_argument("--quick", action="store_true", help="Run a quick 3-second test")
    parser.add_argument("--all", action="store_true", help="Run all predefined tests")
    parser.add_argument("--test", choices=["basic", "variants", "resolution", "long"],
                       help="Run a specific predefined test")
    
    # Custom test arguments
    parser.add_argument("--custom", metavar="PROMPT", help="Custom prompt for video generation")
    parser.add_argument("--seconds", type=int, default=12, help="Video duration in seconds (1-60)")
    parser.add_argument("--width", type=int, default=1280, help="Video width in pixels")
    parser.add_argument("--height", type=int, default=720, help="Video height in pixels")
    parser.add_argument("--variants", type=int, default=1, help="Number of variants (1-4)")
    parser.add_argument("--filename", help="Filename hint for the generated video")
    
    args = parser.parse_args()
    
    # Validate arguments
    if not (args.quick or args.all or args.test or args.custom):
        parser.print_help()
        print("\nError: Please specify --quick, --all, --test, or --custom")
        sys.exit(1)
    
    try:
        if args.quick:
            test_quick()
            
        elif args.all:
            print("\nRunning all tests...")
            test_basic_generation()
            test_multiple_variants()
            test_custom_resolution()
            test_long_video()
            
        elif args.test:
            if args.test == "basic":
                test_basic_generation()
            elif args.test == "variants":
                test_multiple_variants()
            elif args.test == "resolution":
                test_custom_resolution()
            elif args.test == "long":
                test_long_video()
                
        elif args.custom:
            # Validate custom parameters
            if args.seconds < 1 or args.seconds > 60:
                print("Error: seconds must be between 1 and 60")
                sys.exit(1)
            if args.variants < 1 or args.variants > 4:
                print("Error: variants must be between 1 and 4")
                sys.exit(1)
                
            args.prompt = args.custom
            custom_test(args)
            
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    print("=== Sora Video Generation Test Suite ===")
    print(f"Current directory: {Path.cwd()}")
    
    # Display environment info
    endpoint = os.getenv("ENDPOINT_URL")
    output_dir = os.getenv("SORA_OUTPUT_DIR", ".")
    
    print(f"Endpoint: {endpoint if endpoint else 'Not set'}")
    print(f"Output directory: {Path(output_dir).resolve()}\n")
    
    main()

