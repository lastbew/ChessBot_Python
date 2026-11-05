# Agent Skills

This folder holds **Agent Skills**: small, self-contained instruction packs an
AI agent can discover and load when a task matches them.

## How a skill is laid out
Each skill is its own folder:

```
.claude/skills/
  <skill-name>/
    SKILL.md            # required: metadata + instructions
    scripts/            # optional: helper scripts the skill can run
      do_something.ps1
    resources/          # optional: templates, data, examples
```

### SKILL.md format
`SKILL.md` starts with YAML front-matter, then plain Markdown:

```markdown
---
name: my-skill
description: One specific sentence about what this does and WHEN to use it.
---

# My Skill

## When to use this
...

## Steps
1. ...

## Helper scripts
- `scripts/do_something.ps1` — what it does
```

Rules of thumb:
- `name` is short, lowercase, hyphenated (max ~64 chars).
- `description` is **specific about when to use it** — that's what the agent
  reads first to decide whether to load the full skill.
- Keep `SKILL.md` focused; put big details in `scripts/` or `resources/`.

## Add a new skill
1. Copy `.claude/skills/_template/` to `.claude/skills/<your-skill>/`.
2. Fill in the front-matter and write the steps.
3. Drop any helper scripts under `scripts/`.

## Included skills
- **chess-bot** — how to run, test, and maintain the ChessKiller bot in this repo.

> Compatibility: Claude-style agents read `.claude/skills/`. Some other agents
> look in a plain `skills/` folder at the repo root — if yours does, copy this
> folder there (or rename it) and the same `SKILL.md` files work.
