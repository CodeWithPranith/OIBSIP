import pytest

from bmi_app.database import BMIDatabase, DatabaseError


@pytest.fixture
def db(tmp_path):
    database = BMIDatabase(tmp_path / "test.db")
    yield database
    database.close()


def test_save_and_read_back(db):
    db.save_record("Asha", 60, 1.65, 22.04, "Normal", "2026-01-01T10:00:00")
    history = db.get_history("Asha")
    assert len(history) == 1
    assert history[0]["bmi"] == 22.04
    assert history[0]["category"] == "Normal"


def test_multiple_users_are_separate(db):
    db.save_record("Asha", 60, 1.65, 22.04, "Normal", "2026-01-01T10:00:00")
    db.save_record("Ravi", 95, 1.70, 32.87, "Obese", "2026-01-02T10:00:00")
    assert db.get_users() == ["Asha", "Ravi"]
    assert len(db.get_history("Ravi")) == 1
    assert db.get_history("Ravi")[0]["category"] == "Obese"


def test_history_sorted_oldest_first(db):
    db.save_record("Asha", 62, 1.65, 22.77, "Normal", "2026-02-01T10:00:00")
    db.save_record("Asha", 60, 1.65, 22.04, "Normal", "2026-01-01T10:00:00")
    dates = [r["recorded_at"] for r in db.get_history("Asha")]
    assert dates == sorted(dates)


def test_names_are_case_insensitive(db):
    db.save_record("Asha", 60, 1.65, 22.04, "Normal", "2026-01-01T10:00:00")
    assert len(db.get_history("asha")) == 1


def test_empty_name_rejected(db):
    with pytest.raises(DatabaseError):
        db.save_record("   ", 60, 1.65, 22.04, "Normal")


def test_data_persists_after_reopen(tmp_path):
    path = tmp_path / "persist.db"
    first = BMIDatabase(path)
    first.save_record("Asha", 60, 1.65, 22.04, "Normal", "2026-01-01T10:00:00")
    first.close()
    second = BMIDatabase(path)
    assert len(second.get_history("Asha")) == 1
    second.close()


def test_sql_injection_text_is_stored_safely(db):
    nasty = "x'; DROP TABLE records; --"
    db.save_record(nasty, 60, 1.65, 22.04, "Normal", "2026-01-01T10:00:00")
    assert db.get_users() == [nasty]


def test_unwritable_location_raises_database_error(tmp_path):
    blocker = tmp_path / "file.txt"
    blocker.write_text("not a folder")
    with pytest.raises(DatabaseError):
        BMIDatabase(blocker / "sub" / "x.db")


def test_closed_database_raises_database_error(tmp_path):
    database = BMIDatabase(tmp_path / "t.db")
    database.close()
    with pytest.raises(DatabaseError):
        database.save_record("Asha", 60, 1.65, 22.04, "Normal")
