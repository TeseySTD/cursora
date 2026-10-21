"""Write the FastAPI OpenAPI schema to packages/api-client/openapi.json.

Keys are sorted and the file ends with a newline so the output is byte-stable
and `pnpm api:check` can detect drift with a plain git diff.

Usage: python apps/api/scripts/export_openapi.py [output_path]
"""

import json
import sys
from pathlib import Path

from cursora_api.core.config import Settings
from cursora_api.main import create_app

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT = REPO_ROOT / "packages" / "api-client" / "openapi.json"


def main() -> None:
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUTPUT
    # Explicit settings: the schema must not depend on the developer's .env.
    app = create_app(Settings(_env_file=None, log_level="WARNING"))
    spec = json.dumps(app.openapi(), indent=2, sort_keys=True, ensure_ascii=False)
    output.write_text(spec + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {output.relative_to(REPO_ROOT).as_posix()}")


if __name__ == "__main__":
    main()
