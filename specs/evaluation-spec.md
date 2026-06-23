# Evaluation Spec — Pod Classifier

Complete this spec **before** writing any code for Milestone 3.

Use Plan or Ask mode to think through each blank field. When you're done,
your answers here become the blueprint for `compute_accuracy()` and
`compute_per_class_accuracy()` in `evaluate.py`.

---

## Background: What is evaluation?

After building a classifier, we need to know how well it works. Evaluation answers:

- **Overall:** What fraction of episodes did we classify correctly?
- **Per-class:** Are we better at some labels than others?

Both functions take the same inputs: a list of predicted labels and a list of
ground-truth labels, in the same order.

---

## compute_accuracy(predictions, ground_truth)

### What it does

Returns the fraction of predictions that exactly match the ground truth.

### Inputs

| Parameter      | Type        | Description                                                |
| -------------- | ----------- | ---------------------------------------------------------- |
| `predictions`  | `list[str]` | Labels predicted by `classify_episode()`, one per episode. |
| `ground_truth` | `list[str]` | The correct labels, in the same order as `predictions`.    |

### Output

| Return value | Type    | Description                  |
| ------------ | ------- | ---------------------------- |
| accuracy     | `float` | A value between 0.0 and 1.0. |

---

### Spec fields — fill these in before writing code

**Formula:**

```
[blank — write out the accuracy formula in plain English.
 What counts as "correct"? What do you divide by?]

accuracy = correct predictions ÷ total predictions

Worked example: 20 test episodes, 14 classified correctly → 70% overall accuracy.

This number can be misleading. If 70% of your test episodes happen to be interview, a classifier that always returns "interview" achieves 70% accuracy without having learned anything useful. It would fail completely on solo, panel, and narrative.
```

---

**Step-by-step logic:**

```
1. Initialize a counter for correct predictions to 0.
2. Loop over each index i, comparing predictions[i] to ground_truth[i].
3. If predictions[i] == ground_truth[i], increment the correct counter by 1.
4. Divide the correct counter by the total number of items (len(predictions)).
5. Return the result as a float between 0.0 and 1.0.
```

---

**Edge case — what if both lists are empty?**

```
Return 0.0. There are no predictions to evaluate, so there is nothing correct.
Dividing 0 by 0 would cause a ZeroDivisionError, so we must handle this case
explicitly by checking if the list is empty before dividing.
```

---

**Worked example:**

```
predictions  = ["interview", "solo", "panel", "interview"]
ground_truth = ["interview", "solo", "solo",  "narrative"]

Compare each pair:
  Index 0: "interview" == "interview" → correct
  Index 1: "solo"      == "solo"      → correct
  Index 2: "panel"     != "solo"      → incorrect
  Index 3: "interview" != "narrative" → incorrect

correct = 2, total = 4
accuracy = 2 / 4 = 0.5

compute_accuracy() returns 0.5
```

---

## compute_per_class_accuracy(predictions, ground_truth)

### What it does

Returns accuracy broken down by each label. For each label in `VALID_LABELS`,
reports how many episodes with that ground-truth label were classified correctly.

### Inputs

| Parameter      | Type        | Description                               |
| -------------- | ----------- | ----------------------------------------- |
| `predictions`  | `list[str]` | Labels predicted by `classify_episode()`. |
| `ground_truth` | `list[str]` | Correct labels, in the same order.        |

### Output

A `dict` keyed by label. Each value is a dict with three keys:

```python
{
    "interview": {"correct": int, "total": int, "accuracy": float},
    "solo":      {"correct": int, "total": int, "accuracy": float},
    "panel":     {"correct": int, "total": int, "accuracy": float},
    "narrative": {"correct": int, "total": int, "accuracy": float},
}
```

---

### Spec fields — fill these in before writing code

**What does "correct" mean for a given class?**

```
An episode counts as correctly classified for a given class when:
  1. The ground-truth label for that episode IS that class, AND
  2. The predicted label exactly matches the ground-truth label.

For example, an episode counts as correct for "interview" when the
ground-truth label is "interview" AND the prediction is also "interview".
An episode predicted as "interview" when the ground truth is "solo" does
NOT count as correct for the "interview" class — it counts as incorrect
for the "solo" class (because the ground-truth label is "solo").
```

---

**What does "total" mean for a given class?**

```
"Total" is the number of episodes whose ground-truth label is that class —
NOT the total number of predictions for that class.

For example, if there are 5 episodes in the test set whose ground-truth
label is "interview", then total = 5 for the "interview" class, regardless
of how many times the classifier predicted "interview".
```

---

**Step-by-step logic:**

```
1. Initialize a dict for each label in VALID_LABELS with {"correct": 0, "total": 0, "accuracy": 0.0}.
2. Loop over each index i, pairing predictions[i] with ground_truth[i].
3. For each pair (predicted, truth):
   a. Increment the "total" count for the truth label by 1.
   b. If predicted == truth, also increment the "correct" count for that label by 1.
4. After the loop, for each label compute accuracy = correct / total.
   If total == 0 for a label, set accuracy to 0.0 instead of dividing.
5. Return the dict with all four labels and their correct, total, and accuracy values.
```

---

**Edge case — what if a class has no examples in ground_truth (total == 0)?**

```
Set accuracy to 0.0. As stated in the evaluate.py docstring: "0.0 if total is 0".
We cannot divide by zero, and returning 0.0 signals that we have no evidence of
performance for that class rather than falsely reporting success.
```

---

**Worked example:**

```
predictions  = ["interview", "interview", "solo", "panel", "panel"]
ground_truth = ["interview", "solo",      "solo", "panel", "narrative"]

Pair-by-pair analysis:
  Index 0: predicted="interview", truth="interview" → interview correct +1, interview total +1
  Index 1: predicted="interview", truth="solo"      → solo total +1 (wrong prediction)
  Index 2: predicted="solo",      truth="solo"      → solo correct +1, solo total +1
  Index 3: predicted="panel",     truth="panel"     → panel correct +1, panel total +1
  Index 4: predicted="panel",     truth="narrative" → narrative total +1 (wrong prediction)

label       correct  total  accuracy
----------  -------  -----  --------
interview   1        1      1.0
solo        1        2      0.5
panel       1        1      1.0
narrative   0        1      0.0
```

---

## Reflection questions (discuss at the checkpoint)

1. Your overall accuracy might be decent even if one class has very low accuracy.
   Why is per-class accuracy a more informative metric than overall accuracy alone?

2. If `panel` episodes consistently get misclassified as `interview`, what does
   that tell you about your training labels or your prompt?

3. You labeled 20 training episodes and evaluated on 20 test episodes (5 per class).
   How might the evaluation results change if you had labeled 100 training episodes?
   What if you had 200 test episodes?
