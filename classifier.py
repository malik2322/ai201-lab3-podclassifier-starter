import json
import os
from groq import Groq
from config import GROQ_API_KEY, LLM_MODEL, VALID_LABELS, DATA_PATH, TRAIN_FILE, LABELS_FILE

_client = Groq(api_key=GROQ_API_KEY)


def load_labeled_examples() -> list[dict]:
    """
    Load the training episodes and merge them with the student's labels.

    Returns a list of dicts, each with:
      - "id"          : episode ID
      - "title"       : episode title
      - "podcast"     : podcast name
      - "description" : episode description
      - "label"       : the label from my_labels.json (may be None if not yet annotated)

    Only returns episodes where the label is a valid, non-null string.
    Episodes with null labels are silently skipped.
    """
    train_path = os.path.join(DATA_PATH, TRAIN_FILE)
    labels_path = os.path.join(DATA_PATH, LABELS_FILE)

    with open(train_path, encoding="utf-8") as f:
        episodes = {ep["id"]: ep for ep in json.load(f)}

    with open(labels_path, encoding="utf-8") as f:
        labels = {entry["id"]: entry["label"] for entry in json.load(f)}

    labeled = []
    for ep_id, ep in episodes.items():
        label = labels.get(ep_id)
        if label in VALID_LABELS:
            labeled.append({**ep, "label": label})

    return labeled


def build_few_shot_prompt(labeled_examples: list[dict], description: str) -> str:
    task_instruction = (
        "You are classifying podcast episodes by their format. Classify the episode "
        "into exactly one of these four labels:\n\n"
        "- interview: a conversation between a host and one or more guests\n"
        "- solo: a single host speaking from memory, experience, or opinion — no guests, "
        "no assembled external sources\n"
        "- panel: multiple guests with roughly equal speaking time, often debating or "
        "discussing a topic together\n"
        "- narrative: a story assembled from external sources — interviews, archival "
        "audio, reporting — with a clear narrative arc\n\n"
        "Return only the label and your reasoning. Do not explain the taxonomy."
    )

    prompt = task_instruction + "\n\n"

    if labeled_examples:
        prompt += "Here are some labeled examples:\n\n"
        for ex in labeled_examples:
            prompt += f"Title: {ex['title']}\nDescription: {ex['description']}\nLabel: {ex['label']}\n\n---\n\n"

    prompt += (
        f"Now classify this episode:\n\n"
        f"Title: (unknown)\n"
        f"Description: {description}\n"
        f"Label: ?\n\n"
        f"Classify the episode above. Return your answer in the format below:\n\n"
        f"Label: <label>\nReasoning: <one or two sentences>"
    )

    return prompt

def classify_episode(description: str, labeled_examples: list[dict]) -> dict:
    try:
        prompt = build_few_shot_prompt(labeled_examples, description)

        response = _client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
        )

        response_text = response.choices[0].message.content.strip()
        
        print(response_text)  # Debugging: print the raw response from the model

        if "Reasoning:" in response_text:
            label_part, reasoning = response_text.split("Reasoning:", 1)
        else:
            label_part, reasoning = response_text, ""

        label = label_part.split("Label:")[-1].strip().strip(".*_`").lower()
        reasoning = reasoning.strip()

        if label not in VALID_LABELS:
            label = "unknown"

        return {"label": label, "reasoning": reasoning}

    except Exception as e:
        return {"label": "unknown", "reasoning": f"Error: {e}"}
