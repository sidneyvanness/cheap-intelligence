# Current model watch

`current_model_watch.csv` is a dated **2026-09-10** supplement to the longitudinal Text/coding panel.

It deliberately keeps three states distinct:

- GLM-5.3 Flash has published Text/coding and WebDev ratings.
- GPT-6 Astra Max has a published WebDev rating, but no Text/coding rating in the latest snapshot.
- DeepSeek V4.1 Flash has current official pricing and vendor-reported launch benchmarks, but no independent Arena rating yet.

Text/coding and WebDev are different Arena boards with different populations and scales. Blank score cells mean “not published on that board,” not zero. Peak and off-peak DeepSeek rows are separate price schedules. The 3:1 blended rate is `(3 × input + output) / 4`; cached-input discounts are excluded.

Free tiers and short promotions can be real prices, but are not treated as durable standard rates here. The GLM row therefore uses the standard rate effective September 9; the August 31 launch promotion remains documented in the longitudinal snapshot and notes.

DeepSeek's API model ID at release is `deepseek-flash`; `deepseek-v4-1-flash` is this repository's normalized historical ID.

## Sources

- [LMArena leaderboard dataset](https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset) — Text/coding snapshot published September 2
- [LMArena WebDev leaderboard](https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset/tree/main/webdev) — overall snapshot published September 8
- [Z.AI pricing](https://docs.z.ai/guides/overview/pricing), [OpenAI pricing](https://developers.openai.com/api/docs/pricing), and [DeepSeek pricing](https://api-docs.deepseek.com/quick_start/pricing)
- [DeepSeek V4.1 Flash model card](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash) — vendor-reported launch capability evidence only
