### Prompt Engineering Concepts

Use this file to explain 3 different prompt engineering concepts that you tried and their effectiveness. You can include screenshots of your prompts and the AI's responses if you like.

---

### 1. Few-shot prompting (Database Read Expert)

**What it is:** Giving the model one or more worked examples of the exact input→output pattern expected, so it imitates that pattern rather than guessing the format on its own.

**What I tested:** The Database Read Expert's `llm_roles` config includes one example (`few_shot_examples`):
> Q: How long did they work at MSU? -> SELECT p.start_date, p.end_date FROM positions p JOIN institutions i ON p.inst_id = i.inst_id WHERE i.name = 'MSU';

With this example in place, I asked "How long did they work at Islamic University of Gaza?" and got:
```sql
SELECT p.start_date, p.end_date FROM positions p JOIN institutions i ON p.inst_id = i.inst_id WHERE i.name = 'Islamic University of Gaza';
```
Chat reply: accurate — correctly stated the start date and that the position is ongoing.

**Effectiveness:** The example did more than control formatting — it demonstrated a *query strategy*: return the raw `start_date`/`end_date` fields and let a later step turn them into a human sentence, rather than trying to compute anything derived inside the SQL itself. The model followed that exact strategy for a completely different institution name, proving the example generalized rather than being copied verbatim.

---

### 2. Zero-shot prompting (Database Read Expert)

**What it is:** Giving the model only instructions and context, with no worked example to imitate — it has to infer the expected format and approach entirely on its own.

**What I tested:** I temporarily deleted the same few-shot example from the Read Expert's config (making its prompt zero-shot), keeping the instructions and schema context unchanged, and asked the exact same question: "How long did they work at Islamic University of Gaza?"

**Result:**
```sql
SELECT STRFTIME('%Y-%m-%d', end_date) - STRFTIME('%Y-%m-%d', start_date) AS duration FROM positions WHERE inst_id = (SELECT inst_id FROM institutions WHERE name = 'Islamic University of Gaza');
```
Chat reply: "The duration of their work at Islamic University of Gaza is not available."

**Effectiveness:** Without an example, the model still followed the instructions (it produced one valid-looking `SELECT` statement, respecting "SQL only, no markdown"), but it invented its own query strategy — trying to compute the duration directly in SQL using a subtraction operator on two date strings, which is not valid date arithmetic in SQLite. This didn't raise an error; it just silently returned a useless result, so the final answer degraded from a correct date to "not available." This is the clearest illustration in this project of zero-shot's main weakness: the model can follow explicit instructions correctly while still making a reasonable-looking but wrong assumption about *how* to solve the task, when it has no example to anchor to.

---

### 3. Orchestrator prompting (task decomposition)

**What it is:** Instead of one prompt trying to handle an entire request end-to-end, the request is first given to an "Orchestrator" prompt whose only job is to break it into an ordered list of smaller sub-tasks and name which specialized expert should handle each one. Each sub-task then runs through its own separately-prompted expert, and a final prompt merges all the results into one reply.

**How it's applied in this project:** Every chat message goes through `handle_ai_chat_request(db, role="Orchestrator", message=...)` first. I tested it with a compound request: "Does he know Dart? If not, add it to Programming Labs experience." The console showed the Orchestrator correctly splitting this into two ordered steps and running them in sequence:

```
[Orchestrator] generated:
[
    "handle_ai_chat_request(role=\"Database Read Expert\", message=\"Does he have Dart listed as a skill?\")",
    "handle_ai_chat_request(role=\"Database Write Expert\", message=\"Add Dart as a skill to Programming Labs experience\")"
]

[Orchestrator] executing: handle_ai_chat_request(role="Database Read Expert", ...)
[Database Read Expert] generated:
SELECT s.name FROM skills s JOIN experiences e ON s.experience_id = e.experience_id WHERE s.name = 'Dart';

[Orchestrator] executing: handle_ai_chat_request(role="Database Write Expert", ...)
[Database Write Expert] generated:
existing = db.query("SELECT * FROM skills WHERE name = 'Dart' AND experience_id = (SELECT experience_id FROM experiences WHERE name = 'Programming Labs')")
if existing:
    outcome = "Element already exists in the skills table."
else:
    db.insertRows('skills', ['experience_id', 'name', 'skill_level'], ["(SELECT experience_id FROM experiences WHERE name = 'Programming Labs')", 'Dart', 5]);
    outcome = "New Dart added to the skills table."
```
Both steps actually ran, in the correct order (checking before writing), and Dart appeared on the resume page immediately afterward — the reply reused the Write Expert's exact outcome message rather than paraphrasing it.

**Effectiveness:** The codebase makes the alternative concrete and easy to reason about: `handle_ai_chat_request` has a fallback path (`role=None`) that skips all of this and just calls the plain, generic `send_message(message)` — the exact Homework 0 behavior, with no `db` object passed in at all. A single generic prompt handling "does he know Dart, and if not add it" would have no way to actually check the database or perform a real insert — it could only guess or admit it can't help. Decomposition is what makes real, verifiable actions (a checked, conditional database write) possible from one user message, instead of just a conversational answer. The tradeoff, visible directly in the console output, is cost: this one compound question triggered 4 separate model calls (plan, Read Expert, Write Expert, synthesis) instead of Homework 0's single call per message.
