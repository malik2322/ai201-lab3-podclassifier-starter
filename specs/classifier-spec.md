# Classifier Spec — Pod Classifier

Complete this spec **before** writing any code for Milestone 2.

Use Plan or Ask mode to think through each blank field. When you're done,
your answers here become the blueprint for `build_few_shot_prompt()` and
`classify_episode()` in `classifier.py`.

---

## build_few_shot_prompt(labeled_examples, description)

### What it does

Constructs a prompt string for the LLM that includes the task instructions,
all labeled training examples, and the new episode description to classify.

### Inputs

| Parameter          | Type         | Description                                                                                                          |
| ------------------ | ------------ | -------------------------------------------------------------------------------------------------------------------- |
| `labeled_examples` | `list[dict]` | Each dict has `"title"`, `"description"`, `"label"` (and others). These are the examples you labeled in Milestone 1. |
| `description`      | `str`        | The episode description to classify.                                                                                 |

### Output

| Return value | Type  | Description                                        |
| ------------ | ----- | -------------------------------------------------- |
| prompt       | `str` | A complete prompt string ready to send to the LLM. |

---

### Spec fields — fill these in before writing code

**Task instruction (what should the LLM know about the task?):**

```
You are classifying podcast episodes by their format. Classify the episode
into exactly one of these four labels:

- interview: a conversation between a host and one or more guests
- solo: a single host speaking from memory, experience, or opinion — no guests,
  no assembled external sources
- panel: multiple guests with roughly equal speaking time, often debating or
  discussing a topic together
- narrative: a story assembled from external sources — interviews, archival
  audio, reporting — with a clear narrative arc

Return only the label and your reasoning. Do not explain the taxonomy.
```

---

**How should labeled examples be formatted in the prompt?**

```
Each example should include the episode title, a brief excerpt or the full
description, and the correct label. Separate examples with a blank line or
a delimiter like "---". Include all fields that help the model see why the
label was applied — title and description are both useful; other fields
(like episode ID) are not needed.
```

---

**Example block sketch (write one concrete example):**

```
Title: {The Case for Four-Day Workweeks}
Description: {I've been thinking about the four-day workweek for months, and I want to lay out the case for it as clearly as I can. I'm going to cover the productivity research, the companies that have tried it, the objections I find compelling versus the ones I don't, and what I think it would actually take for this to become mainstream. This is a topic I have a real view on, and I want to share it.}
Label: {solo}
```

---

**How should the new episode (to be classified) be presented?**

```
Present it in the same format as the labeled examples, but omit the Label
line and replace it with an instruction to classify. For example:

Title: {title}
Description: {description}
Label: ?

Then add a line like: "Classify the episode above. Return your answer in
the format below:" followed by the output format you chose.
```

---

**What output format should you request from the LLM?**

```
Use a two-line structured format:

Label: <label>
Reasoning: <one or two sentences>

This is the best balance of reliability and simplicity. A single bare label
is easy to parse but gives no reasoning. JSON would be the most robust for
machine parsing, but LLMs sometimes add markdown fences or trailing commas
that break json.loads(). The "Label: X / Reasoning: Y" key-value format is
easy to parse with a simple split on "Label:" and "Reasoning:", and it
naturally produces the two fields we need for the return dict. The LLM
rarely deviates from this format when given a clear example.
```

---

**Edge cases to handle in the prompt:**

```
- If labeled_examples is empty: the prompt still works as a zero-shot
  classifier — the task instruction and label definitions are enough for
  the LLM to attempt a classification, just with lower accuracy. No
  examples section is included; the prompt skips straight to the episode
  to classify.
- If the description is very short (e.g., a single sentence or just a
  title): the prompt still presents it normally. The LLM may be less
  confident, but the format doesn't break. The reasoning field will
  reflect the uncertainty.
- If the description contains special characters, quotes, or newlines:
  these are embedded as-is in the prompt string. Since we're not using
  JSON or any escape-sensitive format in the prompt itself, this is safe.
```

---

## classify_episode(description, labeled_examples)

### What it does

Classifies a single podcast episode description using the few-shot LLM classifier.
Returns a dict with a label and reasoning.

### Inputs

| Parameter          | Type         | Description                                               |
| ------------------ | ------------ | --------------------------------------------------------- |
| `description`      | `str`        | The episode description to classify.                      |
| `labeled_examples` | `list[dict]` | Labeled training examples from `load_labeled_examples()`. |

### Output

| Return value | Type   | Description                                                                                         |
| ------------ | ------ | --------------------------------------------------------------------------------------------------- |
| result       | `dict` | Must have keys `"label"` and `"reasoning"`. `"label"` must be one of `VALID_LABELS` or `"unknown"`. |

