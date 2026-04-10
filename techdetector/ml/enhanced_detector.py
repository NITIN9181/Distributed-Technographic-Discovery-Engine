import spacy
from typing import List
from ..models import Detection, DetectionVector, Technology

class MLEnhancedJobDetector:
    def __init__(self, model_path: str = "./models/tech_ner"):
        try:
            self.nlp = spacy.load(model_path)
        except OSError:
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except Exception:
                self.nlp = spacy.blank("en")
    
    def detect(self, text: str) -> List[Detection]:
        doc = self.nlp(text)
        detections = []
        
        for ent in doc.ents:
            if ent.label_ in ["TECHNOLOGY", "PROGRAMMING_LANGUAGE", "FRAMEWORK", "CLOUD_SERVICE", "DATABASE"]:
                tech = self._map_to_technology(ent.text, ent.label_)
                if tech:
                    detections.append(Detection(
                        technology=tech,
                        vector=DetectionVector.JOB_POSTING_NLP,
                        evidence=f"NER: {ent.text} ({ent.label_})",
                        confidence=0.85
                    ))
        
        return detections
    
    def _map_to_technology(self, text: str, label: str) -> Technology:
        # Mock mapper for now
        return Technology(
            id=text.lower().replace(" ", "-"),
            name=text,
            category=label.lower(),
            description=None,
            detection_rules=[]
        )
