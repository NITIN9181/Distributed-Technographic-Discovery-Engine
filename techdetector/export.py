"""
Export detection data in various formats.
"""
import json
import csv
from typing import Iterator
from techdetector.storage import query_detections

def export_json(filepath: str, filters: dict):
    """Export to JSON file."""
    data = query_detections(filters)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def export_csv(filepath: str, filters: dict):
    """Export to CSV file."""
    # Columns: domain, technology, category, vector, first_detected, last_verified
    data = query_detections(filters)
    if not data:
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["canonical_domain", "technology_id", "category", "detection_vector", "first_detected_at", "last_verified_at", "evidence"])
        return

    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            "canonical_domain", "technology_id", "category", 
            "detection_vector", "first_detected_at", "last_verified_at", "evidence"
        ])
        writer.writeheader()
        writer.writerows(data)
