import json
from pathlib import Path
repo=json.loads(Path(r"C:\salkim_ai\.tmp_repo.json").read_text(encoding="utf-8"))
print("default", repo.get("default_branch"))
branches=json.loads(Path(r"C:\salkim_ai\.tmp_branches.json").read_text(encoding="utf-8"))
print([b["name"] for b in branches])
