# Data attribution

Code and original analysis in this repository are MIT-licensed (see `LICENSE`).
Third-party datasets keep their own licenses. Cite them when you reuse the tables.

## LMArena / Chatbot Arena leaderboard

- **Dataset:** [`lmarena-ai/leaderboard-dataset`](https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset) on Hugging Face
- **Used here:** subset `text`, category `coding` (primary spine); subset `text`, overall (optional); subset `webdev` for the Code Arena tip chart
- **What we ship:** normalized weekly CSVs under `data/arena/` — not the full raw Parquet dumps
- **Upstream:** [LMSYS Chatbot Arena](https://lmarena.ai/) / LMArena
- **License:** [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), per the dataset card
- **Attribution:** *LMArena leaderboard data by LMArena, distributed under CC BY 4.0.*

## RoninForge AI Price Index

- **Site:** https://roninforge.org/ai-price-index/
- **Open data:** https://roninforge.org/data/ai-price-index/
- **License:** [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
- **Use:** primary dated list prices for input/output token rates
- **Cite:** *AI Price Index by RoninForge (https://roninforge.org/data/ai-price-index/), CC BY 4.0.*

## Model Price Watch (supplement)

- **APIs:** https://modelpricewatch.com/api/v1/price-history.json , https://modelpricewatch.com/api/v1/models.json
- **Use:** models not already covered by RoninForge
- Respect upstream Terms of Use when re-scraping; this repo only ships derived CSV panels

## Official vendor sources (manual supplements)

- [OpenAI API pricing](https://developers.openai.com/api/docs/pricing) — GPT-6 Astra prices
- [Z.AI pricing](https://docs.z.ai/guides/overview/pricing) — GLM-5.3 Flash standard prices
- [DeepSeek pricing](https://api-docs.deepseek.com/quick_start/pricing), [release note](https://api-docs.deepseek.com/news/news260910), and [model card](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash) — V4.1 Flash prices and vendor-reported launch benchmarks
- Occasional rows from vendor docs when absent from the indexes above
- See notes columns in `data/prices/price_events.csv`

## Fonts in `scripts/viz/fonts/`

- Inter / Inter Display — [SIL Open Font License 1.1](https://scripts.sil.org/OFL); the bundled license text is in `scripts/viz/fonts/LICENSE.txt`

## Media

Charts and movies under `media/` are generated from the attributed data by scripts in this repo.
