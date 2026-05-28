import sys

from . import secrets as secretsmod


def ensure_language(store):
    """Ask once whether to localize the stack. 'en' (default) changes nothing;
    'fr' configures Jellyfin and Seerr in French."""
    if store.language:
        return

    if not sys.stdin.isatty():
        store.set_language("en")
        print("[bootstrap] non-interactive run: language=en")
        return

    print("\nLanguage / Langue:")
    print("  [1] English (default)")
    print("  [2] Français")
    choice = ""
    while choice not in ("1", "2"):
        choice = input("Choice / Choix [1/2] : ").strip() or "1"
    store.set_language("fr" if choice == "2" else "en")
    print(f"  -> {'Français' if choice == '2' else 'English'}\n")


def ensure_policy(store):
    """Establish the credential policy once. Interactive on first run;
    falls back to safe defaults when no TTY is attached (automation)."""
    if store.policy:
        return

    if not sys.stdin.isatty():
        username = secretsmod.gen_username()
        store.set_policy(username, "per_service")
        print(f"[bootstrap] non-interactive run: username='{username}', "
              "random password per service")
        return

    print("\n=== Dockarr bootstrap — first run ===")
    raw = input("Service username? [empty = random a-z(10)] : ").strip()
    username = raw or secretsmod.gen_username()
    print(f"  -> username: {username}")

    print("Password mode:")
    print("  [1] same random password everywhere")
    print("  [2] a different random password per service")
    choice = ""
    while choice not in ("1", "2"):
        choice = input("Choice [1/2] : ").strip()

    if choice == "1":
        store.set_policy(username, "shared", secretsmod.gen_password())
        print("  -> shared random password generated")
    else:
        store.set_policy(username, "per_service")
        print("  -> a random password will be generated per service")

    print(f"Credentials are stored in {store.path}\n")
