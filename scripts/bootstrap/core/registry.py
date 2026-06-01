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
        jellyfin,
        kavita,
        profilarr,
        profilarr_fr,
        profilarr_targets,
        prowlarr_apps,
        qbittorrent,
        qbittorrent_setup,
        qui,
        qui_arr,
        qui_indexers,
        seerr,
        servarr,
        vpn,
    )

    return [
        vpn.MODULE,
        qbittorrent.MODULE,
        qbittorrent_setup.MODULE,
        qui.MODULE,
        qui_arr.MODULE,
        qui_indexers.MODULE,
        servarr.RADARR,
        servarr.SONARR,
        servarr.PROWLARR,
        kavita.MODULE,
        profilarr.MODULE,
        jellyfin.MODULE,
        arr_setup.RADARR_SETUP,
        arr_setup.SONARR_SETUP,
        prowlarr_apps.MODULE,
        profilarr_targets.MODULE,
        profilarr_fr.MODULE,
        seerr.MODULE,
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
