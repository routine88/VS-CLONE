# Nightfall Survivors Text Prototype

The Python logic stack now ships with a small text-mode harness so designers can
prototype Nightfall Survivors runs without waiting for the Unity client. The
entrypoint can be executed directly from the repository root:

```bash
python -m game.prototype --seed 123 --duration 300 --tick-step 10
```

The command above runs a five-minute slice using deterministic RNG so combat and
hazard rolls are reproducible between runs.

## Options

| Option | Description |
| ------ | ----------- |
| `--hunter` | Hunter identifier to pilot (defaults to the active profile hunter). |
| `--seed` | RNG seed for deterministic simulations. |
| `--duration` | Override the total session duration in seconds (default: 1200). |
| `--tick-step` | Simulation tick granularity in seconds (default: 5). |
| `--profile-path` | Load an encrypted player profile before running. Requires `--key`. |
| `--key` | Decryption key used with `--profile-path`. |

## Sample Output

```
Nightfall Survivors Prototype Run
Hunter: Varik the Nightblade (hunter_varik)
Seed: 123
Outcome: Fallen
Duration: 298.4s
Encounters Resolved: 8
Relics: Moonlit Charm
Sigils Earned: 14

Event Log:
  [001] Wave 1 incoming with 6 foes.
  [002] Resolved wave defeating 6 foes in 12.5s.
  ...
```

Event logs mirror the order recorded on the `GameState`, making it easier to
validate encounter pacing, hazard cadence, and reward flow while more of the PRD
feature set is implemented.
