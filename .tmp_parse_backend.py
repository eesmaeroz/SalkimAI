import json
from pathlib import Path
tree=json.loads(Path(r"C:\salkim_ai\.tmp_backend_tree.json").read_text(encoding="utf-8"))
paths=[t["path"] for t in tree.get("tree",[])]
print("count", len(paths))
for p in paths:
    if any(k in p.lower() for k in ["predict", "router", "api", "main.py", "harvest", "weather", "fastapi", "app/"]):
        print(p)
