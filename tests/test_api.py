from .conftest import CSV_NO_TIME, GOOD_CSV


def upload(client, content=GOOD_CSV, name="run.csv"):
    return client.post("/api/v1/datasets", files={"file": (name, content, "text/csv")})


def test_upload_ok_returns_201_and_hides_internal_fields(client, storage):
    response = upload(client)
    assert response.status_code == 201
    body = response.json()
    assert body["rows"] == 3
    assert "file_key" not in body and "owner_oid" not in body
    assert len(storage.files) == 1


def test_upload_without_time_column_is_400(client):
    assert upload(client, CSV_NO_TIME).status_code == 400


def test_upload_over_the_limit_is_413(client):
    big = b"time,x\n" + b"1,1\n" * (400_000)  # about 1.6 MB, limit in tests is 1 MB
    assert upload(client, big).status_code == 413


def test_upload_without_a_file_is_422(client):
    assert client.post("/api/v1/datasets").status_code == 422


def test_uploads_show_up_in_the_list(client):
    upload(client, name="a.csv")
    upload(client, name="b.csv")
    assert [d["name"] for d in client.get("/api/v1/datasets").json()] == ["a.csv", "b.csv"]
