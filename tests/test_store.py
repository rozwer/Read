from local_readable.models import JobRecord
from local_readable.store import JobStore


def test_store_round_trip(tmp_path):
    store = JobStore(tmp_path)
    record = JobRecord(id="a" * 32, filename="paper.pdf", model="qwen2.5:7b")
    store.create(record)
    updated = store.update(record.id, state="running", progress=20)
    assert updated.state == "running"
    assert store.get(record.id).progress == 20

