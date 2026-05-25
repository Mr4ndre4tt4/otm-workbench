import argparse

from otm_workbench.database import session_scope
from otm_workbench.platform.services import bootstrap_admin


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    bootstrap = subparsers.add_parser("bootstrap-admin")
    bootstrap.add_argument("--email", required=True)
    bootstrap.add_argument("--password", required=True)
    qa_user = subparsers.add_parser("bootstrap-qa-user")
    qa_user.add_argument("--email", default="demo@example.test")
    qa_user.add_argument("--password", default="DemoPass123!")
    qa_user.add_argument("--admin", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args()

    if args.command == "bootstrap-admin":
        with session_scope() as db:
            user = bootstrap_admin(db, email=args.email, password=args.password)
            email = user.email
        print(f"Admin user ready: {email}")
    elif args.command == "bootstrap-qa-user":
        with session_scope() as db:
            user = bootstrap_admin(db, email=args.email, password=args.password)
            user.is_admin = bool(args.admin)
            db.commit()
            email = user.email
            is_admin = user.is_admin
        print(f"QA browser user ready: {email}")
        print(f"Admin privileges: {str(is_admin).lower()}")


if __name__ == "__main__":
    main()
