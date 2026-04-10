import spacy
from spacy.training import Example
from pathlib import Path
import json
import random

def prepare_training_data(annotations_file: str) -> list:
    """Load annotated job postings."""
    try:
        with open(annotations_file) as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: {annotations_file} not found. Returning empty dataset.")
        return []

def train_model(
    training_data: list,
    output_dir: str,
    n_iter: int = 15
):
    """Train custom NER model."""
    if not training_data:
        print("No training data provided.")
        return
        
    print("Using blank English model for testing...")
    nlp = spacy.blank("en")
    
    # Add custom NER labels
    if "ner" not in nlp.pipe_names:
        ner = nlp.add_pipe("ner", last=True)
    else:
        ner = nlp.get_pipe("ner")
        
    for label in ["TECHNOLOGY", "PROGRAMMING_LANGUAGE", "FRAMEWORK", "CLOUD_SERVICE", "DATABASE"]:
        ner.add_label(label)
    
    # Training loop
    other_pipes = [pipe for pipe in nlp.pipe_names if pipe != "ner"]
    with nlp.disable_pipes(*other_pipes):
        optimizer = nlp.begin_training()
        for i in range(n_iter):
            random.shuffle(training_data)
            losses = {}
            for item in training_data:
                text = item.get("text", "")
                annotations = item.get("entities", [])
                
                # Format to match what spacy expects
                formatted_annotations = {"entities": [(ent["start"], ent["end"], ent["label"]) for ent in annotations]}
                
                example = Example.from_dict(nlp.make_doc(text), formatted_annotations)
                nlp.update([example], sgd=optimizer, drop=0.2, losses=losses)
            print(f"Iteration {i}: {losses}")
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    nlp.to_disk(output_dir)
    print(f"Model saved to {output_dir}")

if __name__ == "__main__":
    import sys
    data_file = sys.argv[1] if len(sys.argv) > 1 else "../training_data.json"
    train_model(
        prepare_training_data(data_file),
        output_dir="./models/tech_ner",
        n_iter=10
    )
