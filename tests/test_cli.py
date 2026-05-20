import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4


def test_bootstrap_admin_cli_prints_without_detached_instance_error():
    database_path = Path("var") / f"cli-{uuid4()}.db"
    env = {
        **os.environ,
        "OTM_DATABASE_URL": f"sqlite:///{database_path}",
        "PYTHONPATH": "src",
    }
    create_schema = subprocess.run(
        [
            sys.executable,
            "-c",
            "import otm_workbench.models; "
            "from otm_workbench.database import Base, engine; "
            "Base.metadata.create_all(bind=engine)",
        ],
        check=False,
        env=env,
        capture_output=True,
        text=True,
    )
    assert create_schema.returncode == 0, create_schema.stderr

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "otm_workbench.cli",
            "bootstrap-admin",
            "--email",
            "synthetic.user@example.test",
            "--password",
            "SyntheticPass123!",
        ],
        check=False,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "Admin user ready: synthetic.user@example.test" in result.stdout
