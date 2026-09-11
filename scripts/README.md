# Scripts

All paths are **repo-relative** (run from repo root).

| Script | Purpose |
|--------|---------|
| `build_frontiers.py` | Shared name-match / Pareto helpers (+ optional overall rebuild) |
| `build_coding_frontiers.py` | Coding Elo × price weekly panel + same-Elo cost |
| `build_export.py` | Slim CSV/xlsx export under `data/export/coding/` |
| `viz/make_story_viz.py` | Static story charts → `media/coding/` |
| `viz/make_chaptered_movie.py` | Chaptered MP4 → `media/coding/` |
| `viz/fonts/` | Bundled Inter fonts (OFL) |

```bash
pip install -r requirements.txt
python scripts/build_coding_frontiers.py
python scripts/build_export.py
python scripts/viz/make_story_viz.py --skip-anim
# ffmpeg required:
python scripts/viz/make_chaptered_movie.py
```
