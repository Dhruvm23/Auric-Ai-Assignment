"""C2 compliance: GET /rooms returns the exact shape the facilities dashboard expects."""


def test_rooms_response_shape(client):
    resp = client.get("/rooms")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 4

    first = data[0]
    assert set(first.keys()) == {"id", "name", "capacity"}


def test_rooms_match_seed_data(client):
    resp = client.get("/rooms")
    data = resp.json()
    expected = [
        {"id": 3, "name": "Aurora", "capacity": 8},
        {"id": 4, "name": "Basalt", "capacity": 4},
        {"id": 9, "name": "Cinder", "capacity": 12},
        {"id": 17, "name": "Dune", "capacity": 6},
    ]
    assert data == expected


def test_rooms_ordered_by_id(client):
    resp = client.get("/rooms")
    ids = [r["id"] for r in resp.json()]
    assert ids == sorted(ids)
