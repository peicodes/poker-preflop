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
- **Dataset**: `datasets/preflop.yaml`. Each case's `expected_output` is an `ExpectedDecision`: the action and, for raises, the acceptable `raise_to_min`/`raise_to_max` in bb.
- **Evaluators**: `src/poker_preflop/evaluators.py` (`ActionMatches`, `RaiseSizeInRange`, `DecisionCorrect`, all code-based and reading ranges from `expected_output`).
- **Model backend**: `src/poker_preflop/claude_code_model.py` shells out to the `claude` CLI via `claude-agent-sdk`
  (needs `claude auth login`). To use an API key instead, pass e.g. `'anthropic:claude-sonnet-5-5'` to the `Agent` in `agent.py`.
