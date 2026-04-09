import os
from dataclasses import dataclass
from dotenv import load_dotenv

@dataclass
class Config:
    database_url: str
    spacy_model: str = "en_core_web_sm"
    dns_timeout: float = 5.0
    http_timeout: float = 15.0
    
def load_config() -> Config:
    load_dotenv()
    return Config(
        database_url=os.getenv(
            "DATABASE_URL", 
            "postgresql://techdetector:localdev123@localhost:5432/techdetector"
        ),
        spacy_model=os.getenv("SPACY_MODEL", "en_core_web_sm"),
        dns_timeout=float(os.getenv("DNS_TIMEOUT", "5.0")),
        http_timeout=float(os.getenv("HTTP_TIMEOUT", "15.0")),
    )
