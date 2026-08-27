#!/usr/bin/env python3
"""
Directory Cleanup Tool - Find and manage unnecessary files
"""

import os
import hashlib
import argparse
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timedelta
import sys

class DirectoryCleanup:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.unnecessary_files = []
        
        # Define patterns for unnecessary files
        self.temp_extensions = {
            '.tmp', '.temp', '.bak', '.backup', '.old', '.orig', '.swp', '.swo',
            '.~', '.cache', '.log', '.pid', '.lock', '.DS_Store', 'Thumbs.db'
        }
        
        self.temp_patterns = {
            '~$', '.crdownload', '.part', '.partial', '.downloading'
        }
        
        # Define large file threshold (in MB)
        self.large_file_threshold = 100 * 1024 * 1024  # 100MB
        
    def scan_directory(self, recursive=True):
        """Scan directory for all files"""
        if recursive:
            return list(self.directory.rglob('*'))
        else:
            return list(self.directory.glob('*'))
    
    def find_temp_files(self, files):
        """Find temporary and backup files"""
        temp_files = []
        for file_path in files:
            if file_path.is_file():
                # Check extension
                if file_path.suffix.lower() in self.temp_extensions:
                    temp_files.append(('temp_extension', file_path))
                
                # Check filename patterns
                filename = file_path.name.lower()
                for pattern in self.temp_patterns:
                    if filename.endswith(pattern):
                        temp_files.append(('temp_pattern', file_path))
                        break
        
        return temp_files
    
    def find_duplicates(self, files):
        """Find duplicate files based on content hash"""
        hash_map = defaultdict(list)
        duplicates = []
        
        for file_path in files:
            if file_path.is_file():
                try:
                    file_hash = self.get_file_hash(file_path)
                    hash_map[file_hash].append(file_path)
                except (OSError, IOError):
                    continue
        
        # Find duplicates
        for file_hash, file_list in hash_map.items():
            if len(file_list) > 1:
                # Keep the first file, mark others as duplicates
                for duplicate in file_list[1:]:
                    duplicates.append(('duplicate', duplicate))
        
        return duplicates
    
    def find_large_files(self, files):
        """Find unusually large files"""
        large_files = []
        for file_path in files:
            if file_path.is_file():
                try:
                    if file_path.stat().st_size > self.large_file_threshold:
                        large_files.append(('large_file', file_path))
                except (OSError, IOError):
                    continue
        
        return large_files
    
    def find_old_files(self, files, days_old=365):
        """Find files older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        old_files = []
        
        for file_path in files:
            if file_path.is_file():
                try:
                    mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if mod_time < cutoff_date:
                        old_files.append(('old_file', file_path))
                except (OSError, IOError):
                    continue
        
        return old_files
    
    def find_empty_files(self, files):
        """Find empty files and directories"""
        empty_items = []
        
        for file_path in files:
            try:
                if file_path.is_file() and file_path.stat().st_size == 0:
                    empty_items.append(('empty_file', file_path))
                elif file_path.is_dir() and not any(file_path.iterdir()):
                    empty_items.append(('empty_dir', file_path))
            except (OSError, IOError):
                continue
        
        return empty_items
    
    def get_file_hash(self, file_path):
        """Calculate MD5 hash of file content"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def format_size(self, size_bytes):
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    def analyze(self, find_duplicates=True, find_large=True, find_old=True, 
                find_empty=True, old_days=365, recursive=True):
        """Run complete analysis"""
        print(f"Analyzing directory: {self.directory}")
        print("-" * 50)
        
        # Get all files
        all_items = self.scan_directory(recursive)
        files_only = [f for f in all_items if f.is_file()]
        
        print(f"Found {len(files_only)} files to analyze...")
        
        results = {}
        
        # Find temporary files
        print("🗑️  Finding temporary files...")
        temp_files = self.find_temp_files(all_items)
        results['temp'] = temp_files
        
        # Find duplicates
        if find_duplicates:
            print("📝 Finding duplicate files...")
            duplicates = self.find_duplicates(files_only)
            results['duplicates'] = duplicates
        
        # Find large files
        if find_large:
            print("📦 Finding large files...")
            large_files = self.find_large_files(files_only)
            results['large'] = large_files
        
        # Find old files
        if find_old:
            print(f"📅 Finding files older than {old_days} days...")
            old_files = self.find_old_files(files_only, old_days)
            results['old'] = old_files
        
        # Find empty files/dirs
        if find_empty:
            print("📭 Finding empty files and directories...")
            empty_items = self.find_empty_files(all_items)
            results['empty'] = empty_items
        
        return results
    
    def print_results(self, results):
        """Print analysis results"""
        print("\n" + "="*60)
        print("ANALYSIS RESULTS")
        print("="*60)
        
        total_unnecessary = 0
        total_size = 0
        
        for category, items in results.items():
            if not items:
                continue
                
            print(f"\n{category.upper()} FILES ({len(items)} found):")
            print("-" * 40)
            
            category_size = 0
            for file_type, file_path in items[:10]:  # Show first 10
                try:
                    size = file_path.stat().st_size if file_path.is_file() else 0
                    category_size += size
                    total_size += size
                    print(f"  {self.format_size(size):>10} - {file_path}")
                except (OSError, IOError):
                    print(f"  {'N/A':>10} - {file_path}")
            
            total_unnecessary += len(items)
            
            if len(items) > 10:
                print(f"  ... and {len(items) - 10} more files")
            
            print(f"  Category total: {self.format_size(category_size)}")
        
        print(f"\n{'='*60}")
        print(f"SUMMARY:")
        print(f"Total unnecessary files: {total_unnecessary}")
        print(f"Total space that could be freed: {self.format_size(total_size)}")
        print(f"{'='*60}")
    
    def save_report(self, results, output_file="cleanup_report.txt"):
        """Save detailed report to file"""
        with open(output_file, 'w') as f:
            f.write(f"Directory Cleanup Report\n")
            f.write(f"Generated: {datetime.now()}\n")
            f.write(f"Directory: {self.directory}\n")
            f.write("="*60 + "\n\n")
            
            for category, items in results.items():
                if not items:
                    continue
                    
                f.write(f"{category.upper()} FILES ({len(items)} found):\n")
                f.write("-" * 40 + "\n")
                
                for file_type, file_path in items:
                    try:
                        size = file_path.stat().st_size if file_path.is_file() else 0
                        f.write(f"{self.format_size(size):>10} - {file_path}\n")
                    except (OSError, IOError):
                        f.write(f"{'N/A':>10} - {file_path}\n")
                
                f.write("\n")
        
        print(f"📄 Detailed report saved to: {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Find unnecessary files in a directory")
    parser.add_argument("directory", help="Directory to analyze")
    parser.add_argument("--no-duplicates", action="store_true", 
                       help="Skip duplicate file detection")
    parser.add_argument("--no-large", action="store_true", 
                       help="Skip large file detection")
    parser.add_argument("--no-old", action="store_true", 
                       help="Skip old file detection")
    parser.add_argument("--no-empty", action="store_true", 
                       help="Skip empty file detection")
    parser.add_argument("--old-days", type=int, default=365, 
                       help="Consider files older than this many days as old (default: 365)")
    parser.add_argument("--large-mb", type=int, default=100, 
                       help="Consider files larger than this many MB as large (default: 100)")
    parser.add_argument("--no-recursive", action="store_true", 
                       help="Don't scan subdirectories")
    parser.add_argument("--report", type=str, 
                       help="Save detailed report to file")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.directory):
        print(f"Error: Directory '{args.directory}' does not exist.")
        sys.exit(1)
    
    # Create cleanup tool
    cleanup = DirectoryCleanup(args.directory)
    cleanup.large_file_threshold = args.large_mb * 1024 * 1024
    
    # Run analysis
    results = cleanup.analyze(
        find_duplicates=not args.no_duplicates,
        find_large=not args.no_large,
        find_old=not args.no_old,
        find_empty=not args.no_empty,
        old_days=args.old_days,
        recursive=not args.no_recursive
    )
    
    # Print results
    cleanup.print_results(results)
    
    # Save report if requested
    if args.report:
        cleanup.save_report(results, args.report)

if __name__ == "__main__":
    main()
