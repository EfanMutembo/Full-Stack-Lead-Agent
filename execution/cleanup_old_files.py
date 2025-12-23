"""
Clean up redundant temporary files from old workflows.

This script removes old test files, validation reports, and campaign files
that are no longer needed after implementing personalization segmentation.

Usage:
    python cleanup_old_files.py --dry-run  # Preview what will be deleted
    python cleanup_old_files.py            # Actually delete files
"""

import os
import sys
import argparse

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def cleanup_old_files(dry_run=True):
    """
    Remove redundant files from .tmp directory.

    Args:
        dry_run (bool): If True, only print what would be deleted

    Returns:
        dict: Summary of cleanup operation
    """

    # Files to delete (organized by category)
    files_to_delete = {
        "Old test/validation files": [
            ".tmp/test_80_leads.json",
            ".tmp/test_80_filtered.json",
            ".tmp/test_80_filter_report.json",
            ".tmp/test_80_validation_report.json",
            ".tmp/test_80_segment_mapping.json",
            ".tmp/test_leads_v2.json",
            ".tmp/test_validation_batched.json",
            ".tmp/test_validation_with_new_params.json",
            ".tmp/test_percentage_validation.json",
            ".tmp/test_normalize_batch50.json",
            ".tmp/test_campaign_html.json",
            ".tmp/validation_report_v2.json",
            ".tmp/validation_report_v3.json",
        ],
        "Old campaign files (before segmentation)": [
            ".tmp/campaign_copy_dormant_leads_revival.json",
            ".tmp/campaign_copy_home_battery_storage.json",
            ".tmp/campaign_copy_reactivation.json",
            ".tmp/campaign_copy_exec.json",
            ".tmp/campaign_copy_creative.json",
            ".tmp/campaign_ids.json",
            ".tmp/upload_report.json",
            ".tmp/upload_report_final.json",
        ],
        "Old workflow files (before CSV import)": [
            ".tmp/full_leads.json",
            ".tmp/full_leads_filtered.json",
            ".tmp/full_leads_normalized.json",
            ".tmp/full_validation_report.json",
            ".tmp/filter_report.json",
            ".tmp/validation_report.json",
            ".tmp/test_leads.json",
            ".tmp/segment_mapping.json",
            ".tmp/segment_exec_leads.json",
            ".tmp/segment_creative_leads.json",
        ],
    }

    deleted_count = 0
    skipped_count = 0
    total_size = 0

    print("🧹 Cleaning up redundant files...\n")

    for category, files in files_to_delete.items():
        print(f"📁 {category}:")

        for filepath in files:
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                total_size += file_size
                size_kb = file_size / 1024

                if dry_run:
                    print(f"   ⚠️  Would delete: {filepath} ({size_kb:.1f} KB)")
                else:
                    try:
                        os.remove(filepath)
                        print(f"   ✅ Deleted: {filepath} ({size_kb:.1f} KB)")
                        deleted_count += 1
                    except Exception as e:
                        print(f"   ❌ Error deleting {filepath}: {str(e)}")
                        skipped_count += 1
            else:
                # File already deleted or doesn't exist
                skipped_count += 1

        print()

    # Summary
    total_mb = total_size / (1024 * 1024)

    print("=" * 60)
    if dry_run:
        print("🔍 DRY RUN - No files were actually deleted")
        print(f"   Would delete: {deleted_count} files")
        print(f"   Would free: {total_mb:.2f} MB")
        print("\nRun without --dry-run to actually delete files")
    else:
        print("✅ Cleanup complete!")
        print(f"   Deleted: {deleted_count} files")
        print(f"   Freed: {total_mb:.2f} MB")
        print(f"   Skipped: {skipped_count} files (already deleted or errors)")
    print("=" * 60)

    return {
        "deleted": deleted_count,
        "skipped": skipped_count,
        "total_size_mb": total_mb,
        "dry_run": dry_run
    }


def main():
    parser = argparse.ArgumentParser(description='Clean up redundant temporary files')
    parser.add_argument('--dry-run', action='store_true', help='Preview what will be deleted without actually deleting')

    args = parser.parse_args()

    result = cleanup_old_files(dry_run=args.dry_run)

    # Exit code
    sys.exit(0)


if __name__ == '__main__':
    main()
