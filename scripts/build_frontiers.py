#!/usr/bin/env python3
"""Join Arena Elo weekly snapshots to blended prices; compute Pareto frontiers."""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "data"
OUT = ROOT / "frontiers"
OUT.mkdir(parents=True, exist_ok=True)

ARENA_PATH = ROOT / "arena" / "arena_elo_snapshots_weekly.csv"
PRICES_PATH = ROOT / "prices" / "weekly_blended_prices.csv"
XWALK_PATH = ROOT / "model_name_crosswalk.csv"
SIZES_PATH = ROOT / "model_sizes.csv"

PROVIDER_PRIORITY = {
    "openai": 0,
    "anthropic": 0,
    "google": 0,
    "meta": 0,
    "deepseek": 0,
    "mistral": 0,
    "xai": 0,
    "cohere": 0,
    "amazon": 0,
    "alibaba": 1,
    "z.ai": 1,
    "moonshot": 1,
    "minimax": 1,
    "ai21": 1,
    "reka": 1,
    "ibm": 1,
    "01.ai": 1,
    "together": 3,
    "fireworks": 3,
    "deepinfra": 3,
    "groq": 3,
    "perplexity": 4,
}


def provider_rank(p: str) -> int:
    key = (p or "").strip().lower()
    if key in PROVIDER_PRIORITY:
        return PROVIDER_PRIORITY[key]
    for k, v in PROVIDER_PRIORITY.items():
        if k in key:
            return v
    return 2


def normalize_name(s) -> str:
    if s is None or (isinstance(s, float) and np.isnan(s)):
        return ""
    t = str(s).strip().lower()
    t = t.replace("_", "-").replace(" ", "-").replace("/", "-")
    t = t.replace("(", "").replace(")", "")
    t = re.sub(r"-+", "-", t).strip("-")
    for pat in [
        r"^openai-",
        r"^anthropic-",
        r"^google-",
        r"^meta-llama-",
        r"^meta-",
        r"^alibaba-",
        r"^zhipu-",
        r"^zai-",
        r"^xai-",
        r"^amazon-",
        r"^aws-",
        r"^mistralai-",
        r"^cohere-",
        r"^01ai-",
        r"^01-ai-",
        r"^together-",
        r"^fireworks-",
        r"^deepinfra-",
        r"^groq-",
        r"^deepseek-ai-",
    ]:
        t2 = re.sub(pat, "", t)
        if t2 != t:
            t = t2
            break
    return re.sub(r"-+", "-", t).strip("-")


DATE_PATTERNS = [
    re.compile(r"-\d{4}-\d{2}-\d{2}$"),
    re.compile(r"-\d{8}$"),
    re.compile(r"-\d{4}-\d{2}$"),
    re.compile(r"-\d{6}$"),
]

VARIANT_SUFFIXES = [
    re.compile(r"-thinking(-\d+k)?$"),
    re.compile(r"-thinking$"),
    re.compile(r"-high(-\d+k)?$"),
    re.compile(r"-high$"),
    re.compile(r"-max$"),
    re.compile(r"-xhigh$"),
    re.compile(r"-medium$"),
    re.compile(r"-no-thinking$"),
    re.compile(r"-thinking-minimal$"),
    re.compile(r"-preview$"),
    re.compile(r"-exp$"),
    re.compile(r"-latest(-\d+)?$"),
    re.compile(r"-chat-latest(-\d+)?$"),
    re.compile(r"-api-\d+$"),
    re.compile(r"-dev-api$"),
    re.compile(r"-bf16$"),
    re.compile(r"-fp8$"),
    re.compile(r"-nvfp4$"),
    re.compile(r"-online$"),
]


def strip_date(n: str) -> str:
    t = n
    for pat in DATE_PATTERNS:
        t2 = pat.sub("", t)
        if t2 != t and len(t2) >= 3:
            return t2
    return t


def strip_variant(n: str) -> str:
    t = n
    for pat in VARIANT_SUFFIXES:
        t2 = pat.sub("", t)
        if t2 != t and len(t2) >= 3:
            t = t2
    return t


def core_keys(name: str, include_aggressive_alts: bool = True) -> list[str]:
    n = normalize_name(name)
    if not n:
        return []
    keys = [n]
    for fn in (strip_date, strip_variant):
        n2 = fn(n)
        if n2 not in keys:
            keys.append(n2)
    n3 = strip_date(strip_variant(n))
    if n3 not in keys:
        keys.append(n3)
    n4 = strip_variant(strip_date(n))
    if n4 not in keys:
        keys.append(n4)

    if include_aggressive_alts:
        alt = []
        for k in list(keys):
            if k.startswith("chatgpt-4o"):
                alt.append("gpt-4o")
            if k.startswith("gpt-4o-mini"):
                alt.append("gpt-4o-mini")
            elif k.startswith("gpt-4o"):
                alt.append("gpt-4o")
            if k.startswith("gpt-4.1-mini"):
                alt.append("gpt-4.1-mini")
            elif k.startswith("gpt-4.1-nano"):
                alt.append("gpt-4.1-nano")
            elif k.startswith("gpt-4.1"):
                alt.append("gpt-4.1")
            if k.startswith("gpt-4-turbo"):
                alt.append("gpt-4-turbo")
            if k.startswith("gpt-3.5-turbo") or k.startswith("gpt-3-5-turbo"):
                alt.append("gpt-3.5-turbo")
            m = re.match(r"(gemini-[\d.]+-flash-lite)", k)
            if m:
                alt.append(m.group(1))
            m = re.match(r"(gemini-[\d.]+-(?:flash|pro))", k)
            if m:
                alt.append(m.group(1))
            if k.startswith("command-r-plus"):
                alt.append("command-r-plus")
            elif k.startswith("command-r"):
                alt.append("command-r")
            if "nova-lite" in k:
                alt.append("nova-lite")
            if "nova-micro" in k:
                alt.append("nova-micro")
            if "nova-pro" in k and "premier" not in k:
                alt.append("nova-pro")
            if "nova-2-lite" in k:
                alt.append("nova-2-lite")
            if "llama-4-maverick" in k:
                alt.append("llama-4-maverick")
            if "llama-4-scout" in k:
                alt.append("llama-4-scout")
            m = re.match(r"(llama-[\d.]+-\d+b)", k)
            if m:
                alt.append(m.group(1))
            if k.startswith("deepseek-r1"):
                alt.append("deepseek-r1")
            m = re.match(r"(deepseek-v[\d.]+(?:-flash|-pro)?)", k)
            if m:
                alt.append(m.group(1))
            # DeepSeek V4.1 Flash / deepseek-flash API alias
            if "deepseek-v4.1-flash" in k or "deepseek-v4-1-flash" in k or k in ("deepseek-flash", "deepseek-flash-high"):
                alt.append("deepseek-v4-1-flash")
                alt.append("deepseek-flash")
            if "gpt-6-astra" in k or k == "astra":
                alt.append("gpt-6-astra")
            m = re.match(r"(gpt-6(?:-astra)?)", k)
            if m:
                alt.append("gpt-6-astra" if "astra" in k or k == "gpt-6" else m.group(1))
            if k.startswith("grok-4.6") or k.startswith("grok-4-6"):
                alt.append("grok-4.6")
            if re.match(r"mistral-large-\d{4}", k) or k == "mistral-large-3":
                alt.append("mistral-large")
            if "mistral-small" in k:
                alt.append("mistral-small")
            if "mistral-medium" in k:
                alt.append("mistral-medium")
            if "mixtral-8x7b" in k:
                alt.append("mixtral-8x7b")
                alt.append("mistral-mixtral-8x7b")
            if "mixtral-8x22b" in k:
                alt.append("mixtral-8x22b")
                alt.append("mistral-mixtral-8x22b")
            if "gpt-oss-120b" in k:
                alt.append("gpt-oss-120b")
            if "gpt-oss-20b" in k:
                alt.append("gpt-oss-20b")
            if k.startswith("kimi-k2.5") or k.startswith("kimi-k2-5"):
                alt.append("kimi-k2.5")
            if k.startswith("kimi-k2.6"):
                alt.append("kimi-k2.6")
            if k.startswith("minimax-m2.5"):
                alt.append("minimax-m2.5")
            if k.startswith("minimax-m2.7"):
                alt.append("minimax-m2.7")
            if k.startswith("minimax-m3"):
                alt.append("minimax-m3")
            if re.match(r"o\d", k):
                base = re.split(r"-\d{4}", k)[0]
                base = re.sub(r"-high$", "", base)
                alt.append(base)
            m = re.match(r"(gpt-5(?:\.\d+)?(?:-mini|-nano|-chat)?)", k)
            if m:
                alt.append(m.group(1))
            if "muse-glimmer" in k:
                alt.append("muse-glimmer")
                alt.append("muse-glimmer-30b")
            if "jamba" in k and "large" in k:
                alt.append("jamba-large")
            if "jamba" in k and "mini" in k:
                alt.append("jamba-mini")
        for a in alt:
            a = normalize_name(a)
            if a and a not in keys:
                keys.append(a)
        more = []
        for k in keys:
            for kd in (k.replace(".", "-"), k.replace(".", "")):
                if kd and kd not in keys and kd not in more:
                    more.append(kd)
        keys.extend(more)
    return keys


