#!/usr/bin/env python
"""
Quick check script for Ollama installation
Run this after installing Ollama to verify everything works
"""

import subprocess
import sys
import time

def run_command(cmd, description=""):
    """Run a command and show progress"""
    print(f"\n{'='*50}")
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    print(f"{'='*50}")

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ SUCCESS!")
            print(result.stdout)
        else:
            print("❌ FAILED!")
            print("Error:", result.stderr)

        return result.returncode == 0

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    """Check Ollama installation and setup"""
    print("🔍 AVICAST - Checking Ollama Installation")
    print("=" * 50)

    # Step 1: Check if Ollama is installed
    print("\n1. Checking Ollama installation...")
    if not run_command("ollama --version", "Check Ollama version"):
        print("\n❌ Ollama is not installed or not in PATH")
        print("Please install Ollama from: https://ollama.com/download/windows")
        print("Then run this script again.")
        return

    # Step 2: Check if models are available
    print("\n2. Checking available models...")
    if not run_command("ollama list", "List installed models"):
        print("\n⚠️  No models installed yet")

    # Step 3: Pull a model if none available
    print("\n3. Pulling llama3.2 model (this may take 3-5 minutes)...")
    if run_command("ollama pull llama3.2", "Download llama3.2 model"):
        print("✅ Model downloaded successfully!")

        # Step 4: Verify model is available
        print("\n4. Verifying model availability...")
        run_command("ollama list", "Verify models are listed")

        # Step 5: Quick test
        print("\n5. Testing AI integration...")
        run_command("python scripts/test_ai_census_helper.py", "Run AI tests")

    print("\n" + "=" * 50)
    print("🎉 Setup complete! Your AI census helper is ready!")
    print("=" * 50)
    print()
    print("Next steps:")
    print("1. Import your Excel census data")
    print("2. The AI will help match species names")
    print("3. Review AI suggestions for data corrections")
    print("4. Enjoy offline AI assistance!")

if __name__ == '__main__':
    main()


