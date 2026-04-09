"""
Module runner for the technographic scanner.

Allows the package to be invoked with:
    python -m techdetector <url>
    python -m techdetector --query <domain>
    python -m techdetector --list-companies
"""

from techdetector.scanner import main

if __name__ == "__main__":
    main()