# arena normalized name -> (preferred model_id, method, confidence)
MANUAL_ALIASES: dict[str, tuple[str, str, float]] = {
    "chatgpt-4o-latest": ("gpt-4o", "manual_alias", 0.9),
    "chatgpt-4o-latest-20250326": ("gpt-4o", "manual_alias", 0.9),
    "gpt-4o-2024-05-13": ("gpt-4o", "manual_alias", 0.95),
    "gpt-4o-2024-08-06": ("gpt-4o", "manual_alias", 0.95),
    "gpt-4o-mini-2024-07-18": ("gpt-4o-mini", "manual_alias", 0.95),
    "gpt-4-turbo-2024-04-09": ("gpt-4-turbo", "manual_alias", 0.95),
    "gpt-4-0125-preview": ("gpt-4-turbo", "manual_alias", 0.85),
    "gpt-4-1106-preview": ("gpt-4-turbo", "manual_alias", 0.85),
    "gpt-4-0613": ("gpt-4", "manual_alias", 0.9),
    "gpt-4-0314": ("gpt-4", "manual_alias", 0.9),
    "gpt-3.5-turbo-0125": ("openai-gpt-3-5-turbo", "manual_alias", 0.95),
    "gpt-3.5-turbo-1106": ("openai-gpt-3-5-turbo", "manual_alias", 0.95),
    "grok-4.3": ("grok-4.3", "manual_alias", 1.0),
    "grok-4.5": ("grok-4.5", "manual_alias", 1.0),
    "grok-4.6-high": ("grok-4.6", "manual_alias", 0.9),
    "grok-4.20-beta1": ("xai-grok-4-20", "manual_alias", 0.8),
    "grok-4.20-beta-0309-reasoning": ("grok-4.20-0309-reasoning", "manual_alias", 0.9),
    "grok-4.20-multi-agent-beta-0309": ("grok-4.20-multi-agent-0309", "manual_alias", 0.9),
    "claude-3-5-sonnet-20241022": ("claude-3-5-sonnet-20240620", "manual_alias", 0.75),
    "gemini-2.0-flash-lite-preview-02-05": ("gemini-2.0-flash", "manual_alias", 0.75),
    "gpt-4.1-2025-04-14": ("gpt-4.1", "manual_alias", 0.95),
    "gpt-4.1-mini-2025-04-14": ("gpt-4.1-mini", "manual_alias", 0.95),
    "gpt-4.1-nano-2025-04-14": ("gpt-4.1-nano", "manual_alias", 0.95),
    "o1-2024-12-17": ("o1", "manual_alias", 0.95),
    "o1-mini": ("o1-mini", "manual_alias", 1.0),
    "o1-preview": ("o1-preview", "manual_alias", 1.0),
    "o3-2025-04-16": ("o3", "manual_alias", 0.95),
    "o3-mini": ("o3-mini", "manual_alias", 1.0),
    "o3-mini-high": ("o3-mini", "manual_alias", 0.9),
    "o4-mini-2025-04-16": ("o4-mini", "manual_alias", 0.95),
    "gemini-1.5-flash-001": ("gemini-1.5-flash", "manual_alias", 0.95),
    "gemini-1.5-flash-002": ("gemini-1.5-flash", "manual_alias", 0.95),
    "gemini-1.5-flash-api-0514": ("gemini-1.5-flash", "manual_alias", 0.9),
    "gemini-1.5-pro-001": ("gemini-1.5-pro", "manual_alias", 0.95),
    "gemini-1.5-pro-002": ("gemini-1.5-pro", "manual_alias", 0.95),
    "gemini-1.5-pro-api-0514": ("gemini-1.5-pro", "manual_alias", 0.9),
    "gemini-2.0-flash-001": ("gemini-2.0-flash", "manual_alias", 0.95),
    "gemini-2.5-flash": ("gemini-2.5-flash", "manual_alias", 1.0),
    "gemini-2.5-pro": ("gemini-2.5-pro", "manual_alias", 1.0),
    "gemini-2.5-flash-preview-09-2025": ("gemini-2.5-flash", "manual_alias", 0.9),
    "gemini-2.5-flash-lite-preview-06-17-thinking": ("gemini-2.5-flash-lite", "manual_alias", 0.85),
    "gemini-2.5-flash-lite-preview-09-2025-no-thinking": ("gemini-2.5-flash-lite", "manual_alias", 0.85),
    "gemini-3-flash": ("gemini-3-flash-preview", "manual_alias", 0.9),
    "gemini-3-flash-thinking-minimal": ("gemini-3-flash-preview", "manual_alias", 0.85),
    "gemini-3.1-flash-lite-preview": ("gemini-3.1-flash-lite", "manual_alias", 0.95),
    "gemini-3.1-pro-preview": ("gemini-3.1-pro-preview", "manual_alias", 1.0),
    "gemini-3.5-flash": ("gemini-3.5-flash", "manual_alias", 1.0),
    "gemini-3.5-flash-high": ("gemini-3.5-flash", "manual_alias", 0.9),
    "gemini-3.5-flash-medium": ("gemini-3.5-flash", "manual_alias", 0.9),
    "gemini-3.5-flash-lite": ("gemini-3.5-flash-lite", "manual_alias", 1.0),
    "gemini-3.6-flash": ("gemini-3.6-flash", "manual_alias", 1.0),
    "gemini-3.6-flash-high": ("gemini-3.6-flash", "manual_alias", 0.9),
    "gemini-3.7-flash-high": ("gemini-3.7-flash", "manual_alias", 0.9),
    "gemini-3.8-flash-high": ("gemini-3.8-flash", "manual_alias", 0.9),
    "amazon-nova-lite-v1.0": ("nova-lite", "manual_alias", 0.95),
    "amazon-nova-micro-v1.0": ("nova-micro", "manual_alias", 0.95),
    "amazon-nova-pro-v1.0": ("nova-pro", "manual_alias", 0.95),
    "nova-2-lite": ("nova-2-lite", "manual_alias", 1.0),
    "command-r": ("command-r", "manual_alias", 1.0),
    "command-r-08-2024": ("command-r", "manual_alias", 0.95),
    "command-r-plus": ("command-r-plus", "manual_alias", 1.0),
    "command-r-plus-08-2024": ("command-r-plus", "manual_alias", 0.95),
    "jamba-1.5-large": ("jamba-large", "manual_alias", 0.9),
    "jamba-1.5-mini": ("jamba-mini", "manual_alias", 0.9),
    "deepseek-v4-flash": ("deepseek-v4-flash", "manual_alias", 1.0),
    "deepseek-v4-pro": ("deepseek-v4-pro", "manual_alias", 1.0),
    "deepseek-v4-flash-high-preview": ("deepseek-v4-flash", "manual_alias", 0.85),
    "deepseek-v4-flash-thinking": ("deepseek-v4-flash", "manual_alias", 0.85),
    "deepseek-v4-pro-thinking": ("deepseek-v4-pro", "manual_alias", 0.85),
    "deepseek-v4-pro-high-preview": ("deepseek-v4-pro", "manual_alias", 0.85),
    "deepseek-v4-pro-high-20260813": ("deepseek-v4-pro", "manual_alias", 0.85),
    "llama-4-maverick-17b-128e-instruct": ("llama-4-maverick", "manual_alias", 0.9),
    "llama-4-scout-17b-16e-instruct": ("llama-4-scout", "manual_alias", 0.9),
    "llama-3.1-405b-instruct": ("llama-3.1-405b", "manual_alias", 0.9),
    "llama-3.1-405b-instruct-bf16": ("llama-3.1-405b", "manual_alias", 0.85),
    "llama-3.1-405b-instruct-fp8": ("llama-3.1-405b", "manual_alias", 0.85),
    "llama-3.1-70b-instruct": ("llama-3.1-70b", "manual_alias", 0.9),
    "llama-3.1-8b-instruct": ("llama-3.1-8b", "manual_alias", 0.9),
    "llama-3.3-70b-instruct": ("llama-3.3-70b", "manual_alias", 0.9),
    "mistral-large-2402": ("mistral-large", "manual_alias", 0.9),
    "mistral-large-2407": ("mistral-large", "manual_alias", 0.9),
    "mistral-large-2411": ("mistral-large", "manual_alias", 0.9),
    "mistral-large-3": ("mistral-large", "manual_alias", 0.85),
    "mistral-small-24b-instruct-2501": ("mistral-small", "manual_alias", 0.85),
    "mistral-small-2506": ("mistral-small", "manual_alias", 0.9),
    "mistral-small-3.1-24b-instruct-2503": ("mistral-small", "manual_alias", 0.85),
    "mistral-medium": ("mistral-medium", "manual_alias", 1.0),
    "mistral-medium-2505": ("mistral-medium", "manual_alias", 0.9),
    "mistral-medium-2508": ("mistral-medium", "manual_alias", 0.9),
    "mistral-medium-3.5": ("mistral-medium", "manual_alias", 0.85),
    "mixtral-8x7b-instruct-v0.1": ("mistral-mixtral-8x7b", "manual_alias", 0.9),
    "mixtral-8x22b-instruct-v0.1": ("mistral-mixtral-8x22b", "manual_alias", 0.9),
    "qwen3-32b": ("alibaba-qwen3-32b", "manual_alias", 0.95),
    "qwen3.5-122b-a10b": ("alibaba-qwen3-5-122b-a10b", "manual_alias", 0.95),
    "qwen3.5-27b": ("alibaba-qwen3-5-27b", "manual_alias", 0.95),
    "qwen3.5-35b-a3b": ("alibaba-qwen3-5-35b-a3b", "manual_alias", 0.95),
    "qwen3.5-397b-a17b": ("alibaba-qwen3-5-397b-a17b", "manual_alias", 0.95),
    "qwen3.5-flash": ("alibaba-qwen3-5-flash", "manual_alias", 0.95),
    "qwen3.6-plus": ("alibaba-qwen3-6-plus", "manual_alias", 0.95),
    "qwen3.7-plus": ("alibaba-qwen3-7-plus", "manual_alias", 0.95),
    "qwen3.8-27b": ("alibaba-qwen3-8-27b", "manual_alias", 0.95),
    "qwen3.8-max": ("alibaba-qwen3-8-max", "manual_alias", 0.95),
    "qwen3-max-2025-09-23": ("qwen3-max", "manual_alias", 0.9),
    "qwen3-max-preview": ("qwen3-max", "manual_alias", 0.85),
    "qwen-max-0919": ("qwen-max", "manual_alias", 0.9),
    "qwen-plus-0125": ("qwen-plus", "manual_alias", 0.9),
    "glm-4.5": ("zhipu-glm-4-5", "manual_alias", 0.95),
    "glm-4.5-air": ("zhipu-glm-4-5-air", "manual_alias", 0.95),
    "glm-4.6": ("zhipu-glm-4-6", "manual_alias", 0.95),
    "glm-4.6v": ("zhipu-glm-4-6v", "manual_alias", 0.95),
    "glm-4.7": ("zhipu-glm-4-7", "manual_alias", 0.95),
    "glm-4.7-flash": ("zhipu-glm-4-7-flash", "manual_alias", 0.95),
    "glm-5": ("zhipu-glm-5", "manual_alias", 0.95),
    "glm-5.1": ("zhipu-glm-5-1", "manual_alias", 0.95),
    "glm-5.2-max": ("zhipu-glm-5-2", "manual_alias", 0.9),
    "glm-5.2-max": ("zhipu-glm-5-2", "manual_alias", 0.9),  # noqa duplicate ok
    "glm-5.3-flash": ("zhipu-glm-5-3-flash", "manual_alias", 0.95),
    "glm-5.3-max": ("zhipu-glm-5-3", "manual_alias", 0.9),
    "glm-5v-turbo": ("zhipu-glm-5v-turbo", "manual_alias", 0.95),
    "glm-5.2 max": ("zhipu-glm-5-2", "manual_alias", 0.9),
    "grok-2-2024-08-13": ("grok-2", "manual_alias", 0.9),
    "grok-2-mini-2024-08-13": ("grok-2-mini", "manual_alias", 0.9),
    "grok-3-preview-02-24": ("grok-3", "manual_alias", 0.85),
    "grok-3-mini-beta": ("grok-3-mini", "manual_alias", 0.9),
    "grok-3-mini-high": ("grok-3-mini", "manual_alias", 0.85),
    "grok-4-0709": ("grok-4", "manual_alias", 0.9),
    "grok-4-fast-reasoning": ("grok-4-fast-reasoning", "manual_alias", 1.0),
    "kimi-k2.5-instant": ("kimi-k2.5", "manual_alias", 0.9),
    "kimi-k2.5-thinking": ("kimi-k2.5", "manual_alias", 0.9),
    "kimi-k2.6": ("kimi-k2.6", "manual_alias", 1.0),
    "kimi-k2-0711-preview": ("kimi-k2", "manual_alias", 0.85),
    "kimi-k2-0905-preview": ("kimi-k2", "manual_alias", 0.85),
    "minimax-m2": ("minimax-m2", "manual_alias", 1.0),
    "minimax-m2.5": ("minimax-m2.5", "manual_alias", 1.0),
    "minimax-m2.7": ("minimax-m2.7", "manual_alias", 1.0),
    "minimax-m3": ("minimax-m3", "manual_alias", 1.0),
    "minimax-m2.1-preview": ("minimax-m2", "manual_alias", 0.8),
    "gpt-oss-120b": ("gpt-oss-120b", "manual_alias", 1.0),
    "gpt-oss-20b": ("gpt-oss-20b", "manual_alias", 1.0),
    "muse-glimmer": ("fireworks-muse-glimmer-30b", "manual_alias", 0.85),
    "claude-fable-5.1-max": ("claude-fable-5-1", "manual_alias", 0.9),
    "claude-opus-5-high": ("claude-opus-5", "manual_alias", 0.9),
    "claude-opus-5-max": ("claude-opus-5", "manual_alias", 0.9),
    "claude-sonnet-5-high": ("claude-sonnet-5", "manual_alias", 0.9),
    "claude-sonnet-5-thinking": ("claude-sonnet-5", "manual_alias", 0.85),
    # --- 2026-09 refresh: Astra / DeepSeek V4.1 Flash / Grok 4.6 ---
    "gpt-6-astra": ("gpt-6-astra", "manual_alias", 1.0),
    "gpt-6-astra-high": ("gpt-6-astra", "manual_alias", 0.9),
    "gpt-6-astra-xhigh": ("gpt-6-astra", "manual_alias", 0.9),
    "gpt-6-astra-max": ("gpt-6-astra", "manual_alias", 0.9),
    "gpt-6-astra-medium": ("gpt-6-astra", "manual_alias", 0.9),
    "gpt-6-astra-low": ("gpt-6-astra", "manual_alias", 0.9),
    "gpt-6-astra-non-reasoning": ("gpt-6-astra", "manual_alias", 0.85),
    "astra": ("gpt-6-astra", "manual_alias", 0.8),
    "deepseek-v4.1-flash": ("deepseek-v4-1-flash", "manual_alias", 1.0),
    "deepseek-v4-1-flash": ("deepseek-v4-1-flash", "manual_alias", 1.0),
    "deepseek-flash": ("deepseek-v4-1-flash", "manual_alias", 0.95),
    "deepseek-v4.1-flash-high": ("deepseek-v4-1-flash", "manual_alias", 0.9),
    "deepseek-v4-1-flash-high": ("deepseek-v4-1-flash", "manual_alias", 0.9),
    "deepseek-v4.1-flash-thinking": ("deepseek-v4-1-flash", "manual_alias", 0.85),
    "deepseek-v4-1-flash-thinking": ("deepseek-v4-1-flash", "manual_alias", 0.85),
    "deepseek-flash-high": ("deepseek-v4-1-flash", "manual_alias", 0.9),
    "grok-4.6": ("grok-4.6", "manual_alias", 1.0),
    "grok-4-6": ("grok-4.6", "manual_alias", 0.95),
    "grok-4.6-high": ("grok-4.6", "manual_alias", 0.9),
    "grok-4-6-high": ("grok-4.6", "manual_alias", 0.9),
    "grok-4.6-xhigh": ("grok-4.6", "manual_alias", 0.9),
    # --- 2026-09-25 snapshot: Opus 5.5 / GPT-6 Sol & Luna / Grok 4.7 / Fable 5 / DeepSeek V4.1 Flash Max ---
    "claude-opus-5.5": ("claude-opus-5-5", "manual_alias", 1.0),
    "claude-opus-5.5-high": ("claude-opus-5-5", "manual_alias", 0.9),
    "claude-opus-5.5-max": ("claude-opus-5-5", "manual_alias", 0.9),
    "claude-fable-5-high": ("claude-fable-5", "manual_alias", 0.9),
    "gpt-6-sol": ("gpt-6-sol", "manual_alias", 1.0),
    "gpt-6-sol-max": ("gpt-6-sol", "manual_alias", 0.9),
    "gpt-6-sol-high": ("gpt-6-sol", "manual_alias", 0.9),
    "gpt-6-luna": ("gpt-6-luna", "manual_alias", 1.0),
    "gpt-6-luna-max": ("gpt-6-luna", "manual_alias", 0.9),
    "gpt-6-luna-high": ("gpt-6-luna", "manual_alias", 0.9),
    "grok-4.7": ("grok-4.7", "manual_alias", 1.0),
    "grok-4.7-high": ("grok-4.7", "manual_alias", 0.9),
    "grok-4.7-xhigh": ("grok-4.7", "manual_alias", 0.9),
    "deepseek-v4.1-flash-max": ("deepseek-v4-1-flash", "manual_alias", 0.9),
    # --- 2026-10-28 snapshot: Gemini 4 Argon / Claude 5.5 Sonnet & Haiku / GPT-6.1 Sol / Muse Wonder ---
    "gemini-4-argon-high": ("gemini-4-argon", "manual_alias", 0.9),
    "claude-sonnet-5.5-xhigh": ("claude-sonnet-5-5", "manual_alias", 0.9),
    "claude-haiku-5.5-high": ("claude-haiku-5-5", "manual_alias", 0.9),
    "gpt-6.1-sol-max": ("gpt-6.1-sol", "manual_alias", 0.9),
    "muse-wonder-max": ("meta-muse-wonder", "manual_alias", 0.9),
    "mistral-large-4": ("mistral-large-4", "manual_alias", 1.0),
    "step-5-preview": ("stepfun-step-5-preview", "manual_alias", 0.95),
    "step-3.5-flash": ("stepfun-step-3-5-flash", "manual_alias", 0.95),
    "kimi-k3-max": ("moonshot-kimi-k3", "manual_alias", 0.9),
}


