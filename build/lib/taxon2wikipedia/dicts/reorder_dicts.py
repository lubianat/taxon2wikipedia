import json
from pathlib import Path

HERE = Path(__file__).parent.resolve()
for path in HERE.glob("*.json"):
    dict_now = json.loads(path.read_text())
    path.write_text(json.dumps(dict_now, indent=4, sort_keys=True, ensure_ascii=False))
