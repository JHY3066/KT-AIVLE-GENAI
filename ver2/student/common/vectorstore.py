# student/common/vectorstore.py
from pathlib import Path
from student.day2.impl.store import FaissStore  # 기존 구현 재사용

class VSConfig:
    def __init__(self, index_dir: str):
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)

def get_store(index_dir: str) -> FaissStore:
    cfg = VSConfig(index_dir)
    return FaissStore(index_path=cfg.index_dir / "faiss.index",
                      meta_path=cfg.index_dir / "docs.jsonl")
