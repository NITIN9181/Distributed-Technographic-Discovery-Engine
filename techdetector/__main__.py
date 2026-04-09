"""
Module runner for the technographic scanner.

Allows the package to be invoked with:
    python -m techdetector scan <url>
    python -m techdetector scan-batch <file>
    ...
"""

from techdetector.cli import cli

if __name__ == "__main__":
    cli()