def build_price_lookups(prices: pd.DataFrame):
    meta = prices[["provider", "model_id", "model_name_canonical"]].drop_duplicates()
    by_id = {}
    # model_id-normalized -> candidates (exact id keys only from model_id)
    id_index: dict[str, list[dict]] = {}
    # canonical-normalized -> candidates (weaker)
    can_index: dict[str, list[dict]] = {}
    # broader core keys from model_id only (not canonical — avoids GPT-4.1 label pollution)
    core_index: dict[str, list[dict]] = {}

    for _, r in meta.iterrows():
        rec = {
            "provider": r["provider"],
            "model_id": r["model_id"],
            "model_name_canonical": r["model_name_canonical"],
            "rank": provider_rank(r["provider"]),
        }
        by_id[r["model_id"]] = rec
        nid = normalize_name(r["model_id"])
        id_index.setdefault(nid, []).append(rec)
        # also raw model_id as key
        id_index.setdefault(r["model_id"].lower(), []).append(rec)

        ncan = normalize_name(r["model_name_canonical"])
        if ncan and ncan != nid:
            can_index.setdefault(ncan, []).append(rec)

        for k in core_keys(r["model_id"], include_aggressive_alts=True):
            core_index.setdefault(k, []).append(rec)

    def dedupe(lst):
        by = {}
        for rec in lst:
            mid = rec["model_id"]
            if mid not in by or rec["rank"] < by[mid]["rank"]:
                by[mid] = rec
        return sorted(by.values(), key=lambda x: (x["rank"], x["model_id"]))

    for d in (id_index, can_index, core_index):
        for k in list(d.keys()):
            d[k] = dedupe(d[k])

    return by_id, id_index, can_index, core_index


