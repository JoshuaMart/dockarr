import sys

from .core import prompts
from .core.context import build_context
from .core.registry import load_modules, resolve_order


def main(argv):
    flags = [a for a in argv[1:] if a.startswith("-")]
    positionals = [a for a in argv[1:] if not a.startswith("-")]
    force = "--force" in flags
    only = positionals[0] if positionals else None

    ctx = build_context()
    all_modules = load_modules()

    if only:
        selected = [m for m in all_modules if m.name == only]
        if not selected:
            names = ", ".join(m.name for m in all_modules)
            ctx.log.error(f"Unknown module '{only}'. Available: {names}")
            return 1
    else:
        selected = all_modules

    order = resolve_order(selected)
    prompts.ensure_language(ctx.secrets)
    prompts.ensure_policy(ctx.secrets)
    prompts.ensure_profilarr_fr(ctx.secrets)

    for module in order:
        try:
            if not force and module.is_done(ctx):
                ctx.log.info(f"[{module.name}] already configured — skipping")
                continue
            ctx.log.info(f"[{module.name}] provisioning…")
            module.run(ctx)
            ctx.log.info(f"[{module.name}] done")
        except Exception as exc:  # noqa: BLE001 — surface a clean message per module
            ctx.log.error(f"[{module.name}] FAILED: {exc}")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
