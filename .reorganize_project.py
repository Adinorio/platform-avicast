#!/usr/bin/env python3
"""
Project reorganization script for cleaner repository structure.
This script moves files to more appropriate locations.
"""

import os
import shutil
from pathlib import Path

def create_directories():
    """Create new directory structure."""
    dirs_to_create = [
        "config",
        "scripts/setup",
        "scripts/testing",
        "docs/setup",
        "docs/features",
        "docs/troubleshooting"
    ]

    for dir_path in dirs_to_create:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {dir_path}")

def move_files():
    """Move files to appropriate locations."""

    # Configuration files
    config_moves = [
        ("env.example", "config/env.example"),
        ("egret_training_config.yaml", "config/egret_training_config.yaml"),
        ("hyp.egret.yaml", "config/hyp.egret.yaml"),
        ("pyproject.toml", "config/pyproject.toml"),
    ]

    # Requirements files
    requirements_moves = [
        ("requirements.txt", "config/requirements.txt"),
        ("requirements-dev.txt", "config/requirements-dev.txt"),
        ("requirements-processing.txt", "config/requirements-processing.txt"),
    ]

    # Documentation files
    docs_moves = [
        ("EGRET_SYSTEM_IMPROVEMENTS.md", "docs/features/EGRET_SYSTEM_IMPROVEMENTS.md"),
        ("SYSTEM_FIXES_README.md", "docs/troubleshooting/SYSTEM_FIXES_README.md"),
        ("INSTALLATION_README.md", "docs/setup/INSTALLATION_README.md"),
    ]

    # Setup and test files
    setup_moves = [
        ("setup_environment.py", "scripts/setup/setup_environment.py"),
        ("simple_system_test.py", "scripts/testing/simple_system_test.py"),
        ("test_improvements.py", "scripts/testing/test_improvements.py"),
        ("test_model.py", "scripts/testing/test_model.py"),
        ("test_multi_egret_system.py", "scripts/testing/test_multi_egret_system.py"),
        ("test_system_fixes.py", "scripts/testing/test_system_fixes.py"),
    ]

    all_moves = config_moves + requirements_moves + docs_moves + setup_moves

    for src, dst in all_moves:
        if os.path.exists(src):
            # Create destination directory if it doesn't exist
            os.makedirs(os.path.dirname(dst), exist_ok=True)

            # Move file
            shutil.move(src, dst)
            print(f"📁 Moved: {src} → {dst}")
        else:
            print(f"⚠️  Source file not found: {src}")

def create_redirect_files():
    """Create redirect files in original locations."""

    redirects = [
        ("requirements.txt", "config/requirements.txt"),
        ("requirements-dev.txt", "config/requirements-dev.txt"),
        ("requirements-processing.txt", "config/requirements-processing.txt"),
        ("EGRET_SYSTEM_IMPROVEMENTS.md", "docs/features/EGRET_SYSTEM_IMPROVEMENTS.md"),
        ("SYSTEM_FIXES_README.md", "docs/troubleshooting/SYSTEM_FIXES_README.md"),
        ("INSTALLATION_README.md", "docs/setup/INSTALLATION_README.md"),
    ]

    for original, new_location in redirects:
        redirect_content = f"""# File Moved

This file has been moved to: `{new_location}`

Please update your references accordingly.

For quick access, you can use:
```bash
# View the file
cat {new_location}

# Edit the file
code {new_location}
```
"""
        with open(original, 'w') as f:
            f.write(redirect_content)
        print(f"📄 Created redirect file: {original}")

def main():
    """Main reorganization function."""
    print("🏗️  Starting Project Reorganization")
    print("=" * 50)

    print("\n📁 Creating new directory structure...")
    create_directories()

    print("\n📋 Moving files to appropriate locations...")
    move_files()

    print("\n🔗 Creating redirect files...")
    create_redirect_files()

    print("\n✅ Reorganization Complete!")
    print("\nNew directory structure:")
    print("""
platform-avicast/
├── config/                    # All configuration files
│   ├── requirements.txt       # Core dependencies
│   ├── requirements-dev.txt   # Development dependencies
│   ├── requirements-processing.txt  # AI/ML dependencies
│   ├── env.example           # Environment template
│   ├── egret_training_config.yaml  # ML training config
│   ├── hyp.egret.yaml        # Training hyperparameters
│   └── pyproject.toml        # Project configuration
├── docs/                     # Documentation
│   ├── setup/               # Setup guides
│   ├── features/            # Feature documentation
│   └── troubleshooting/     # Troubleshooting guides
├── scripts/                 # Scripts and tools
│   ├── setup/              # Setup scripts
│   └── testing/            # Test scripts
├── apps/                    # Django applications
├── avicast_project/         # Django project config
├── manage.py               # Django management script
├── tests/                  # Django test suite
├── media/                  # User uploaded files
├── static/                 # Static assets
├── templates/              # HTML templates
├── models/                 # ML models
├── training_data/          # Training datasets
├── venv_new/              # Virtual environment
└── README.md              # Main project README
""")

if __name__ == "__main__":
    main()