def resolve_model_id(mid: str, by_id, id_index, core_index):
    if mid in by_id:
        return by_id[mid]
    n = normalize_name(mid)
    for idx in (id_index, core_index):
        cands = idx.get(n) or idx.get(mid.lower())
        if cands:
            # prefer exact model_id match
            for c in cands:
                if c["model_id"] == mid or normalize_name(c["model_id"]) == n:
                    return c
            return cands[0]
    return None


def pick_match(arena_name: str, by_id, id_index, can_index, core_index) -> dict | None:
    n = normalize_name(arena_name)

    def pack(rec, method, conf, key):
        return {
            "model_name_arena": arena_name,
            "model_id_price": rec["model_id"],
            "provider": rec["provider"],
            "model_name_canonical": rec["model_name_canonical"],
            "match_method": method,
            "match_confidence": conf,
            "normalized_arena": n,
            "matched_key": key,
        }

    # Manual alias: resolve preferred model_id strictly
    if n in MANUAL_ALIASES:
        mid, method, conf = MANUAL_ALIASES[n]
        rec = resolve_model_id(mid, by_id, id_index, core_index)
        if rec is not None:
            return pack(rec, method, conf, normalize_name(mid))
        # alias target missing from price catalog — fall through / unmatched

    # Exact normalized model_id
    if n in id_index:
        return pack(id_index[n][0], "exact_model_id", 1.0, n)

    # Strip date then exact id
    nd = strip_date(n)
    if nd != n and nd in id_index:
        return pack(id_index[nd][0], "strip_date", 0.95, nd)

    nv = strip_variant(nd)
    if nv in id_index:
        return pack(id_index[nv][0], "strip_variant", 0.9, nv)

    # Exact canonical (only if unique high-confidence and not colliding oddly)
    if n in can_index and len(can_index[n]) == 1:
        return pack(can_index[n][0], "exact_canonical", 0.95, n)

    # Core keys from arena against model_id-derived core index
    keys = core_keys(arena_name, include_aggressive_alts=True)
    best = None
    for i, k in enumerate(keys):
        cands = id_index.get(k) or core_index.get(k)
        if not cands:
            continue
        rec = cands[0]
        # Guard: refuse if arena key is a strict prefix mismatch like gpt-4 vs gpt-4.1
        # Prefer candidate whose normalized id equals key
        exactish = [c for c in cands if normalize_name(c["model_id"]) == k]
        if exactish:
            rec = exactish[0]
        conf = 1.0 if i == 0 else (0.92 if i <= 2 else 0.82)
        method = "fuzzy_core" if i > 2 else "core_key"
        cand = pack(rec, method, conf, k)
        if best is None or cand["match_confidence"] > best["match_confidence"]:
            best = cand
        if conf >= 0.92 and exactish:
            return cand

    if best and best["match_confidence"] >= 0.82:
        return best
    return None


