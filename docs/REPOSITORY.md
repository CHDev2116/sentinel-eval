# Repository naming

**Product name:** SentinelEval (eval harness + benchmark)  
**Recommended GitHub repo:** [`sentinel-eval`](https://github.com/CHDev2116/sentinel-eval) (kebab-case)

| Option | Notes |
|--------|--------|
| **`sentinel-eval`** ✅ | Clear, professional, matches common OSS conventions |
| `sentineleval` | Harder to read; no word boundary |
| `llm-sentinel-eval` | Explicit but long; redundant if org/profile already LLM-focused |

## Rename on GitHub

```bash
# From the repo root (requires gh CLI + admin on the repo)
gh repo rename sentinel-eval --yes

# Update your local remote
git remote set-url origin git@github.com:CHDev2116/sentinel-eval.git
# or: https://github.com/CHDev2116/sentinel-eval.git
```

GitHub will redirect `red_team_project` → `sentinel-eval` for clones and old links. Update README badges and any external links after rename.

## Local folder name (optional)

Your checkout path can stay `red_team_project`; only the **GitHub slug** needs to change for a sharp public URL.

```bash
cd ..
mv red_team_project sentinel-eval
cd sentinel-eval
```