---

### Spec fields — fill these in before writing code

**Step 1 — Build the prompt:**

```
Call build_few_shot_prompt(labeled_examples, description) and store the
returned string in a variable (e.g., prompt). Pass through both arguments
exactly as received — no modification needed before calling.
```

---

**Step 2 — Send to the LLM:**

```
Call _client.chat.completions.create() with:
  - model: the model name from config (LLM_MODEL)
  - messages: a list with one dict — {"role": "user", "content": prompt}
    (system-design.md shows an optional system message too — either shape works)
  - max_tokens: a reasonable limit (e.g., 200–300) to keep responses concise

Extract the response text from:
  response.choices[0].message.content
```

---

**Step 3 — Parse the response:**

```
Since the requested output format is "Label: <label>\nReasoning: <text>":

1. Strip whitespace from the full response text.
2. Split the response on "Reasoning:" (case-insensitive) to separate the
   two parts. If "Reasoning:" is not found, treat the entire response as
   the label line and set reasoning to an empty string.
3. From the first part, find the text after "Label:" — strip it and call
   .lower() to normalize. This gives the predicted label.
4. From the second part (if it exists), strip it to get the reasoning string.

Concrete code sketch:
  response_text = response.choices[0].message.content.strip()
  if "Reasoning:" in response_text:
      label_part, reasoning = response_text.split("Reasoning:", 1)
  else:
      label_part, reasoning = response_text, ""
  label = label_part.split("Label:")[-1].strip().strip(".*_`").lower()
  reasoning = reasoning.strip()

Normalization detail: after lowercasing, also strip surrounding
punctuation and markdown formatting characters (., *, _, `) so that
responses like "Label: **Interview**" or "Label: narrative." are
correctly matched. This handles capitalization variance, markdown
bold/italic, and trailing punctuation without requiring the model to
be perfectly consistent.
```

---

**Step 4 — Validate the label:**

```
After extracting and lowercasing the label string, check if it is in
VALID_LABELS (["interview", "solo", "panel", "narrative"]). If it is not
— for example, the LLM returned "discussion", "conversational", or a
multi-word phrase — set label to "unknown". This ensures the evaluation
loop always gets a predictable value and can count it as incorrect
rather than crashing on an unexpected string.

Concrete check:
  if label not in VALID_LABELS:
      label = "unknown"

Debugging tip: if your classifier returns "unknown" for more than ~10%
of episodes, the problem is almost always in the parsing, not the
classification. Add a temporary print(response_text) line before the
parsing logic and inspect what the LLM is actually returning — look for
unexpected formatting, extra text, or label variants that your
normalization isn't catching.
```

---

**Step 5 — Handle errors gracefully:**

```
Wrap the entire LLM call and parsing logic in a try/except block that
catches broad exceptions (Exception). Things that could go wrong:

- Network/API error: Groq is unreachable, rate-limited, or returns a 500.
- Empty response: the LLM returns an empty string or None.
- Unparseable response: the response doesn't contain "Label:" at all,
  so the split logic produces garbage.
- Timeout: the API call takes too long.

In all of these cases, return the fallback dict:
  {"label": "unknown", "reasoning": "Error: <brief description of what went wrong>"}

This way the evaluation loop continues through all 20 episodes. The
"unknown" label will count as incorrect, which is the right behavior —
a failed classification should hurt accuracy, not crash the run.
```

---

### Return value structure

```python
{
    "label": str,      # one of VALID_LABELS, or "unknown" if invalid/error
    "reasoning": str,  # brief explanation from the LLM
}
```

---

## Notes on label quality

The classifier is only as good as your labels. If your training examples have
inconsistent or ambiguous labels, the LLM will learn the wrong pattern.

Before implementing the classifier, re-read `data/taxonomy.md` and double-check
any labels you're unsure about. Annotation quality is part of the lab.

---

## Implementation Notes

_Fill this in after implementing and testing both functions._

**Test: what does the raw LLM response look like for one episode?**

```
Episode tested: [solo]
Raw response text: [Reasoning: The episode features a single host presenting their thoughts and opinions on the four-day workweek, without any mention of guests or external sources being interviewed. The host's personal perspective and experience are the primary focus of the episode, which is characteristic of a solo format.]
```

**How did you parse the label out of the response?**

```
[describe the string operations — strip, split, lower, etc.]
```

**Did any episodes return `"unknown"`? If so, why?**

```
[yes / no — if yes, what did the raw response look like?]
```

**One thing about the output format that surprised you:**

```
[your answer here]
```
