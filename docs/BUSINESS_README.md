# SentinelEval — Business Overview (Proposals & Client Engagements)

> For executives, procurement, legal, and security leaders. **No AI or programming background required.**
>
> **繁體中文:** [商業說明 (zh-TW)](BUSINESS_README.zh-TW.md) · Technical setup: [Project README](../README.md)

---

## In one sentence

**Before AI handles your company email, we test it with realistic malicious messages to see whether it gets tricked and labels dangerous threads as “safe.”**

Pre-launch **security quality control** — not chatbot friendliness scores.

---

## Use cases

| Use case | Business outcome |
|----------|------------------|
| **Internal AI email assistant security testing** | Know whether your copilot can be manipulated before employees rely on it |
| **Detect hidden instructions** | Catch overrides buried in signatures, forwards, footers, or multilingual text |
| **Prevent prompt override** | Stop “ignore prior policy” patterns from reaching automation |
| **Benchmark local models before deployment** | Compare candidates on *your* mail shapes, not vendor marketing |
| **Enterprise local LLM evaluation** | Run entirely on-prem — samples stay in your boundary |
| **Compare Ollama / vLLM / LM Studio models** | Same test harness, swap the model tag |
| **Validate structured outputs** | Ensure every response is machine-readable for SOAR and workflows |
| **CI release gates for AI systems** | Block deploy when a release candidate fails security cases |
| **AI governance pipeline** | Repeatable evidence for risk committees and auditors |
| **Benchmark prompts before rollout** | Prove a prompt change did not drop attack detection |
| **Regression testing for model upgrades** | “Smarter” models that miss more attacks are caught in CI |

---

## Built for your company — not a fixed lab quiz

SentinelEval is an **extensible evaluation framework**. The open golden suite is a starting point; engagements typically **adapt** it to your environment:

| You bring | We configure |
|-----------|--------------|
| **Custom attack datasets** | Your thread formats, languages, LOB-specific lures |
| **Enterprise prompts** | Your production auditor / triage templates in the harness |
| **Internal CI** | GitHub Actions, GitLab, Jenkins — fail the build on missed injections |
| **Local or hosted LLMs** | Ollama on laptop, vLLM in VPC, or approved API endpoints |
| **Go-live rules** | What “unacceptable” means for queues, SOAR, and auto-close |

**Message for procurement:** this is a **platform and methodology** you can own — not a single score on someone else’s benchmark.

---

## Architecture (executive view)

Dark-theme workflow — how mail security testing fits your AI stack:

<p align="center">
  <img src="diagrams/architecture_business.svg" alt="SentinelEval enterprise AI governance workflow" width="1000"/>
</p>

<p align="center"><em>Optional PNG for slides: <code>./scripts/export_business_diagram.sh</code> (no Homebrew — uses macOS Quick Look, apt/dnf, or Inkscape). SVG alone is fine for GitHub/decks.</em></p>

Engineering detail: [architecture in technical README](../README.md#architecture).

---

## Product demo (what clients watch)

**~30 seconds** beats a wall of metrics. Use these previews in decks today; drop in GIF/MP4 when recorded.

| Preview | What it shows |
|---------|----------------|
| Terminal smoke run | Local command → per-case pass/fail → report path |
| Before / after detection | Same thread marked SAFE vs UNSAFE after testing |
| Leaderboard | Compare models on injection recall before rollout |

<p align="center">
  <img src="demos/demo_run_animated.svg" alt="Terminal smoke run preview" width="820"/>
</p>

<p align="center">
  <img src="demos/attack_before_after.svg" alt="Before and after attack detection" width="820"/>
</p>

<p align="center">
  <img src="demos/leaderboard_preview.svg" alt="Leaderboard comparison preview" width="820"/>
</p>

**Record your own GIF/video** (recommended filenames): see [docs/demos/README.md](demos/README.md)

```text
docs/demos/sentinel-eval-smoke.gif      # ~30s CLI
docs/demos/release-gate-fail.gif        # deploy blocked
docs/demos/leaderboard.gif              # model comparison
```

---

## What this project demonstrates (capabilities you are buying)

| Capability | Why it matters commercially |
|------------|------------------------------|
| **AI evaluation framework design** | Repeatable harness, not one-off consultant scripts |
| **Prompt-injection & instruction-override testing** | Matches real mail-threat models, not trivia Q&A |
| **Local LLM orchestration** | Fits data-residency and air-gapped requirements |
| **AI CI/CD governance** | Release gates, history, regression on every change |
| **Structured audit pipelines** | JSON contracts wired to SOAR, ticketing, and analytics |
| **Adversarial surface testing** | Same attack, many wrappers (unicode, forwards, footers, …) |
| **Calibration & confidence review** | Surfaces “confident but wrong” — a board-level risk topic |

---

## Engagement deliverables (what you receive from us)

| Deliverable | What you receive |
|-------------|------------------|
| **Risk mapping report** | Missed attack types and false alarms — in queue / SOC / automation language |
| **Go-live recommendation** | Ship · hold · ship with mandatory human review |
| **Before/after comparison** | Evidence across model or prompt changes |
| **Custom test pack** | Scenarios aligned to your mail flows (optional) |
| **CI integration playbook** | Embed gates in your release process (optional) |
| **Executive + engineering readouts** | Slide-ready summary plus structured JSON reports |

---

## Typical client situations

| Situation | If you skip pre-launch testing |
|-----------|--------------------------------|
| AI auto-sorts or closes internal mail | Hidden instructions → **wrong queue, threats not blocked** |
| AI pre-reads mail for SOC | Polished but wrong summary → **delayed or mis-prioritized response** |
| New model feels “smarter” | Worse on attacks → **regression after go-live** |
| Cloud-only eval vendors | Samples leave your boundary → **compliance exposure** |

---

## Losses we help you avoid

1. **Shipping while attacks still slip through**  
2. **Wrong automated routing or remediation**  
3. **Silent regression after upgrades**  
4. **High confidence on wrong safety calls**

---

## How this differs from generic “AI accuracy” tests

| Typical AI evaluation | SentinelEval |
|----------------------|--------------|
| Q&A correctness | **Hidden commands in mail — still “safe”?** |
| Cloud upload | **Runs in your environment** |
| One headline % | **Attacks caught · false alarms · per-case ship gate** |
| One-off | **Repeatable history for governance** |

---

## Privacy & compliance

- **Synthetic test cases** by default  
- **In-environment execution**  
- **Defensive validation only** — simulated attacks for testing  

(Contractual DPA and controls per your org.)

---

## Suggested engagement flow

1. Workshop — define flows and unacceptable errors  
2. Agree go-live criteria  
3. Run evaluation + readout  
4. Iterate until criteria met or residual risk is documented  

---

## Glossary

| Term | Plain meaning |
|------|----------------|
| **Prompt injection** | Hidden text trying to override AI rules |
| **Instruction override** | “Ignore previous instructions…” style attacks |
| **Release gate** | Do not deploy if required tests fail |
| **Golden test cases** | Agreed answers for consistent regression |

---

## Good fit · Poor fit

**Good fit:** AI on mail/tickets/SOC assist; need governance evidence; want contract-ready acceptance criteria.  

**Poor fit:** Chatbot satisfaction only; no automated decisions on content; want a score without defining failure modes.

---

## Next steps

- **Technical README:** [README.md](../README.md)  
- **Demo recording guide:** [demos/README.md](demos/README.md)  
- **Commercial contact:** add email or intake form here  

---

*SentinelEval — Extensible local security benchmarking for AI that handles email. Test before production traffic does.*
