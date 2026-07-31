import json
from pathlib import Path
for p in [".tmp_apps.json", ".tmp_infra.json"]:
    d=json.loads(Path(r"C:\salkim_ai", p).read_text(encoding="utf-8"))
    print("===", p)
    print([i.get("name") for i in d] if isinstance(d, list) else str(d)[:400])
tree=json.loads(Path(r"C:\salkim_ai\.tmp_tree.json").read_text(encoding="utf-8"))
paths=[t["path"] for t in tree.get("tree", []) if "predict" in t["path"].lower() or t["path"].endswith("main.py") or "fastapi" in t["path"].lower() or "/api/" in t["path"].lower() or t["path"].startswith("apps/")]
print("=== matches")
for p in paths[:120]:
    print(p)
