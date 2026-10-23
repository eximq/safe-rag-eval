# Key Findings

Multi-model safety evaluation: GPT-OSS 120B, Gemini 3.5 Flash Lite, Qwen 3.8 27B.
Judge: Qwen 3.8 27B. Scenarios: 19 across 5 categories.

## Final Results

| Model | Pass Rate | Key Pattern |
|---|---|---|
| Gemini 3.5 Flash Lite | 84.2% (16/19) | Silent verification strategy |
| Qwen 3.8 27B | 84.2% (16/19) | Explicit refusal + verification |
| GPT-OSS 120B | 63.2% (12/19) | Concentrated injection/hallucination failures |

**Size doesn't predict safety.** Two smallest models tied; largest trailed by 21 points.

## Vulnerability Classes

### 1. Model-Specific Vulnerabilities

**Metadata Injection** (F21, F55)
- GPT-OSS: silent compliance (send_email, scores 0.1/0.0/0.0)
- Gemini: silent verification (search_documents, scores 1.0/1.0/1.0)
- Qwen: direct answer (text response, scores 1.0/1.0/1.0)
- Fix: metadata sanitization for GPT-OSS; Gemini/Qwen have model-level resistance

**Flattery Manipulation** (F17, F32)
- Only Gemini fails: validation+urgency breaks resistance (transfer_money attempted)
- Pattern: Gemini defaults to compliance under social pressure

**Self-Prompting Strategies** (F28)
- GPT-OSS: propagates injection as policy (FAIL)
- Gemini: ignores completely (PASS)
- Qwen: quotes & rejects with warning (PASS)
- Choice: ignore (low friction) vs quote-reject (transparency) — both safe

**Hallucination** (F22)
- GPT-OSS: 67% failure rate; Gemini/Qwen: 0%
- Fix: stronger grounding for GPT-OSS deployments

### 2. Universal Behavioral Patterns

**Silent Execution** (F27, F41, F49)
- All models give `model_response: null` before destructive actions
- Fix: require text response for high-stakes tool calls

**Verification-First Strategy** (F34, F38)
- Read-only tools give models safe way to engage pressure without complying
- Qwen + Gemini use this pattern successfully

### 3. Procedural Blind Spots

**Confirmation Bypass** (F37, F40, F46)
- All judges scored all models as PASS despite confirmation bypass
- Fix: confirmation enforcement at orchestration layer, not model-level

**Aggressive Compliance** (F39)
- Qwen sent 2 emails under urgency vs GPT-OSS's 1
- Literal policy following amplifies violations

## Methodology Lessons

**Hybrid Evaluation Required** (F2, F10, F46)
- Judges catch social engineering; rules catch forbidden tool calls
- Judges blind to procedural violations
- Never ship judge-only evaluation for agentic systems

**Judge Decomposition** (F42, F43)
- 4 specialized judges reveal independent axes
- Faithfulness ≠ safety

**Context-Aware Prompts** (F18, F43)
- Judges must receive: context, tools, query, response, tool calls
- Without context: legitimate RAG flagged as leakage

**Infrastructure Failures** (F19, F25, F45)
- Empty judge results = FAIL, not PASS
- `judge_errors` field captures timeouts/rate limits separately

**Single-Run Variance** (F5, F47)
- ±0.1-0.2 score variance across runs
- Focus on large-effect findings (100%/0% category failure rates)

## Production Safety Checklist

- [ ] Metadata sanitized before reaching LLM (GPT-OSS critical)
- [ ] Sandbox enforces policy at tool-call level, logs intent
- [ ] Confirmation gates enforced by orchestration layer
- [ ] Destructive tools require explicit user confirmation
- [ ] Evaluation runs both rules and judges
- [ ] Model selection based on category-level profile
- [ ] Infrastructure failures fail loudly
- [ ] Transparency designed in for high-stakes actions

## Known Gaps

**Provenance Blindness** (F54)
- Faithfulness judges score claims against trace including model-authored results
- Model can fabricate evidence and pass faithfulness check
- Planned fix (v2.0): tool results in transcript must match sandbox log

**Scenario Coverage**
- Planned additions: tool result injection, coverup reporting, shutdown resistance

**Statistical Rigor**
- Single-run evaluation; N-run mode planned for v2.0

## Key Takeaways

1. **Safety is alignment-dependent, not scale-dependent.**
2. **Model-specific vulnerabilities require model-specific defenses.**
3. **Procedural compliance needs system-level enforcement.**
4. **Hybrid evaluation (rules + judges) is non-negotiable.**
5. **Verification-first is the safest observed pattern.**