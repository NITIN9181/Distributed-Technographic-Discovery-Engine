"""
NLP-based technology extraction from job postings.
"""
import logging
import spacy
from typing import List
from techdetector.models import Detection, DetectionVector, Technology

logger = logging.getLogger(__name__)

class JobPostingDetector:
    def __init__(self, signatures: list[dict]):
        logger.info("Initializing NLP model...")
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("en_core_web_sm not found, downloading temporarily via spacy.cli...")
            from spacy.cli import download
            download("en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")
            
        self.signatures = []
        for s in signatures:
            if 'job_posting' in s.get('detection_vectors', {}):
                tech = Technology(id=s['id'], name=s['name'], category=s['category'])
                self.signatures.append({
                    'technology': tech,
                    'patterns': s['detection_vectors']['job_posting']
                })
    
    def detect(self, career_text: str) -> list[Detection]:
        """
        Extract technologies mentioned in job posting text.
        """
        detections = []
        
        # Limit text length to avoid NLP pipeline slowness on huge aggregated pages
        if len(career_text) > 100000:
            career_text = career_text[:100000]
            
        doc = self.nlp(career_text)
        text_lower = career_text.lower()
        
        for sig in self.signatures:
            patterns = sig['patterns']
            detected = False
            evidence = ""
            
            # 1. Simple Keyword Match in text
            if 'keywords' in patterns:
                for kw in patterns['keywords']:
                    if kw.lower() in text_lower:
                        detected = True
                        evidence = f"Keyword match: '{kw}'"
                        break
            
            # 2. Context Match
            if not detected and 'context_patterns' in patterns:
                for pattern in patterns['context_patterns']:
                    if pattern.lower() in text_lower:
                        detected = True
                        evidence = f"Context match: '{pattern}'"
                        break
            
            # Additional logic can be applied around NER tokens if needed, e.g. finding proper ORGs.
            
            if detected:
                detections.append(Detection(
                    technology=sig['technology'],
                    vector=DetectionVector.JOB_POSTING_NLP,
                    evidence=evidence
                ))
    
        return detections
