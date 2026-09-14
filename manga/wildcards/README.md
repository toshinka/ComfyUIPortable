# Manga-owned wildcards

This directory is the default Dynamic Prompt root for TEGAKI Manga basic Generate.
It is intentionally independent from `ComfyUI/wildcards` and any Forge/ReForge
installation. Keep collections small, project-authored, and free of copied
third-party wildcard packs. A local shared collection may be selected through
`TEGAKI_MANGA_WILDCARDS_DIR`.

Supported basic syntax is provided by the installed `dynamicprompts` package:
`__name__`, `{a|b}`, nested forms, weighted choices, and escaped braces (`\\{` /
`\\}`). Missing or malformed syntax fails closed before backend submission.

Expansion uses two independent deterministic domains derived as
`SHA-256("tegaki-manga-play4:" + domain + ":" + effective_seed)` (the first
8 bytes as an unsigned integer), with `domain` set to `positive` or `negative`.
