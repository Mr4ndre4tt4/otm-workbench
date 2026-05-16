import argparse

from otm_workbench.database import session_scope
from otm_workbench.platform.services import bootstrap_admin


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    bootstrap = subparsers.add_parser("bootstrap-admin")
    bootstrap.add_argument("--email", required=True)
    bootstrap.add_argument("--password", required=True)
    args = parser.parse_args()

    if args.command == "bootstrap-admin":
        with session_scope() as db:
            user = bootstrap_admin(db, email=args.email, password=args.password)
        print(f"Admin user ready: {user.email}")


if __name__ == "__main__":
    main()
