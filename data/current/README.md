# Current model watch

`current_model_watch.csv` is a dated **2026-11-10** supplement to the longitudinal Text/coding panel.

It records, for each watched model, which Arena boards have published a rating and the current list price:

- Gemini 4 Carbon is #1 on Text/coding (1563, 1,072 votes). It became generally available on November 10 at a $2/$10 introductory rate ($4 blended) through November 30, then $4/$20. That is the day after the latest snapshot (November 9), so it joins the weekly panel with the next snapshot. At $4 it would score above Opus 5.5 for half the price.
- Claude Opus 5.5 is the highest-rated model in the panel; Gemini 4 Argon is 2 points lower at half the price, on an introductory rate that doubles on December 1.
- Muse Ember (Meta, November 9) costs $0.20 blended, the same as Claude Haiku 5.5 and GPT-6 Luna. It rates above both on WebDev but has no Text/coding rating yet.
- Inkling 2 Small (Thinking Machines, November 5, $0.475) and Kimi K3.1 Pro (Max) ($4) gained their first Text/coding ratings. Both sit inside the frontier.
- Claude Fable 5.2 (November 9) cut Fable's price 20% to $8/$40 ($16 blended). It is not rated yet.
- Step 3.5 Flash is still the cheapest paid model at o1 level. DeepSeek V4.1 Flash 1017 still has a WebDev rating but no Text/coding rating.
- MiMo v2.6 Pro is #5 on Text/coding but has no list price in our sources, so it is tracked only in `arena_unmatched_models.csv`.

Text/coding and WebDev are different Arena boards with different populations and scales. Blank score cells mean “not published on that board,” not zero. DeepSeek rows carry the peak (standard) rate; off-peak is 50% of it. The 3:1 blended rate is `(3 × input + output) / 4`; cached-input discounts are excluded.

Free tiers and short promotions can be real prices, but are not treated as durable standard rates here. The GLM row therefore uses the standard rate effective September 9; the August 31 launch promotion remains documented in the longitudinal snapshot and notes. DeepSeek's peak rate is its standard price (off-peak is described as a 50% discount), so the peak row is what the weekly panel uses.

DeepSeek's API model ID at release is `deepseek-flash`; `deepseek-v4-1-flash` is this repository's normalized historical ID.

## Sources

- [LMArena leaderboard dataset](https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset) — Text/coding snapshot published November 9
- [LMArena WebDev leaderboard](https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset/tree/main/webdev) — overall snapshot published November 9
- [Z.AI pricing](https://docs.z.ai/guides/overview/pricing), [OpenAI pricing](https://developers.openai.com/api/docs/pricing), [Anthropic pricing](https://docs.claude.com/en/docs/about-claude/pricing), [DeepSeek pricing](https://api-docs.deepseek.com/quick_start/pricing), [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing) and [StepFun pricing](https://platform.stepfun.ai/docs/en/guides/pricing/details)
- [Gemini 4 Carbon availability](https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-4-carbon-now-available/) — general availability and introductory price, November 10
- [Muse Ember announcement](https://research.meta.ai/blog/muse-ember) and [Tinker models and pricing](https://tinker-docs.thinkingmachines.ai/tinker/models/models_and_pricing/) (Inkling 2 Small)
- [RoninForge AI Price Index](https://roninforge.org/data/ai-price-index/) — dated first-party prices; [Model Price Watch](https://modelpricewatch.com) for models RoninForge does not cover
