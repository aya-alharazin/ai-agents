### Prompt Engineering Concepts

Use this file to explain 3 different prompt engineering concepts that you tried and their effectiveness. You can include screenshots of your prompts and the AI's responses if you like.

---

### 1. Few-shot prompting (Database Read Expert)

**What I tested:** The Database Read Expert's `llm_roles` config includes one example (`few_shot_examples`) showing a question paired with the exact SQL style expected:
> Q: How long did they work at MSU? -> SELECT p.start_date, p.end_date FROM positions p JOIN institutions i ON p.inst_id = i.inst_id WHERE i.name = 'MSU';

I asked "How long did they work at Islamic University of Gaza?" with this example in place, then temporarily deleted the example (making the same prompt zero-shot) and asked the exact same question again, keeping everything else (instructions, schema context) unchanged.

**Result with the example (few-shot):**
```sql
SELECT p.start_date, p.end_date FROM positions p JOIN institutions i ON p.inst_id = i.inst_id WHERE i.name = 'Islamic University of Gaza';
```
Chat reply: accurate — correctly stated the start date and that the position is ongoing.

**Result without the example (zero-shot):**
```sql
SELECT STRFTIME('%Y-%m-%d', end_date) - STRFTIME('%Y-%m-%d', start_date) AS duration FROM positions WHERE inst_id = (SELECT inst_id FROM institutions WHERE name = 'Islamic University of Gaza');
```
Chat reply: "The duration of their work at Islamic University of Gaza is not available."

**Effectiveness:** The example wasn't just controlling output *formatting* — it was implicitly teaching a *query strategy*. With no example, the model tried to compute the duration itself inside SQL, using a subtraction operator on two date strings, which isn't valid date arithmetic in SQLite. It didn't error, it just silently produced a useless result, and the final answer degraded from a correct date to "not available." One well-chosen example prevented an entire category of subtly-wrong query design, not just cosmetic differences.
