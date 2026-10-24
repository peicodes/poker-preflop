# poker-preflop

Evaluate an LLM preflop prompt with Pydantic AI + Pydantic Evals, running on your Claude Code login.

```
.venv/bin/python run_evals.py                         # prompts/v1.md on sonnet
.venv/bin/python run_evals.py --prompt v2 --model opus
.venv/bin/python smoke_test.py                        # single call sanity check
```

- **Prompt**: `prompts/<name>.md` is the system prompt. Copy `v1.md` to try a variant, select it with `--prompt`.
- **Spot formatting** (the user message): `render_spot` in `src/poker_preflop/agent.py`.
- **Output schema**: `Decision` in `src/poker_preflop/schemas.py` (`fold` / `call` / `raise` + `raise_to_bb`).
- **Dataset**: `datasets/preflop.yaml`. Each case's `expected_output` is an `ExpectedDecision`: the action and, for raises, a `raise_to_target` in bb.
- **Evaluators**: `src/poker_preflop/evaluators.py` has `Correctness`, a code-based 0-1 score: 0 if the action is wrong, 1 for a right fold/call, and for a right raise a Gaussian falloff on % difference from `raise_to_target` (10% off ≈ 0.85, 20% ≈ 0.53, 40% ≈ 0.08).
  `Reasoning` is a pass/fail LLM judge (Gemini via the gateway) of the `reasoning` text: it must support the action taken and, for raises, explain the size.
- **Model backend**: `src/poker_preflop/claude_code_model.py` shells out to the `claude` CLI via `claude-agent-sdk`
  (needs `claude auth login`).
- **Anthropic vs Google AI Studio**: `--model sonnet` runs on Claude Code; `--model gateway/google-ai-studio:gemini-2.5-flash`
  runs through your Logfire gateway's `google-ai-studio` provider (set `PYDANTIC_AI_GATEWAY_API_KEY`, and `PYDANTIC_AI_GATEWAY_BASE_URL`
  if not US region). See `build_model` in `agent.py`. Run both and compare the experiments in Logfire.
