import json
from pathlib import Path

for name in [".tmp_repos_ees.json", ".tmp_repos_arif.json"]:
    path = Path(r"C:\salkim_ai") / name
    print("===", name)
    if not path.exists():
        print("missing")
        continue
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        for repo in data:
            print(repo["name"], "-", repo.get("description"))
    else:
        print(str(data)[:500])