def monday_on_or_before(d: pd.Timestamp) -> pd.Timestamp:
    return d - pd.Timedelta(days=int(d.weekday()))


def is_pareto(elos: np.ndarray, prices: np.ndarray) -> np.ndarray:
    n = len(elos)
    on = np.ones(n, dtype=bool)
    for i in range(n):
        better_eq_elo = elos >= elos[i]
        better_eq_price = prices <= prices[i]
        strict = (elos > elos[i]) | (prices < prices[i])
        dom = better_eq_elo & better_eq_price & strict
        dom[i] = False
        if dom.any():
            on[i] = False
    return on


def match_sizes(arena_names: list[str], sizes: pd.DataFrame, xwalk: pd.DataFrame) -> pd.DataFrame:
    size_map = {}
    for _, r in sizes.iterrows():
        entry = {"params_b": r.get("params_b"), "open_weights": r.get("open_weights")}
        for k in core_keys(r["model_name"]) + [normalize_name(r["model_name"])]:
            if k and k not in size_map:
                size_map[k] = entry
    for _, r in xwalk.iterrows():
        an = r.get("arena_name")
        if pd.isna(an) or pd.isna(r.get("params_b")):
            continue
        entry = {"params_b": r["params_b"], "open_weights": True}
        for k in core_keys(an) + [normalize_name(an)]:
            if k and k not in size_map:
                size_map[k] = entry
            elif k and (size_map[k].get("params_b") is None or (isinstance(size_map[k].get("params_b"), float) and np.isnan(size_map[k]["params_b"]))):
                size_map[k] = {**size_map[k], "params_b": r["params_b"]}

    rows = []
    for name in arena_names:
        hit = None
        for k in core_keys(name):
            if k in size_map:
                hit = size_map[k]
                break
        if hit:
            rows.append({"model_name_arena": name, **hit})
        else:
            rows.append({"model_name_arena": name, "params_b": np.nan, "open_weights": np.nan})
    return pd.DataFrame(rows)


