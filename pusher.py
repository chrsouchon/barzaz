#!/.venv/bin/python

from git import Repo # documentation: https://gitpython.readthedocs.io/en/stable/tutorial.html
import os
import fileextension
import time
import subprocess
import argparse
from datetime import datetime, timedelta

def format_time(seconds):
    """Format time in a human-readable way"""
    if seconds < 1:
        return f"{seconds:.2f}s"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    else:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{int(minutes)}m {remaining_seconds:.1f}s"

def process_files_in_batches(files, batch_size, file_type="files"):
    """Process files in batches of specified size"""
    for i in range(0, len(files), batch_size):
        batch = files[i:i + batch_size]
        yield batch

def main():
    script_start_time = time.time()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Git pusher with batch support and configurable intervals')
    parser.add_argument('--batch-size', '-b', type=int, default=1, 
                       help='Number of files to process in each batch (default: 1)')
    parser.add_argument('--interval', '-i', type=float, default=1.0,
                       help='Sleep interval in seconds between batches (default: 1.0)')
    parser.add_argument('--lfs', action='store_true', default=True,
                       help='Enable LFS for large files (default: enabled)')
    parser.add_argument('--no-lfs', dest='lfs', action='store_false',
                       help='Disable LFS - treat all files as regular files')
    args = parser.parse_args()
    
    batch_size = args.batch_size
    sleep_interval = args.interval
    use_lfs = args.lfs
    
    print(f"🚀 Starting Git pusher at {datetime.now().strftime('%H:%M:%S')}")
    print(f"📦 Using batch size: {batch_size}")
    print(f"⏱️  Sleep interval: {format_time(sleep_interval)} between batches")
    print(f"🔧 LFS mode: {'Enabled' if use_lfs else 'Disabled'}")
    print("-" * 50)
    
    # Initialize timing variables
    total_files_processed = 0
    total_commits = 0
    batch_times = []
    
    setup_start = time.time()
    repo = Repo(os.getcwd())
    repo.git.pull("origin", "master")
    
    # Only set up LFS if enabled
    if use_lfs:
        try:
            repo.git.lfs("install")
            repo.git.add(".gitattributes")
            repo.git.commit(m="Add .gitattributes")
            repo.git.push("origin", "master")
        except:
            print("✓ LFS already installed.")
    else:
        print("⚠️  LFS disabled - all files will be processed as regular files")
    
    try:
        repo.git.add("pusher.py")
        repo.git.commit(m="Add pusher.py")
        repo.git.push("origin", "master")
    except:
        print("✓ pusher.py already added.")
    
    file_list = os.listdir(os.getcwd())
    if ".obsidian" in file_list:
        try:
            repo.git.add(".obsidian")
            repo.git.commit(m="Add .obsidian")
            repo.git.push("origin", "master")
        except:
            print("✓ .obsidian already added.")
    
    setup_time = time.time() - setup_start
    print(f"⚙️  Setup completed in {format_time(setup_time)}")
    
    # Get LFS file extensions only if LFS is enabled
    if use_lfs:
        lfs_files = fileextension.main()
    else:
        lfs_files = []  # Empty list means no files will be treated as LFS
    
    untracked_array = []
    untracked_lfs_array = []
    
    if repo.untracked_files:
        analysis_start = time.time()
        for untracked in repo.untracked_files:
            if use_lfs and untracked.endswith(tuple(lfs_files)):
                untracked_lfs_array.append(untracked)
            else:
                untracked_array.append(untracked)
        
        analysis_time = time.time() - analysis_start
        print(f"🔍 File analysis completed in {format_time(analysis_time)}")
        
        # Print what will be processed
        print(f"📄 Regular files ({len(untracked_array)}):")
        for untracked in untracked_array:
            print(f"  {untracked}")
        
        if use_lfs and untracked_lfs_array:
            print(f"📦 LFS files ({len(untracked_lfs_array)}):")
            for untracked in untracked_lfs_array:
                print(f"  lfs {untracked}")
        
        # Process regular files in batches
        if untracked_array:
            regular_start = time.time()
            print(f"\n📄 Processing {len(untracked_array)} regular files in batches of {batch_size}...")
            
            for batch_num, batch in enumerate(process_files_in_batches(untracked_array, batch_size), 1):
                batch_start = time.time()
                print(f"\n  Batch {batch_num}/{(len(untracked_array) + batch_size - 1) // batch_size}: {len(batch)} files")
                
                # Add all files in batch
                add_start = time.time()
                for file in batch:
                    print(f"    📁 Adding {file}...")
                    repo.git.add(file)
                add_time = time.time() - add_start
                
                # Create commit message
                if len(batch) == 1:
                    commit_msg = f"Add {batch[0]}"
                else:
                    commit_msg = f"Add {len(batch)} files: {', '.join(batch)}"
                
                commit_start = time.time()
                print(f"    💾 Committing batch...")
                repo.git.commit(m=commit_msg)
                commit_time = time.time() - commit_start
                
                push_start = time.time()
                print(f"    ⬆️  Pushing batch...")
                repo.git.push("origin", "master")
                push_time = time.time() - push_start
                
                batch_total_time = time.time() - batch_start
                batch_times.append(batch_total_time)
                total_files_processed += len(batch)
                total_commits += 1
                
                print(f"    ⏱️  Batch timing: add={format_time(add_time)}, commit={format_time(commit_time)}, push={format_time(push_time)}, total={format_time(batch_total_time)}")
                
                # Sleep between batches (skip for last batch)
                if batch_num < (len(untracked_array) + batch_size - 1) // batch_size:
                    if sleep_interval > 0:
                        print(f"    💤 Sleeping for {format_time(sleep_interval)}...")
                        time.sleep(sleep_interval)
            
            regular_time = time.time() - regular_start
            print(f"✅ Regular files completed in {format_time(regular_time)}")
        
        # Process LFS files in batches (only if LFS is enabled)
        if use_lfs and untracked_lfs_array:
            lfs_start = time.time()
            print(f"\n📦 Processing {len(untracked_lfs_array)} LFS files in batches of {batch_size}...")
            
            for batch_num, batch in enumerate(process_files_in_batches(untracked_lfs_array, batch_size), 1):
                batch_start = time.time()
                print(f"\n  LFS Batch {batch_num}/{(len(untracked_lfs_array) + batch_size - 1) // batch_size}: {len(batch)} files")
                
                # Track all files in batch with LFS
                track_start = time.time()
                for file in batch:
                    print(f"    🎯 Tracking {file} with LFS...")
                    subprocess.run(["git", "lfs", "track", file])
                track_time = time.time() - track_start
                
                # Add all files in batch
                add_start = time.time()
                for file in batch:
                    print(f"    📁 Adding {file}...")
                    repo.git.add(file)
                add_time = time.time() - add_start
                
                # Create commit message
                if len(batch) == 1:
                    commit_msg = f"Add {batch[0]} (LFS)"
                else:
                    commit_msg = f"Add {len(batch)} LFS files: {', '.join(batch)}"
                
                commit_start = time.time()
                print(f"    💾 Committing LFS batch...")
                repo.git.commit(m=commit_msg)
                commit_time = time.time() - commit_start
                
                push_start = time.time()
                print(f"    ⬆️  Pushing LFS batch...")
                repo.git.push("origin", "master")
                push_time = time.time() - push_start
                
                batch_total_time = time.time() - batch_start
                batch_times.append(batch_total_time)
                total_files_processed += len(batch)
                total_commits += 1
                
                print(f"    ⏱️  Batch timing: track={format_time(track_time)}, add={format_time(add_time)}, commit={format_time(commit_time)}, push={format_time(push_time)}, total={format_time(batch_total_time)}")
                
                # Sleep between batches (skip for last batch)
                if batch_num < (len(untracked_lfs_array) + batch_size - 1) // batch_size:
                    if sleep_interval > 0:
                        print(f"    💤 Sleeping for {format_time(sleep_interval)}...")
                        time.sleep(sleep_interval)
            
            lfs_time = time.time() - lfs_start
            print(f"✅ LFS files completed in {format_time(lfs_time)}")
    
    else:
        print("ℹ️  No untracked files.")
        
        # Handle modified files
        diffs = repo.index.diff(None)
        if diffs:
            modified_start = time.time()
            modified_files = [d.a_path for d in diffs]
            
            # Print what will be processed
            print(f"📝 Modified files ({len(modified_files)}):")
            for d in diffs:
                print(f"  {d.a_path}")
            
            print(f"\n📝 Processing {len(modified_files)} modified files in batches of {batch_size}...")
            
            # Process modified files in batches
            for batch_num, batch in enumerate(process_files_in_batches(modified_files, batch_size), 1):
                batch_start = time.time()
                print(f"\n  Modified Batch {batch_num}/{(len(modified_files) + batch_size - 1) // batch_size}: {len(batch)} files")
                
                # Add all files in batch
                add_start = time.time()
                for file in batch:
                    print(f"    📁 Adding {file}...")
                    repo.git.add(file)
                add_time = time.time() - add_start
                
                # Create commit message
                if len(batch) == 1:
                    commit_msg = f"Update {batch[0]}"
                else:
                    commit_msg = f"Update {len(batch)} files: {', '.join(batch)}"
                
                commit_start = time.time()
                print(f"    💾 Committing batch...")
                repo.git.commit(m=commit_msg)
                commit_time = time.time() - commit_start
                
                push_start = time.time()
                print(f"    ⬆️  Pushing batch...")
                repo.git.push("origin", "master")
                push_time = time.time() - push_start
                
                batch_total_time = time.time() - batch_start
                batch_times.append(batch_total_time)
                total_files_processed += len(batch)
                total_commits += 1
                
                print(f"    ⏱️  Batch timing: add={format_time(add_time)}, commit={format_time(commit_time)}, push={format_time(push_time)}, total={format_time(batch_total_time)}")
                
                # Sleep between batches (skip for last batch)
                if batch_num < (len(modified_files) + batch_size - 1) // batch_size:
                    if sleep_interval > 0:
                        print(f"    💤 Sleeping for {format_time(sleep_interval)}...")
                        time.sleep(sleep_interval)
            
            modified_time = time.time() - modified_start
            print(f"✅ Modified files completed in {format_time(modified_time)}")
        else:
            print("ℹ️  No modified files to process.")
    
    # Final summary
    script_total_time = time.time() - script_start_time
    
    print("\n" + "=" * 60)
    print("📊 PERFORMANCE SUMMARY")
    print("=" * 60)
    print(f"🕐 Total execution time: {format_time(script_total_time)}")
    print(f"📁 Files processed: {total_files_processed}")
    print(f"💾 Commits created: {total_commits}")
    print(f"⏱️  Sleep interval used: {format_time(sleep_interval)}")
    print(f"🔧 LFS mode: {'Enabled' if use_lfs else 'Disabled'}")
    
    if batch_times:
        avg_batch_time = sum(batch_times) / len(batch_times)
        min_batch_time = min(batch_times)
        max_batch_time = max(batch_times)
        
        print(f"📦 Batches processed: {len(batch_times)}")
        print(f"⏱️  Average batch time: {format_time(avg_batch_time)}")
        print(f"🏃 Fastest batch: {format_time(min_batch_time)}")
        print(f"🐌 Slowest batch: {format_time(max_batch_time)}")
        
        if total_files_processed > 0:
            files_per_second = total_files_processed / script_total_time
            print(f"📈 Processing rate: {files_per_second:.2f} files/second")
    
    print(f"🏁 Completed at {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 60)

if __name__ == "__main__":
    main()
