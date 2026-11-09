from app.db.models import Dataset
from app.db.session import new_session
from app.repositories.datasets import DatasetRepository
from app.repositories.jobs import JobRepository
from app.services.jobs import JobService

from .conftest import CSV_NO_TIME, CSV_WITH_GAP, GOOD_CSV, make_token


def upload(client, headers, content=GOOD_CSV, name="run.csv"):
    return client.post("/api/v1/datasets", headers=headers, files={"file": (name, content, "text/csv")})


# ---- boundaries: validation and uploads ----
def test_upload_ok_returns_201_and_hides_internal_fields(client, lotte, storage):
    response = upload(client, lotte)
    assert response.status_code == 201
    body = response.json()
    assert body["rows"] == 3
    assert "file_key" not in body and "owner_oid" not in body
    assert len(storage.files) == 1


def test_upload_without_time_column_is_400(client, lotte):
    assert upload(client, lotte, CSV_NO_TIME).status_code == 400


def test_upload_over_the_limit_is_413(client, lotte):
    big = b"time,x\n" + b"1,1\n" * (400_000)  # about 1.6 MB, limit in tests is 1 MB
    assert upload(client, lotte, big).status_code == 413


def test_job_with_a_bad_body_is_422(client, lotte):
    response = client.post("/api/v1/jobs", headers=lotte, json={"dataset_id": "abc"})
    assert response.status_code == 422


# ---- jobs: jobs ----
def test_job_flow_202_then_409_then_200(client, lotte, storage):
    dataset_id = upload(client, lotte, CSV_WITH_GAP).json()["id"]
    job = client.post("/api/v1/jobs", headers=lotte, json={"dataset_id": dataset_id})
    assert job.status_code == 202
    job_id = job.json()["id"]

    assert client.get(f"/api/v1/jobs/{job_id}/report", headers=lotte).status_code == 409  # the 409 trap

    with new_session(client.app.state.engine) as session:  # play the worker once
        service = JobService(JobRepository(session), DatasetRepository(session), storage)
        assert service.run_next() is True
        assert service.run_next() is False  # nothing left

    assert client.get(f"/api/v1/jobs/{job_id}", headers=lotte).json()["status"] == "done"
    report = client.get(f"/api/v1/jobs/{job_id}/report", headers=lotte)
    assert report.status_code == 200
    assert report.json()["quality_score"] == 100 - 1 - 5 * 2


def test_worker_marks_a_broken_job_failed_and_survives(client, lotte, storage):
    dataset_id = upload(client, lotte).json()["id"]
    job_id = client.post("/api/v1/jobs", headers=lotte, json={"dataset_id": dataset_id}).json()["id"]
    storage.files.clear()  # the file vanished: the job must fail, not crash the worker
    with new_session(client.app.state.engine) as session:
        JobService(JobRepository(session), DatasetRepository(session), storage).run_next()
    assert client.get(f"/api/v1/jobs/{job_id}", headers=lotte).json()["status"] == "failed"


# ---- security: security ----
def test_no_token_is_401(client):
    assert client.get("/api/v1/me").status_code == 401


def test_garbage_token_is_401(client):
    assert client.get("/api/v1/me", headers={"Authorization": "Bearer abc.def.ghi"}).status_code == 401


def test_expired_token_is_401(client, private_key):
    token = make_token(private_key, exp_in=-10)
    assert client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_token_for_another_audience_is_401(client, private_key):
    token = make_token(private_key, aud="some-other-api")
    assert client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_token_from_another_issuer_is_401(client, private_key):
    token = make_token(private_key, iss="https://evil.example/v2.0")
    assert client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_token_signed_with_another_key_is_401(client):
    from cryptography.hazmat.primitives.asymmetric import rsa

    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    token = make_token(other_key)
    assert client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_me_returns_the_roles_from_the_token(client, pieter):
    assert client.get("/api/v1/me", headers=pieter).json()["roles"] == ["Viewer"]


def test_viewer_may_read_but_not_upload_403(client, lotte, pieter):
    assert upload(client, pieter).status_code == 403
    upload(client, lotte)
    assert client.get("/api/v1/datasets", headers=pieter).status_code == 200


