from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from tests.conftest import login

SHIFT_PAYLOAD = {
    "name": "Day",
    "start_time": "09:00:00",
    "end_time": "18:00:00",
    "break_minutes": 60,
}


def _create_shift(client: TestClient) -> dict:
    login(client, "admin@test.example", "AdminPass123")
    r = client.post("/shifts", json=SHIFT_PAYLOAD)
    assert r.status_code == 201
    return r.json()


def _staff_id(db_session: Session) -> str:
    return str(db_session.query(User).filter(User.email == "staff@test.example").one().id)


def test_manager_can_create_schedule(client: TestClient, db_session: Session) -> None:
    shift = _create_shift(client)
    login(client, "manager@test.example", "ManagerPass123")

    response = client.post(
        "/schedules",
        json={"user_id": _staff_id(db_session), "shift_id": shift["id"], "work_date": "2026-07-01"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["work_date"] == "2026-07-01"
    assert body["scheduled_start"] == "09:00:00"
    assert body["status"] == "SCHEDULED"


def test_staff_cannot_create_schedule(client: TestClient, db_session: Session) -> None:
    shift = _create_shift(client)
    login(client, "staff@test.example", "StaffPass123")

    response = client.post(
        "/schedules",
        json={"user_id": _staff_id(db_session), "shift_id": shift["id"], "work_date": "2026-07-02"},
    )

    assert response.status_code == 403


def test_duplicate_schedule_is_rejected(client: TestClient, db_session: Session) -> None:
    shift = _create_shift(client)
    login(client, "admin@test.example", "AdminPass123")
    payload = {"user_id": _staff_id(db_session), "shift_id": shift["id"], "work_date": "2026-07-03"}

    client.post("/schedules", json=payload)
    response = client.post("/schedules", json=payload)

    assert response.status_code == 400


def test_staff_can_view_own_schedules(client: TestClient, db_session: Session) -> None:
    shift = _create_shift(client)
    sid = _staff_id(db_session)
    client.post("/schedules", json={"user_id": sid, "shift_id": shift["id"], "work_date": "2026-07-04"})

    login(client, "staff@test.example", "StaffPass123")
    response = client.get("/schedules")

    assert response.status_code == 200
    assert all(s["user_id"] == sid for s in response.json())


def test_staff_cannot_see_other_schedules_via_user_id_filter(
    client: TestClient, db_session: Session
) -> None:
    shift = _create_shift(client)
    admin_id = str(db_session.query(User).filter(User.email == "admin@test.example").one().id)
    client.post(
        "/schedules",
        json={"user_id": admin_id, "shift_id": shift["id"], "work_date": "2026-07-05"},
    )

    login(client, "staff@test.example", "StaffPass123")
    response = client.get(f"/schedules?user_id={admin_id}")

    assert response.status_code == 200
    assert all(s["user_id"] != admin_id for s in response.json())


def test_manager_can_view_all_schedules(client: TestClient, db_session: Session) -> None:
    shift = _create_shift(client)
    sid = _staff_id(db_session)
    admin_id = str(db_session.query(User).filter(User.email == "admin@test.example").one().id)
    client.post("/schedules", json={"user_id": sid, "shift_id": shift["id"], "work_date": "2026-07-06"})
    client.post("/schedules", json={"user_id": admin_id, "shift_id": shift["id"], "work_date": "2026-07-06"})

    login(client, "manager@test.example", "ManagerPass123")
    response = client.get("/schedules")

    assert response.status_code == 200
    user_ids = {s["user_id"] for s in response.json()}
    assert len(user_ids) >= 2


def test_schedules_filter_by_date_range(client: TestClient, db_session: Session) -> None:
    shift = _create_shift(client)
    sid = _staff_id(db_session)
    for day in ["2026-07-07", "2026-07-08", "2026-08-01"]:
        client.post("/schedules", json={"user_id": sid, "shift_id": shift["id"], "work_date": day})

    response = client.get("/schedules?start_date=2026-07-01&end_date=2026-07-31")

    assert response.status_code == 200
    dates = [s["work_date"] for s in response.json()]
    assert "2026-07-07" in dates
    assert "2026-07-08" in dates
    assert "2026-08-01" not in dates


def test_generate_schedules(client: TestClient, db_session: Session) -> None:
    shift = _create_shift(client)
    sid = _staff_id(db_session)

    response = client.post(
        "/schedules/generate",
        json={
            "user_id": sid,
            "shift_id": shift["id"],
            "start_date": "2026-09-01",
            "end_date": "2026-09-30",
            "weekdays": [0, 1, 2, 3, 4],  # Mon–Fri
        },
    )

    assert response.status_code == 201
    created = response.json()
    assert len(created) == 22  # 22 weekdays in Sep 2026
    assert all(s["scheduled_start"] == "09:00:00" for s in created)


def test_generate_skips_existing_schedules(client: TestClient, db_session: Session) -> None:
    shift = _create_shift(client)
    sid = _staff_id(db_session)
    client.post(
        "/schedules",
        json={"user_id": sid, "shift_id": shift["id"], "work_date": "2026-10-05"},
    )

    response = client.post(
        "/schedules/generate",
        json={
            "user_id": sid,
            "shift_id": shift["id"],
            "start_date": "2026-10-05",
            "end_date": "2026-10-05",
            "weekdays": [0],  # Monday
        },
    )

    assert response.status_code == 201
    assert response.json() == []  # skipped because it already existed


def test_manager_can_delete_schedule(client: TestClient, db_session: Session) -> None:
    shift = _create_shift(client)
    sid = _staff_id(db_session)
    create_resp = client.post(
        "/schedules",
        json={"user_id": sid, "shift_id": shift["id"], "work_date": "2026-11-01"},
    )
    schedule_id = create_resp.json()["id"]

    login(client, "manager@test.example", "ManagerPass123")
    response = client.delete(f"/schedules/{schedule_id}")

    assert response.status_code == 204

    get_resp = client.get(f"/schedules?start_date=2026-11-01&end_date=2026-11-01")
    assert all(s["id"] != schedule_id for s in get_resp.json())


def test_staff_cannot_delete_schedule(client: TestClient, db_session: Session) -> None:
    shift = _create_shift(client)
    sid = _staff_id(db_session)
    create_resp = client.post(
        "/schedules",
        json={"user_id": sid, "shift_id": shift["id"], "work_date": "2026-11-02"},
    )
    schedule_id = create_resp.json()["id"]

    login(client, "staff@test.example", "StaffPass123")
    response = client.delete(f"/schedules/{schedule_id}")

    assert response.status_code == 403


def test_generate_rejects_invalid_date_range(client: TestClient, db_session: Session) -> None:
    shift = _create_shift(client)
    sid = _staff_id(db_session)

    response = client.post(
        "/schedules/generate",
        json={
            "user_id": sid,
            "shift_id": shift["id"],
            "start_date": "2026-09-30",
            "end_date": "2026-09-01",
            "weekdays": [0],
        },
    )

    assert response.status_code == 422