def main():
    arena = pd.read_csv(ARENA_PATH)
    prices = pd.read_csv(PRICES_PATH)
    xwalk = pd.read_csv(XWALK_PATH)
    sizes = pd.read_csv(SIZES_PATH)

    arena["snapshot_date"] = pd.to_datetime(arena["snapshot_date"])
    prices["week_start"] = pd.to_datetime(prices["week_start"])

    by_id, id_index, can_index, core_index = build_price_lookups(prices)

    arena_models = sorted(arena["model_name"].unique())
    match_rows, unmatched = [], []
    for name in arena_models:
        # skip alias if target model_id absent (e.g. gpt-4.1-mini not in catalog)
        m = pick_match(name, by_id, id_index, can_index, core_index)
        if m:
            match_rows.append(m)
        else:
            unmatched.append(name)

    matches = pd.DataFrame(match_rows)
    freq = arena.groupby("model_name").size().rename("n_snapshots")
    unmatched_freq = (
        pd.DataFrame({"model_name_arena": unmatched})
        .merge(freq, left_on="model_name_arena", right_index=True, how="left")
        .sort_values("n_snapshots", ascending=False)
    )
    print(f"Matched {len(matches)} / {len(arena_models)} ({100*len(matches)/len(arena_models):.1f}%)")
    print("Top unmatched:")
    print(unmatched_freq.head(25).to_string(index=False))

    matches_out = matches[
        [
            "model_name_arena",
            "model_id_price",
            "provider",
            "model_name_canonical",
            "match_method",
            "match_confidence",
            "normalized_arena",
            "matched_key",
        ]
    ].copy()
    matches_out.to_csv(OUT / "arena_price_name_matches.csv", index=False)
    unmatched_freq.to_csv(OUT / "arena_unmatched_models.csv", index=False)

    # sanity: gpt-4.1 should map to gpt-4.1
    bad = matches_out[matches_out["model_name_arena"] == "gpt-4.1-2025-04-14"]
    print("gpt-4.1 match:", bad.to_string(index=False) if len(bad) else "MISSING")

    # Date align
    arena = arena.copy()
    arena["week_start"] = arena["snapshot_date"].map(monday_on_or_before)
    arena = arena.sort_values(["week_start", "snapshot_date"])
    arena = arena.groupby(["week_start", "model_name"], as_index=False).last()

    panel = arena.merge(
        matches_out[["model_name_arena", "model_id_price", "match_confidence"]],
        left_on="model_name",
        right_on="model_name_arena",
        how="inner",
    )

    pr = prices.rename(columns={"model_id": "model_id_price"})[
        [
            "week_start",
            "model_id_price",
            "provider",
            "input_usd_per_mtok",
            "output_usd_per_mtok",
            "blended_3_1_usd_per_mtok",
        ]
    ].copy()
    pr["prov_rank"] = pr["provider"].map(provider_rank)
    pr = pr.sort_values(["week_start", "model_id_price", "prov_rank"]).drop_duplicates(
        ["week_start", "model_id_price"], keep="first"
    )

    panel = panel.merge(pr, on=["week_start", "model_id_price"], how="inner")

    size_df = match_sizes(panel["model_name_arena"].unique().tolist(), sizes, xwalk)
    panel = panel.merge(size_df, on="model_name_arena", how="left")

    panel = panel[
        [
            "week_start",
            "model_name_arena",
            "model_id_price",
            "provider",
            "elo",
            "blended_3_1_usd_per_mtok",
            "input_usd_per_mtok",
            "output_usd_per_mtok",
            "params_b",
            "open_weights",
            "match_confidence",
        ]
    ].copy()
    panel = panel.dropna(subset=["elo", "blended_3_1_usd_per_mtok"])
    panel = panel.sort_values(["week_start", "elo"], ascending=[True, False]).reset_index(drop=True)

    # Pareto
    on_flags = np.zeros(len(panel), dtype=bool)
    for week, g in panel.groupby("week_start", sort=True):
        idx = g.index.to_numpy()
        on = is_pareto(g["elo"].to_numpy(float), g["blended_3_1_usd_per_mtok"].to_numpy(float))
        on_flags[idx] = on
    panel["on_frontier"] = on_flags

    panel_write = panel.copy()
    panel_write["week_start"] = panel_write["week_start"].dt.strftime("%Y-%m-%d")
    panel_write.to_csv(OUT / "arena_elo_price_weekly_panel.csv", index=False)
    panel_write.to_csv(OUT / "arena_elo_price_weekly_frontier.csv", index=False)

    # Same-elo cost (exclude non-positive prices from "achieving" set — free/zero list prices
    # still remain on the panel/frontier, but cost series needs a meaningful API cost)
    weeks_sorted = sorted(panel["week_start"].unique())
    models_per_week = panel.groupby("week_start").size()
    first_ge5 = models_per_week[models_per_week >= 5].index.min()
    target_anchors = [
        first_ge5,
        pd.Timestamp("2024-01-01"),
        pd.Timestamp("2024-07-01"),
        pd.Timestamp("2025-01-01"),
        pd.Timestamp("2025-07-01"),
        pd.Timestamp("2026-01-01"),
    ]
    anchors = []
    for t in target_anchors:
        if pd.isna(t):
            continue
        cand = [w for w in weeks_sorted if w <= t]
        if not cand:
            cand = [w for w in weeks_sorted if w >= t][:1]
        if not cand:
            continue
        w = cand[-1]
        fr = panel[(panel["week_start"] == w) & (panel["on_frontier"])]
        if fr.empty:
            for w2 in weeks_sorted:
                if w2 < w:
                    continue
                fr = panel[(panel["week_start"] == w2) & (panel["on_frontier"])]
                if not fr.empty:
                    w = w2
                    break
        if fr.empty:
            continue
        if w not in anchors:
            anchors.append(w)

    same_rows = []
    for t0 in anchors:
        fr0 = panel[(panel["week_start"] == t0) & (panel["on_frontier"])]
        # Q* from frontier using positive-price models when possible
        fr0_pos = fr0[fr0["blended_3_1_usd_per_mtok"] > 0]
        q_star = float((fr0_pos if len(fr0_pos) else fr0)["elo"].max())
        for t in weeks_sorted:
            if t < t0:
                continue
            g = panel[panel["week_start"] == t]
            qual = g[(g["elo"] >= q_star) & (g["blended_3_1_usd_per_mtok"] > 0)]
            if qual.empty:
                same_rows.append(
                    {
                        "anchor_week": t0.strftime("%Y-%m-%d"),
                        "anchor_max_elo": q_star,
                        "week_start": t.strftime("%Y-%m-%d"),
                        "min_blended_price_for_anchor_elo": np.nan,
                        "achieving_model": None,
                        "n_models_qualifying": 0,
                    }
                )
            else:
                i = qual["blended_3_1_usd_per_mtok"].idxmin()
                row = qual.loc[i]
                same_rows.append(
                    {
                        "anchor_week": t0.strftime("%Y-%m-%d"),
                        "anchor_max_elo": q_star,
                        "week_start": t.strftime("%Y-%m-%d"),
                        "min_blended_price_for_anchor_elo": float(row["blended_3_1_usd_per_mtok"]),
                        "achieving_model": row["model_name_arena"],
                        "n_models_qualifying": int(len(qual)),
                    }
                )
    same_df = pd.DataFrame(same_rows)
    same_df.to_csv(OUT / "same_elo_cost_over_time.csv", index=False)

    # Summary
    panel2 = panel.copy()
    panel2["year"] = panel2["week_start"].dt.year
    arena_y = arena.copy()
    arena_y["year"] = arena_y["week_start"].dt.year
    match_rate_by_year = {}
    for y, g in arena_y.groupby("year"):
        models_y = set(g["model_name"].unique())
        matched_y = models_y & set(matches_out["model_name_arena"])
        match_rate_by_year[str(int(y))] = {
            "arena_models": len(models_y),
            "matched_models": len(matched_y),
            "match_rate": round(len(matched_y) / len(models_y), 4) if models_y else 0,
            "panel_rows": int((panel2["year"] == y).sum()),
            "panel_unique_models": int(panel2.loc[panel2["year"] == y, "model_name_arena"].nunique()),
        }

    mpw = panel2.groupby("week_start").size()
    early_week = panel2["week_start"].min()
    late_week = panel2["week_start"].max()
    early_f = panel2[(panel2["week_start"] == early_week) & (panel2["on_frontier"])].sort_values("elo", ascending=False)
    late_f = panel2[(panel2["week_start"] == late_week) & (panel2["on_frontier"])].sort_values("elo", ascending=False)

    def frontier_examples(df):
        return [
            {
                "model": r["model_name_arena"],
                "elo": round(float(r["elo"]), 2),
                "blended": float(r["blended_3_1_usd_per_mtok"]),
                "provider": r["provider"],
            }
            for _, r in df.head(10).iterrows()
        ]

    decline = {}
    for aw, g in same_df.groupby("anchor_week"):
        g2 = g.dropna(subset=["min_blended_price_for_anchor_elo"]).sort_values("week_start")
        if len(g2) < 2:
            decline[aw] = {"has_series": False}
            continue
        first_p = float(g2.iloc[0]["min_blended_price_for_anchor_elo"])
        last_p = float(g2.iloc[-1]["min_blended_price_for_anchor_elo"])
        decline[aw] = {
            "has_series": True,
            "anchor_max_elo": float(g2.iloc[0]["anchor_max_elo"]),
            "start_price": first_p,
            "end_price": last_p,
            "start_week": g2.iloc[0]["week_start"],
            "end_week": g2.iloc[-1]["week_start"],
            "declined": bool(last_p < first_p),
            "pct_change": round(100 * (last_p - first_p) / first_p, 2) if first_p else None,
        }

    # models/week series for README
    mpw_by_year = {
        str(int(y)): {
            "median": float(s.median()),
            "mean": round(float(s.mean()), 2),
            "min": int(s.min()),
            "max": int(s.max()),
            "weeks": int(len(s)),
        }
        for y, s in mpw.groupby(mpw.index.year)
    }

    summary = {
        "generated": "2026-09-11",
        "arena_models_total": int(len(arena_models)),
        "matched_models": int(len(matches)),
        "match_rate": round(len(matches) / len(arena_models), 4),
        "unmatched_models": int(len(unmatched)),
        "panel_rows": int(len(panel2)),
        "weeks_covered": int(panel2["week_start"].nunique()),
        "week_start_min": early_week.strftime("%Y-%m-%d"),
        "week_start_max": late_week.strftime("%Y-%m-%d"),
        "median_models_per_week": float(mpw.median()),
        "mean_models_per_week": round(float(mpw.mean()), 2),
        "models_per_week_by_year": mpw_by_year,
        "frontier_rows": int(panel2["on_frontier"].sum()),
        "median_frontier_models_per_week": float(
            panel2[panel2["on_frontier"]].groupby("week_start").size().median()
        ),
        "match_rate_by_year": match_rate_by_year,
        "example_frontier_early_week": early_week.strftime("%Y-%m-%d"),
        "example_frontier_early": frontier_examples(early_f),
        "example_frontier_latest_week": late_week.strftime("%Y-%m-%d"),
        "example_frontier_latest": frontier_examples(late_f),
        "same_elo_cost_decline": decline,
        "anchors": [a.strftime("%Y-%m-%d") for a in anchors],
        "top_unmatched": unmatched_freq.head(25).to_dict(orient="records"),
        "zero_price_panel_rows": int((panel2["blended_3_1_usd_per_mtok"] <= 0).sum()),
        "note_span": (
            "Arena weekly file only starts listing commercial GPT/Claude once they "
            "appear on the leaderboard (~2023-12); earlier Arena weeks are mostly "
            "open models without API list prices in our price panel."
        ),
    }
    with open(OUT / "_summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)

    # README
    lines = []
    lines.append("# Arena Elo × blended price weekly frontiers\n")
    lines.append("Built **2026-09-11** from Arena weekly Elo snapshots + Monday blended API prices.\n")
    lines.append("## Outputs\n")
    lines.append("| File | Description |")
    lines.append("|------|-------------|")
    lines.append("| `arena_price_name_matches.csv` | Arena ↔ price matches (`match_method`, `match_confidence`) |")
    lines.append("| `arena_unmatched_models.csv` | Frequent Arena models with no high-precision price match |")
    lines.append("| `arena_elo_price_weekly_panel.csv` | Weekly panel (Elo + blended price), matched rows only |")
    lines.append("| `arena_elo_price_weekly_frontier.csv` | Same panel + `on_frontier` (max Elo, min blended $/MTok) |")
    lines.append("| `same_elo_cost_over_time.csv` | Min blended price to hit each anchor week's max frontier Elo |")
    lines.append("| `_summary.json` | Coverage / example frontier / decline stats |")
    lines.append("| `build_frontiers.py` | Reproducible builder |\n")
    lines.append("## Name matching\n")
    lines.append(
        "Normalize aggressively (lowercase, hyphenate, strip org prefixes, strip dated "
        "suffixes like `-20241022` / `-2024-05-13`, strip thinking/high/preview variants). "
        "Prefer exact `model_id` hits; manual aliases for Arena naming quirks. Canonical-name "
        "index is used only when unique (Ronin sometimes labels historical `gpt-4` as "
        "`GPT-4.1`). First-party providers preferred over hosters.\n"
    )
    lines.append(
        f"**Overall:** {summary['matched_models']}/{summary['arena_models_total']} Arena models "
        f"({100*summary['match_rate']:.1f}%). Panel keeps only weeks with both Elo and price.\n"
    )
    lines.append("### Match rates by year (Arena models appearing that year)\n")
    lines.append("| Year | Arena models | Matched | Rate | Panel rows | Median models/week |")
    lines.append("|------|-------------|---------|------|------------|--------------------|")
    for y in sorted(match_rate_by_year.keys()):
        m = match_rate_by_year[y]
        mp = mpw_by_year.get(y, {})
        lines.append(
            f"| {y} | {m['arena_models']} | {m['matched_models']} | {100*m['match_rate']:.1f}% | "
            f"{m['panel_rows']} | {mp.get('median', '—')} |"
        )
    lines.append("\n## Date alignment\n")
    lines.append(
        "Map each Arena `snapshot_date` to the Monday on or before it. Join to "
        "`weekly_blended_prices.week_start`. If multiple snapshots collapse to one Monday, "
        "keep the latest snapshot that week per model.\n"
    )
    lines.append("## Pareto definition\n")
    lines.append(
        "Per week, a model is on the frontier iff no other same-week model has Elo ≥ it "
        "AND blended price ≤ it with at least one strict inequality "
        "(maximize Elo, minimize 3:1 blended $/MTok).\n"
    )
    lines.append("## Coverage\n")
    lines.append(
        f"- Panel weeks: **{summary['week_start_min']} → {summary['week_start_max']}** "
        f"({summary['weeks_covered']} weeks)\n"
        f"- Panel rows: **{summary['panel_rows']}**\n"
        f"- Median models/week: **{summary['median_models_per_week']}**\n"
        f"- Median frontier size/week: **{summary['median_frontier_models_per_week']}**\n"
    )
    lines.append(f"- {summary['note_span']}\n")
    lines.append("## Caveats\n")
    lines.append(
        "1. **Elo drift:** Arena Elo is relative; re-estimation and the Bradley-Terry transition "
        "(~2024-01) mean cross-year levels are not a pure absolute IQ scale.\n"
        "2. **Incomplete price coverage for open / mid-tier models:** Early Arena is dominated by "
        "Vicuna/LLaMA/chatGLM/etc. with no commercial API list price → excluded from the panel. "
        "Many mid-tier / hosted-only open models remain unmatched (`arena_unmatched_models.csv`).\n"
        "3. **High-precision bias:** Ambiguous preview→GA links are under-matched rather than guessed.\n"
        "4. **Thinking / high-effort Arena variants** often share the base API price (lower confidence).\n"
        "5. **Blended price** uses a fixed 3:1 input:output mix — not workload-specific.\n"
        "6. **Zero list prices** (e.g. promotional free tiers) can appear on the Pareto frontier; "
        "the same-Elo cost series requires **positive** blended price to avoid $0 artifacts.\n"
        "7. Prices and Elo are never invented — both must be observed for a row to appear.\n"
    )
    lines.append("## Same-Elo cost series\n")
    lines.append(
        "Anchors (frontier-defined weeks near requested calendar points): "
        + ", ".join(a.strftime("%Y-%m-%d") for a in anchors)
        + ".\n\n"
        "For each anchor t0, Q* = max Elo on that week's frontier (positive-price models preferred). "
        "For later weeks t ≥ t0, cost = min blended price among models with Elo ≥ Q* and price > 0.\n"
    )
    lines.append("### Does same-Elo cost decline?\n")
    for aw, d in decline.items():
        if not d.get("has_series"):
            lines.append(f"- Anchor {aw}: insufficient series")
            continue
        arrow = "YES (decline)" if d["declined"] else "NO (up/flat)"
        lines.append(
            f"- Anchor {aw} (Q*={d['anchor_max_elo']:.1f}): "
            f"{d['start_price']:.4f} → {d['end_price']:.4f} $/MTok "
            f"({d['pct_change']}%) from {d['start_week']} to {d['end_week']} — **{arrow}**"
        )
    lines.append("\n## Example frontier models\n")
    lines.append(f"### Early week ({summary['example_frontier_early_week']})\n")
    for e in summary["example_frontier_early"]:
        lines.append(f"- {e['model']}: Elo {e['elo']}, ${e['blended']}/MTok ({e['provider']})")
    lines.append(f"\n### Latest week ({summary['example_frontier_latest_week']})\n")
    for e in summary["example_frontier_latest"]:
        lines.append(f"- {e['model']}: Elo {e['elo']}, ${e['blended']}/MTok ({e['provider']})")
    lines.append("")
    (OUT / "README.md").write_text("\n".join(lines))

    print(json.dumps({
        "match_rate": summary["match_rate"],
        "weeks_covered": summary["weeks_covered"],
        "median_models_per_week": summary["median_models_per_week"],
        "span": [summary["week_start_min"], summary["week_start_max"]],
        "panel_rows": summary["panel_rows"],
        "decline": {k: (v.get("declined"), v.get("pct_change")) for k, v in decline.items()},
    }, indent=2))
    print("Early:", summary["example_frontier_early"][:5])
    print("Latest:", summary["example_frontier_latest"][:5])


if __name__ == "__main__":
    main()
