# Current model watch

`current_model_watch.csv` is a dated **2026-09-25** supplement to the longitudinal Text/coding panel.

It records, for each watched model, which Arena boards have published a rating and the current list price:

- GLM-5.3 Flash, GPT-6 Astra Max and DeepSeek V4.1 Flash (`deepseek-v4.1-flash-max`, first Text/coding score September 25) are rated on both boards.
- Claude Opus 5.5 (released September 22) leads both boards on the September 25 snapshots; its Text/coding score rests on 573 votes.
- GPT-6 Luna (released September 23) is the new $0.20 point on the coding frontier.
- MiMo v2.6 Pro is #2 on Text/coding but has no list price in our sources, so it is tracked only in `arena_unmatched_models.csv`.

Text/coding and WebDev are different Arena boards with different populations and scales. Blank score cells mean “not published on that board,” not zero. Peak and off-peak DeepSeek rows are separate price schedules. The 3:1 blended rate is `(3 × input + output) / 4`; cached-input discounts are excluded.

Free tiers and short promotions can be real prices, but are not treated as durable standard rates here. The GLM row therefore uses the standard rate effective September 9; the August 31 launch promotion remains documented in the longitudinal snapshot and notes. DeepSeek's peak rate is its standard price (off-peak is described as a 50% discount), so the peak row is what the weekly panel uses.

DeepSeek's API model ID at release is `deepseek-flash`; `deepseek-v4-1-flash` is this repository's normalized historical ID.

## Sources

- [LMArena leaderboard dataset](https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset) — Text/coding snapshot published September 25
- [LMArena WebDev leaderboard](https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset/tree/main/webdev) — overall snapshot published September 25
- [Z.AI pricing](https://docs.z.ai/guides/overview/pricing), [OpenAI pricing](https://developers.openai.com/api/docs/pricing), [Anthropic pricing](https://docs.claude.com/en/docs/about-claude/pricing), and [DeepSeek pricing](https://api-docs.deepseek.com/quick_start/pricing)
- [RoninForge AI Price Index](https://roninforge.org/data/ai-price-index/) — confirms the DeepSeek off-peak schedule under API id `deepseek-flash`
