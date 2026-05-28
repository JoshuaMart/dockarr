class Module:
    name = ""
    depends = ()

    def is_done(self, ctx):
        raise NotImplementedError

    def run(self, ctx):
        raise NotImplementedError


def load_modules():
    """Return every available module, in declaration order. Add new modules
    here as integrations are built."""
    from ..modules import (
        arr_setup,
        kavita,
        profilarr,
        prowlarr_apps,
        qbittorrent,
        qbittorrent_setup,
        qui,
        servarr,
    )

    return [
        qbittorrent.MODULE,
        qbittorrent_setup.MODULE,
        qui.MODULE,
        servarr.RADARR,
        servarr.SONARR,
        servarr.PROWLARR,
        kavita.MODULE,
        profilarr.MODULE,
        arr_setup.RADARR_SETUP,
        arr_setup.SONARR_SETUP,
        prowlarr_apps.MODULE,
    ]


def resolve_order(modules):
    """Topologically sort the given modules by their `depends`."""
    by_name = {m.name: m for m in modules}
    ordered = []
    seen = set()

    def visit(module):
        if module.name in seen:
            return
        seen.add(module.name)
        for dep in module.depends:
            if dep in by_name:
                visit(by_name[dep])
        ordered.append(module)

    for module in modules:
        visit(module)
    return ordered
