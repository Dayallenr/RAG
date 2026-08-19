# Config profiles

A profile is a small YAML overlay merged over `config/config.yaml` at load
time. It returns the same `Config` object every caller already receives, so
nothing downstream knows profiles exist.

```bash
python scripts/build_index.py --profile finetuned --recreate
DUEDILIGENCE_CONFIG_PROFILE=finetuned python -m duediligence.api.app
```

The same variable selects a profile for the served API — no rebuilt image and
no file edited into the container, since `config/` already ships in the image.
The service then reports the `model`, `index` and `profile` it actually loaded
on `/healthz` and `/readyz`, so a container holding a model that does not match
its index is visible rather than silent. `python scripts/verify_served_profile.py`
serves both profiles for real and checks exactly that
(`results/serving/profile_check.json`).

Selection is by **name**, resolved inside this directory — not by path, so an
experiment cannot quietly run against an untracked overlay sitting outside the
repository and produce a report nobody else can reproduce.

Two rules the loader enforces, both of which exist to stop a comparison from
silently measuring the wrong thing:

- **A profile that changes the embedding model must also change the index
  name.** One index holds one model's vectors. Pointing a second model at it
  scores cosine similarity across incompatible spaces — no error, no warning,
  and no recovery short of re-embedding the corpus.
- **An unknown profile name raises rather than falling back to the base
  config.** A silent fallback produces a report labelled `finetuned` that
  measured the baseline, which is precisely the failure the fine-tune
  comparison exists to detect.