def test_delete_own_only(client, private_key, lotte):
    dataset_id = upload(client, lotte).json()["id"]
    other = {"Authorization": f"Bearer {make_token(private_key, oid='oid-someone-else')}"}
    assert (
        client.delete(f"/api/v1/datasets/{dataset_id}", headers=other).status_code == 404
    )  # private: hidden
    admin = {"Authorization": f"Bearer {make_token(private_key, roles=('Admin',), oid='oid-admin')}"}
    assert client.delete(f"/api/v1/datasets/{dataset_id}", headers=admin).status_code == 204


def test_dataset_ids_are_not_filenames(client, lotte, storage):
    upload(client, lotte, name="../../etc/passwd")
    assert all(key.endswith(".csv") and "/" not in key for key in storage.files)
    assert Dataset  # imported so the model is registered


# ---- ownership: who may touch what ----
def headers_for(private_key, oid, roles):
    return {"Authorization": f"Bearer {make_token(private_key, oid=oid, roles=roles)}"}


def start_job(client, headers, dataset_id):
    return client.post("/api/v1/jobs", headers=headers, json={"dataset_id": dataset_id})


def test_delete_a_missing_dataset_is_404(client, lotte):
    assert client.delete("/api/v1/datasets/999", headers=lotte).status_code == 404


def test_viewer_may_not_delete_a_dataset_403(client, lotte, pieter):
    dataset_id = upload(client, lotte).json()["id"]
    assert client.delete(f"/api/v1/datasets/{dataset_id}", headers=pieter).status_code == 403


def test_owner_may_delete_their_own_dataset(client, lotte):
    dataset_id = upload(client, lotte).json()["id"]
    assert client.delete(f"/api/v1/datasets/{dataset_id}", headers=lotte).status_code == 204


def test_job_is_visible_to_its_owner_and_to_an_admin(client, private_key, lotte):
    dataset_id = upload(client, lotte).json()["id"]
    job_id = start_job(client, lotte, dataset_id).json()["id"]
    admin = headers_for(private_key, "oid-admin", ("Admin",))
    assert client.get(f"/api/v1/jobs/{job_id}", headers=lotte).status_code == 200
    assert client.get(f"/api/v1/jobs/{job_id}", headers=admin).status_code == 200


def test_someone_elses_job_and_report_are_404_like_a_missing_one(client, private_key, lotte, pieter):
    dataset_id = upload(client, lotte).json()["id"]
    job_id = start_job(client, lotte, dataset_id).json()["id"]
    other_researcher = headers_for(private_key, "oid-other", ("Researcher",))
    for headers in (pieter, other_researcher):
        for suffix in ("", "/report"):
            real = client.get(f"/api/v1/jobs/{job_id}{suffix}", headers=headers)
            missing = client.get(f"/api/v1/jobs/9999{suffix}", headers=headers)
            assert real.status_code == missing.status_code == 404
            assert real.json() == missing.json()


def test_viewer_may_not_start_a_job_403(client, lotte, pieter):
    dataset_id = upload(client, lotte).json()["id"]
    assert start_job(client, pieter, dataset_id).status_code == 403


def test_start_a_job_on_a_missing_dataset_is_404(client, lotte):
    assert start_job(client, lotte, 999).status_code == 404


def test_no_token_cannot_read_a_job_401(client):
    assert client.get("/api/v1/jobs/1").status_code == 401


# ---- visibility: private and public ----
def upload_public(client, headers, content=GOOD_CSV):
    response = client.post(
        "/api/v1/datasets",
        headers=headers,
        data={"visibility": "public"},
        files={"file": ("run.csv", content, "text/csv")},
    )
    assert response.status_code == 201
    return response.json()


def ids(response):
    return [d["id"] for d in response.json()]


def test_upload_is_private_by_default(client, lotte):
    assert upload(client, lotte).json()["visibility"] == "private"


def test_upload_can_be_public(client, lotte):
    assert upload_public(client, lotte)["visibility"] == "public"


def test_an_unknown_visibility_is_422(client, lotte):
    response = client.post(
        "/api/v1/datasets",
        headers=lotte,
        data={"visibility": "team"},
        files={"file": ("run.csv", GOOD_CSV, "text/csv")},
    )
    assert response.status_code == 422


