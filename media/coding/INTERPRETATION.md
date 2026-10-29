# Interpretation — coding frontier story

**What changed ( 2024-04-01 → 2026-10-26, 123 weeks ):**

1. **Shape / migration.** The score–price Pareto frontier marches **up and left**: a higher peak score and a longer cheap tail. Early weeks are short, expensive stubs (GPT-4-class). Later weeks stretch from sub-$0.10 flash/open models up to ~1547 premium peaks. See `migration.png` for the clearest before→after.

2. **Peak capability (ceiling, not wiggles).** Raw weekly maximum score rose from **1267** (`gpt-4-1106-preview`) to **1547** (`claude-opus-5.5-high`). The **running maximum** (capability frontier ceiling) ends at **1553** — about **+286 points**.

   **Why the mid-2025 dip?** Around the Gemini 2.5 Pro plateau, the Arena score wobbles a few points week to week. **Arena ratings are relative** (leaderboard composition drifts); small dips are not true capability loss. The bold envelope line tells the real story: the observed ceiling does not go backwards.

3. **Price collapse (fixed published score).** Holding an earlier peak score threshold fixed, the cheapest blended $/MTok falls by roughly two orders of magnitude on early anchors:
- Peak score of 2024-04-01 (~1267): $15 → $0.1275/MTok (−99%, ~118× cheaper)
- Peak score of 2024-04-08 (~1278): $15 → $0.1275/MTok (−99%, ~118× cheaper)
- Peak score of 2024-07-01 (~1301): $6 → $0.1275/MTok (−98%, ~47× cheaper)
- Peak score of 2024-12-30 (~1359): $1.925 → $0.15/MTok (−92%, ~13× cheaper)

   Weeks with no qualifying matched model appear as NaNs in the export; charts fill gaps ≤8 weeks (LOCF / log-linear) and draw those segments dashed.

**How to read the charts.** Ignore dominated points — only the frontier curve matters. Color = time. In the MP4, older weekly curves **stay on screen** as a muted trail so you watch the migration accumulate.

**Caveats / omissions.** Arena scores are relative and the estimator/model pool changed over time. Panel ends 2026-10-26. **Gemini 4 Argon (introductory $2/$10 through Nov 30), Claude Sonnet/Haiku 5.5, GPT-6.1 Sol, Muse Wonder and Step 3.5 Flash/Step 5 Preview enter the panel between weeks 2026-09-28 and 2026-10-26. Gemini 4 Carbon (#1 on the 2026-10-28 board) and MiMo v2.6 Pro have no list price and are excluded.** Text/coding and WebDev scores are not interchangeable. Free ($0) prices are explicit and floored at $0.05 only on log axes; the August 31 GLM-5.3 Flash rate was promotional.
