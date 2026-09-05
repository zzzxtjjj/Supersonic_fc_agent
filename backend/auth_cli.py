import argparse
import getpass
import secrets

from backend.auth import hash_password


def main() -> None:
    parser = argparse.ArgumentParser(description="Supersonic FC admin auth helper")
    parser.add_argument("command", choices=["hash-password", "generate-secret"])
    args = parser.parse_args()

    if args.command == "generate-secret":
        print(secrets.token_urlsafe(48))
        return

    password = getpass.getpass("Admin password: ")
    confirmation = getpass.getpass("Confirm password: ")
    if password != confirmation:
        raise SystemExit("Passwords do not match.")
    print(hash_password(password))


if __name__ == "__main__":
    main()
