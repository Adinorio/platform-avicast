#!/usr/bin/env python3
"""
Git Files Analysis Script

Analyzes all files in the repository and categorizes them by size and type
to help determine what should be added to .gitignore
"""

import os
import sys
from pathlib import Path
from collections import defaultdict
import json

def get_file_info(file_path):
    """Get file information including size and type"""
    try:
        stat = file_path.stat()
        size_mb = stat.st_size / (1024 * 1024)
        extension = file_path.suffix.lower()

        # Categorize file types
        if extension in ['.pt', '.onnx', '.tflite', '.pb', '.h5', '.weights']:
            category = 'MODEL_FILES'
        elif extension in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp']:
            category = 'IMAGE_FILES'
        elif extension in ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']:
            category = 'VIDEO_FILES'
        elif extension in ['.log', '.out']:
            category = 'LOG_FILES'
        elif extension in ['.zip', '.tar.gz', '.rar', '.7z']:
            category = 'ARCHIVE_FILES'
        elif extension in ['.db', '.sqlite', '.sqlite3']:
            category = 'DATABASE_FILES'
        elif file_path.name in ['__pycache__', '.pytest_cache', '.mypy_cache']:
            category = 'CACHE_DIRS'
        else:
            category = 'OTHER'

        return {
            'path': str(file_path),
            'name': file_path.name,
            'size_mb': round(size_mb, 2),
            'extension': extension,
            'category': category
        }
    except Exception as e:
        return None

def analyze_repository(root_path):
    """Analyze all files in the repository"""
    print("🔍 ANALYZING REPOSITORY FILES...")
    print("=" * 70)

    root_path = Path(root_path)
    all_files = []
    category_stats = defaultdict(lambda: {'count': 0, 'total_size_mb': 0, 'files': []})

    # Walk through all files
    for file_path in root_path.rglob('*'):
        if file_path.is_file() and not file_path.is_symlink():
            file_info = get_file_info(file_path)
            if file_info:
                all_files.append(file_info)
                cat = file_info['category']
                category_stats[cat]['count'] += 1
                category_stats[cat]['total_size_mb'] += file_info['size_mb']
                category_stats[cat]['files'].append(file_info)

    # Sort files by size
    all_files.sort(key=lambda x: x['size_mb'], reverse=True)

    # Print summary
    print(f"📊 TOTAL FILES FOUND: {len(all_files)}")
    print()

    # Print category breakdown
    print("📂 CATEGORY BREAKDOWN:")
    print("-" * 50)
    for category, stats in sorted(category_stats.items(), key=lambda x: x[1]['total_size_mb'], reverse=True):
        print("20"
              f"{stats['count']:>5}")

    # Print largest files
    print("\n📏 LARGEST FILES (>1MB):")
    print("-" * 70)
    large_files = [f for f in all_files if f['size_mb'] > 1]
    for i, file_info in enumerate(large_files[:20], 1):
        print("2d"
              f"{file_info['category']}")

    # Analyze git status
    print("\n🔍 GIT STATUS ANALYSIS:")
    print("-" * 50)

    # Check what files are tracked vs untracked
    tracked_files = []
    untracked_files = []

    for file_info in all_files:
        file_path = Path(file_info['path'])
        relative_path = file_path.relative_to(root_path)

        # Check if file is tracked by git
        try:
            result = os.popen(f'git ls-files --error-unmatch "{relative_path}" 2>/dev/null').read().strip()
            if result:
                tracked_files.append(file_info)
            else:
                untracked_files.append(file_info)
        except:
            untracked_files.append(file_info)

    print(f"✅ TRACKED FILES: {len(tracked_files)}")
    print(f"❌ UNTRACKED FILES: {len(untracked_files)}")

    # Large untracked files that should be ignored
    large_untracked = [f for f in untracked_files if f['size_mb'] > 10]
    if large_untracked:
        print(f"\n🚨 LARGE UNTRACKED FILES (>10MB) - SHOULD BE IGNORED:")
        print("-" * 60)
        for file_info in large_untracked[:10]:
            print("6.1f"
                  f"{file_info['category']}")

    # Generate .gitignore recommendations
    print("\n📝 .GITIGNORE RECOMMENDATIONS:")
    print("-" * 50)

    recommendations = []

    # Model files
    model_extensions = ['.pt', '.onnx', '.tflite', '.pb', '.h5', '.weights']
    model_files = [f for f in all_files if f['extension'] in model_extensions and f['size_mb'] > 1]
    if model_files:
        recommendations.append("# Model files (VERY LARGE)")
        for ext in ['*.pt', '*.onnx', '*.tflite', '*.pb', '*.h5', '*.weights']:
            recommendations.append(ext)

    # Training artifacts
    training_dirs = ['runs/', 'checkpoints/', 'weights/', 'logs/', 'wandb/', 'mlruns/']
    if any('runs' in f['path'] or 'checkpoint' in f['path'] or 'weight' in f['path']
           for f in all_files):
        recommendations.append("# Training artifacts")
        recommendations.extend(training_dirs)

    # Large media files
    media_files = [f for f in all_files if f['category'] in ['VIDEO_FILES', 'IMAGE_FILES'] and f['size_mb'] > 5]
    if media_files:
        recommendations.append("# Large media files")
        recommendations.extend(['*.mp4', '*.avi', '*.mov', '*.mkv', '*.jpg', '*.png'])

    # Print recommendations
    for rec in recommendations:
        print(f"   {rec}")

    # Save detailed analysis
    analysis_data = {
        'summary': {
            'total_files': len(all_files),
            'total_size_mb': sum(f['size_mb'] for f in all_files),
            'tracked_files': len(tracked_files),
            'untracked_files': len(untracked_files),
            'large_files_over_10mb': len([f for f in all_files if f['size_mb'] > 10])
        },
        'categories': dict(category_stats),
        'largest_files': [f for f in all_files if f['size_mb'] > 10][:20],
        'gitignore_recommendations': recommendations
    }

    with open('git_analysis_report.json', 'w') as f:
        json.dump(analysis_data, f, indent=2)

    print("\n💾 Detailed analysis saved to: git_analysis_report.json")
    print(f"📊 Repository contains {len(all_files)} files totaling {sum(f['size_mb'] for f in all_files):.1f} MB")

def main():
    """Main analysis function"""
    if len(sys.argv) > 1:
        root_path = sys.argv[1]
    else:
        root_path = '.'

    analyze_repository(root_path)

if __name__ == "__main__":
    main()
