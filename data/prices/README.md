# LLM API price panel

Normalized historical list prices for quality–price Pareto analysis.

**Generated:** 2026-09-11  
**Price unit:** USD per 1M tokens  
**Blended (v1):** `(3 * input + 1 * output) / 4`

## Files

| File | Description |
|------|-------------|
| `price_events.csv` | Dated price windows (input / output / cached / …) |
| `weekly_blended_prices.csv` | Monday panel of effective prices + 3:1 blend |

Raw RoninForge / Model Price Watch JSON dumps are **not** shipped in this public repo (large; regenerate from upstream).

## Sources

1. **RoninForge AI Price Index** (preferred) — https://roninforge.org/ai-price-index/ — **CC BY 4.0**
2. **Model Price Watch** (supplement) — https://modelpricewatch.com
3. Occasional official vendor docs (see `notes` in `price_events.csv`)

## Schemas

`price_events.csv`:  
`provider, model_id, model_name_canonical, variation, price_usd_per_mtok, effective_from, effective_to, source, confidence, source_url, notes`

`weekly_blended_prices.csv`:  
`week_start, provider, model_id, model_name_canonical, input_usd_per_mtok, output_usd_per_mtok, blended_3_1_usd_per_mtok, source_note`

## Caveats

- Sparse early history; no invented prices
- Cached / tier2 variations exist in events but are **not** used in the weekly blend
