# Current model watch

`current_model_watch.csv` is a dated **2026-10-28** supplement to the longitudinal Text/coding panel.

It records, for each watched model, which Arena boards have published a rating and the current list price:

- Gemini 4 Carbon is #1 on Text/coding (1,106 votes) but was only announced on October 28, at a $2/$10 introductory rate with limited access. It is not on Google's pricing page, so it stays off the price axis.
- Claude Opus 5.5 is the highest-rated priced model; Gemini 4 Argon (released October 13) is 9 points lower at half the price, on an introductory rate that doubles on December 1.
- Claude Haiku 5.5 (released October 7) takes the $0.20 point on the coding frontier from GPT-6 Luna, whose score fell as votes accumulated.
- Step 3.5 Flash gained a list price in our sources on October 8 and is now the cheapest paid model at o1 level.
- DeepSeek's 0910 V4.1 Flash build was replaced by the 1017 build on October 17 at the same price; the 1017 build has a WebDev rating but no Text/coding rating yet.
- MiMo v2.6 Pro is #4 on Text/coding but has no list price in our sources, so it is tracked only in `arena_unmatched_models.csv`.

Text/coding and WebDev are different Arena boards with different populations and scales. Blank score cells mean “not published on that board,” not zero. DeepSeek rows carry the peak (standard) rate; off-peak is 50% of it. The 3:1 blended rate is `(3 × input + output) / 4`; cached-input discounts are excluded.

Free tiers and short promotions can be real prices, but are not treated as durable standard rates here. The GLM row therefore uses the standard rate effective September 9; the August 31 launch promotion remains documented in the longitudinal snapshot and notes. DeepSeek's peak rate is its standard price (off-peak is described as a 50% discount), so the peak row is what the weekly panel uses.

DeepSeek's API model ID at release is `deepseek-flash`; `deepseek-v4-1-flash` is this repository's normalized historical ID.

## Sources

- [LMArena leaderboard dataset](https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset) — Text/coding snapshot published October 28
- [LMArena WebDev leaderboard](https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset/tree/main/webdev) — overall snapshot published October 28
- [Z.AI pricing](https://docs.z.ai/guides/overview/pricing), [OpenAI pricing](https://developers.openai.com/api/docs/pricing), [Anthropic pricing](https://docs.claude.com/en/docs/about-claude/pricing), [DeepSeek pricing](https://api-docs.deepseek.com/quick_start/pricing), [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing) and [StepFun pricing](https://platform.stepfun.ai/docs/en/guides/pricing/details)
- [Google's Gemini 4 Carbon announcement](https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-4-carbon/) — announced introductory price, not a list price
- [RoninForge AI Price Index](https://roninforge.org/data/ai-price-index/) — dated first-party prices; [Model Price Watch](https://modelpricewatch.com) for models RoninForge does not cover
