#!/usr/bin/env python3
"""
HTML Encoding Converter Tool

Processes HTML files recursively in a directory:

1. Reads HTML files using UTF-8 / fallback encodings
2. Converts charset declarations to UTF-8
3. Adds <meta charset="UTF-8"> when missing
4. Replaces .htm references with .html
5. Replaces chrsouchon.free.fr with chrsouchon.fr
6. Beautifies HTML
7. Writes files as UTF-8
8. Renames .htm files to .html
9. Works on Windows, Linux and macOS

Requirements:
    pip install beautifulsoup4

Usage:
    python html_converter_tool.py <directory>

Examples:
    python html_converter_tool.py .
    python html_converter_tool.py . --no-backup
    python html_converter_tool.py "C:\\Users\\chrso\\Desktop\\Barzaz"
"""

import sys
import argparse
import re
import shutil
from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup


class HTMLConverter:
    def __init__(self, directory: str, backup: bool = True):
        self.directory = Path(directory).resolve()
        self.backup = backup
        self.processed_files = []
        self.errors = []

    # ------------------------------------------------------------------
    # Reading
    # ------------------------------------------------------------------

    def read_file_content(self, file_path: Path) -> Optional[str]:
        """Read a file using sensible encoding fallbacks."""

        encodings_to_try = [
            "utf-8-sig",
            "utf-8",
            "cp1252",
            "iso-8859-1",
            "latin1",
        ]

        for encoding in encodings_to_try:
            try:
                with file_path.open("r", encoding=encoding) as f:
                    content = f.read()

                print(f"  Read with encoding: {encoding}")
                return content

            except UnicodeDecodeError:
                continue

            except OSError as e:
                self.errors.append(
                    f"Could not read {file_path}: {e}"
                )
                return None

        # Last resort
        try:
            raw_content = file_path.read_bytes()
            content = raw_content.decode("utf-8", errors="replace")
            print("  Read with UTF-8 error replacement")
            return content

        except OSError as e:
            self.errors.append(
                f"Could not read {file_path}: {e}"
            )
            return None

    # ------------------------------------------------------------------
    # Charset
    # ------------------------------------------------------------------

    def fix_charset_declarations(self, content: str) -> str:
        """Convert charset declarations to UTF-8."""

        # <meta charset="ISO-8859-1">
        content = re.sub(
            r'(<meta\b[^>]*\bcharset\s*=\s*[\'"]?)[^\'">\s]+',
            r'\1UTF-8',
            content,
            flags=re.IGNORECASE,
        )

        # <meta http-equiv="Content-Type"
        #       content="text/html; charset=ISO-8859-1">
        content = re.sub(
            r'(\bcontent\s*=\s*[\'"][^\'"]*?\bcharset\s*=\s*)'
            r'[^\'";\s]+',
            r'\1UTF-8',
            content,
            flags=re.IGNORECASE,
        )

        # charset=ISO-8859-1 without quotes around the attribute
        content = re.sub(
            r'(\bcharset\s*=\s*)[^\s;>"\']+',
            r'\1UTF-8',
            content,
            flags=re.IGNORECASE,
        )

        # XML declaration
        content = re.sub(
            r'(<\?xml\b[^>]*\bencoding\s*=\s*[\'"]?)[^\'">\s]+',
            r'\1UTF-8',
            content,
            flags=re.IGNORECASE,
        )

        # Check whether a charset declaration now exists
        if not re.search(r'\bcharset\s*=', content, re.IGNORECASE):
            content = self.add_utf8_charset(content)

        return content

    def add_utf8_charset(self, content: str) -> str:
        """Add UTF-8 meta declaration."""

        utf8_meta = '<meta charset="UTF-8">'

        # Prefer <head>
        match = re.search(
            r'<head\b[^>]*>',
            content,
            flags=re.IGNORECASE,
        )

        if match:
            position = match.end()
            return (
                content[:position]
                + "\n    "
                + utf8_meta
                + content[position:]
            )

        # If there is no <head>, create one after <html>
        match = re.search(
            r'<html\b[^>]*>',
            content,
            flags=re.IGNORECASE,
        )

        if match:
            position = match.end()
            return (
                content[:position]
                + "\n<head>\n    "
                + utf8_meta
                + "\n</head>"
                + content[position:]
            )

        # Last resort
        return utf8_meta + "\n" + content

    # ------------------------------------------------------------------
    # URL / extension replacement
    # ------------------------------------------------------------------

    def replace_htm_with_html(self, content: str) -> str:
       """Replace every .htm extension with .html."""
       return re.sub(
           r'\.htm\b',
           '.html',
           content,
           flags=re.IGNORECASE
       )


    # ------------------------------------------------------------------
    # Domain replacement
    # ------------------------------------------------------------------

    def replace_chrsouchon_domain(self, content: str) -> str:
        """Replace old domain with new domain."""

        return re.sub(
            r'\bchrsouchon\.free\.fr\b',
            'chrsouchon.fr',
            content,
            flags=re.IGNORECASE,
        )

    # ------------------------------------------------------------------
    # Beautification
    # ------------------------------------------------------------------

    def beautify_html(self, content: str) -> str:
        """Beautify HTML using BeautifulSoup."""

        try:
            soup = BeautifulSoup(content, "html.parser")

            # BeautifulSoup's prettify uses two spaces by default.
            pretty_html = soup.prettify(
                formatter="html"
            )

            return pretty_html

        except Exception as e:
            print(
                f"  Warning: Could not beautify HTML: {e}"
            )
            print("  Keeping original formatting.")
            return content

    # ------------------------------------------------------------------
    # Backup
    # ------------------------------------------------------------------

    def create_backup(self, file_path: Path) -> Optional[Path]:
        """Create a .backup copy."""

        if not self.backup:
            return None

        backup_path = file_path.with_name(
            file_path.name + ".backup"
        )

        try:
            shutil.copy2(file_path, backup_path)
            print(f"  Backup: {backup_path.name}")
            return backup_path

        except OSError as e:
            self.errors.append(
                f"Could not create backup for {file_path}: {e}"
            )
            return None

    # ------------------------------------------------------------------
    # Processing
    # ------------------------------------------------------------------

    def process_file(self, file_path: Path) -> bool:
        """Process one HTML file."""

        print(f"\nProcessing: {file_path}")

        content = self.read_file_content(file_path)

        if content is None:
            return False

        # Backup original BEFORE modifying anything
        self.create_backup(file_path)

        # Apply transformations
        content = self.fix_charset_declarations(content)
        content = self.replace_htm_with_html(content)
        content = self.replace_chrsouchon_domain(content)

        print("  Beautifying HTML...")
        content = self.beautify_html(content)

        # Determine output filename
        if file_path.suffix.lower() == ".htm":
            output_path = file_path.with_suffix(".html")
        else:
            output_path = file_path

        try:
            # Write UTF-8
            with output_path.open(
                "w",
                encoding="utf-8",
                newline="\n",
            ) as f:
                f.write(content)

            # If .htm -> .html, remove original
            if output_path != file_path:
                try:
                    file_path.unlink()
                except OSError as e:
                    self.errors.append(
                        f"Could not remove original {file_path}: {e}"
                    )
                    return False

                print(
                    f"  Renamed: {file_path.name} -> "
                    f"{output_path.name}"
                )

            else:
                print(f"  Updated: {output_path.name}")

            print("  Saved as UTF-8")

            self.processed_files.append(output_path)
            return True

        except OSError as e:
            self.errors.append(
                f"Error writing {output_path}: {e}"
            )
            return False

    # ------------------------------------------------------------------
    # File discovery
    # ------------------------------------------------------------------

    def find_html_files(self) -> list[Path]:
        """
        Find HTML files recursively.

        Uses pathlib rather than the Unix 'find' command so that
        this works correctly on Windows, Linux and macOS.
        """

        html_files = []

        try:
            for path in self.directory.rglob("*"):
                if not path.is_file():
                    continue

                # Ignore our own backup files
                if path.name.lower().endswith(".backup"):
                    continue

                if path.suffix.lower() in {".htm", ".html"}:
                    html_files.append(path)

        except OSError as e:
            self.errors.append(
                f"Error searching directory: {e}"
            )

        return sorted(
            html_files,
            key=lambda p: str(p).lower()
        )

    # ------------------------------------------------------------------
    # Directory conversion
    # ------------------------------------------------------------------

    def convert_directory(self) -> dict:
        """Process all HTML files recursively."""

        if not self.directory.exists():
            return {
                "success": False,
                "error": (
                    f"Directory does not exist: "
                    f"{self.directory}"
                ),
            }

        if not self.directory.is_dir():
            return {
                "success": False,
                "error": (
                    f"Path is not a directory: "
                    f"{self.directory}"
                ),
            }

        html_files = self.find_html_files()

        if not html_files:
            return {
                "success": True,
                "message": (
                    "No .htm or .html files found "
                    f"under {self.directory}"
                ),
                "processed": 0,
                "total_found": 0,
                "processed_files": [],
                "errors": self.errors,
            }

        print(
            f"Found {len(html_files)} HTML file(s) to process."
        )

        successful = 0

        for file_path in html_files:
            if self.process_file(file_path):
                successful += 1

        return {
            "success": True,
            "processed": successful,
            "total_found": len(html_files),
            "processed_files": [
                str(f) for f in self.processed_files
            ],
            "errors": self.errors,
        }


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Convert HTML files to UTF-8, replace .htm "
            "with .html, update the domain, and beautify HTML."
        )
    )

    parser.add_argument(
        "directory",
        help="Directory containing HTML files",
    )

    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not create .backup files",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show processed files",
    )

    args = parser.parse_args()

    directory = Path(args.directory).expanduser().resolve()

    print("HTML Encoding Converter")
    print(f"Target directory: {directory}")
    print(
        f"Backup files: "
        f"{'No' if args.no_backup else 'Yes'}"
    )
    print("-" * 60)

    converter = HTMLConverter(
        directory,
        backup=not args.no_backup,
    )

    result = converter.convert_directory()

    print("\n" + "-" * 60)

    if not result["success"]:
        print(f"ERROR: {result['error']}")
        sys.exit(1)

    if "message" in result:
        print(result["message"])
        sys.exit(0)

    print("Processing complete!")
    print(
        f"Files processed: "
        f"{result['processed']}/{result['total_found']}"
    )

    if result["errors"]:
        print(
            f"\nErrors encountered "
            f"({len(result['errors'])}):"
        )

        for error in result["errors"]:
            print(f"  - {error}")

    if args.verbose and result["processed_files"]:
        print("\nProcessed files:")

        for file_path in result["processed_files"]:
            print(f"  - {file_path}")

    # Return failure if any file had an error
    if result["errors"]:
        sys.exit(2)


if __name__ == "__main__":
    main()