def test_list_shows_own_and_public_datasets_and_hides_other_private_ones(client, private_key, lotte, pieter):
    private_id = upload(client, lotte).json()["id"]
    public_id = upload_public(client, lotte)["id"]
    other = headers_for(private_key, "oid-other", ("Researcher",))
    admin = headers_for(private_key, "oid-admin", ("Admin",))
    assert ids(client.get("/api/v1/datasets", headers=lotte)) == [private_id, public_id]
    assert ids(client.get("/api/v1/datasets", headers=other)) == [public_id]
    assert ids(client.get("/api/v1/datasets", headers=pieter)) == [public_id]  # a Viewer reads public ones
    assert ids(client.get("/api/v1/datasets", headers=admin)) == [private_id, public_id]


def test_anyone_may_start_a_job_on_a_public_dataset_and_read_it(client, private_key, lotte):
    dataset_id = upload_public(client, lotte)["id"]
    other = headers_for(private_key, "oid-other", ("Researcher",))
    job_id = start_job(client, other, dataset_id).json()["id"]
    assert client.get(f"/api/v1/jobs/{job_id}", headers=other).status_code == 200
    assert (
        client.get(f"/api/v1/jobs/{job_id}", headers=lotte).status_code == 200
    )  # public: the owner reads it too


def test_starting_a_job_on_someone_elses_private_dataset_is_404(client, private_key, lotte):
    dataset_id = upload(client, lotte).json()["id"]
    other = headers_for(private_key, "oid-other", ("Researcher",))
    assert start_job(client, other, dataset_id).status_code == 404


def test_jobs_on_a_public_dataset_are_readable_by_others_until_it_goes_private(
    client, private_key, lotte, pieter
):
    dataset_id = upload_public(client, lotte)["id"]
    job_id = start_job(client, lotte, dataset_id).json()["id"]
    assert client.get(f"/api/v1/jobs/{job_id}", headers=pieter).status_code == 200
    client.patch(f"/api/v1/datasets/{dataset_id}", headers=lotte, json={"visibility": "private"})
    assert client.get(f"/api/v1/jobs/{job_id}", headers=pieter).status_code == 404


def test_owner_may_change_visibility(client, lotte):
    dataset_id = upload(client, lotte).json()["id"]
    response = client.patch(f"/api/v1/datasets/{dataset_id}", headers=lotte, json={"visibility": "public"})
    assert response.status_code == 200
    assert response.json()["visibility"] == "public"


def test_admin_may_change_visibility_of_a_private_dataset(client, private_key, lotte):
    dataset_id = upload(client, lotte).json()["id"]
    admin = headers_for(private_key, "oid-admin", ("Admin",))
    response = client.patch(f"/api/v1/datasets/{dataset_id}", headers=admin, json={"visibility": "public"})
    assert response.status_code == 200


def test_a_stranger_may_not_change_or_delete_a_public_dataset_403(client, private_key, lotte):
    dataset_id = upload_public(client, lotte)["id"]
    other = headers_for(private_key, "oid-other", ("Researcher",))
    assert (
        client.patch(
            f"/api/v1/datasets/{dataset_id}", headers=other, json={"visibility": "private"}
        ).status_code
        == 403
    )
    assert client.delete(f"/api/v1/datasets/{dataset_id}", headers=other).status_code == 403
    assert ids(client.get("/api/v1/datasets", headers=lotte)) == [dataset_id]  # still there


def test_a_stranger_gets_404_for_a_private_dataset_on_patch_and_delete(client, private_key, lotte):
    dataset_id = upload(client, lotte).json()["id"]
    other = headers_for(private_key, "oid-other", ("Researcher",))
    assert (
        client.patch(
            f"/api/v1/datasets/{dataset_id}", headers=other, json={"visibility": "public"}
        ).status_code
        == 404
    )
    assert client.delete(f"/api/v1/datasets/{dataset_id}", headers=other).status_code == 404


def test_a_viewer_may_not_change_visibility_403(client, lotte, pieter):
    dataset_id = upload_public(client, lotte)["id"]
    assert (
        client.patch(
            f"/api/v1/datasets/{dataset_id}", headers=pieter, json={"visibility": "private"}
        ).status_code
        == 403
    )


def test_patching_a_missing_dataset_is_404(client, lotte):
    assert (
        client.patch("/api/v1/datasets/999", headers=lotte, json={"visibility": "public"}).status_code == 404
    )
