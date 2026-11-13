import pytest

from app import create_app


@pytest.fixture()
def client():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    yield app.test_client()


def make_location(client, name="Shelf A"):
    return client.post("/api/v1/locations/", json={"name": name}).get_json()


def make_item(client, location_id, name="Laptop"):
    return client.post(
        "/api/v1/items/",
        json={"name": name, "description": "14 inch", "location": location_id},
    ).get_json()


# ---- locations ----
def test_create_location(client):
    response = client.post("/api/v1/locations/", json={"name": "Shelf A"})
    assert response.status_code == 201
    assert response.get_json()["name"] == "Shelf A"


def test_duplicate_location_name_is_rejected(client):
    make_location(client, "Shelf A")
    response = client.post("/api/v1/locations/", json={"name": "Shelf A"})
    assert response.status_code == 400
    assert "name" in response.get_json()


def test_location_without_name_is_rejected(client):
    response = client.post("/api/v1/locations/", json={})
    assert response.status_code == 400
    assert "name" in response.get_json()


# ---- items: create, read, update, delete ----
def test_create_item(client):
    location = make_location(client)
    response = client.post(
        "/api/v1/items/",
        json={"name": "Laptop", "description": "14 inch", "location": location["id"]},
    )
    assert response.status_code == 201
    assert response.get_json()["name"] == "Laptop"


def test_list_items(client):
    location = make_location(client)
    make_item(client, location["id"], "Laptop")
    make_item(client, location["id"], "Monitor")
    response = client.get("/api/v1/items/")
    assert response.status_code == 200
    assert response.get_json()["count"] == 2


def test_retrieve_item(client):
    location = make_location(client)
    item = make_item(client, location["id"])
    response = client.get(f"/api/v1/items/{item['id']}/")
    assert response.status_code == 200
    assert response.get_json()["name"] == "Laptop"


def test_retrieve_missing_item_returns_404(client):
    assert client.get("/api/v1/items/9999/").status_code == 404


def test_patch_item_changes_only_the_given_field(client):
    location = make_location(client)
    item = make_item(client, location["id"])
    response = client.patch(f"/api/v1/items/{item['id']}/", json={"description": "updated"})
    assert response.status_code == 200
    body = client.get(f"/api/v1/items/{item['id']}/").get_json()
    assert body["description"] == "updated"
    assert body["name"] == "Laptop"


def test_delete_item(client):
    location = make_location(client)
    item = make_item(client, location["id"])
    assert client.delete(f"/api/v1/items/{item['id']}/").status_code == 204
    assert client.get(f"/api/v1/items/{item['id']}/").status_code == 404


# ---- validation ----
def test_item_without_name_is_rejected(client):
    location = make_location(client)
    response = client.post(
        "/api/v1/items/", json={"description": "no name", "location": location["id"]}
    )
    assert response.status_code == 400
    assert "name" in response.get_json()


def test_item_with_unknown_location_is_rejected(client):
    response = client.post("/api/v1/items/", json={"name": "Laptop", "location": 9999})
    assert response.status_code == 400
    assert "location" in response.get_json()


def test_item_without_location_is_rejected(client):
    response = client.post("/api/v1/items/", json={"name": "Laptop"})
    assert response.status_code == 400
    assert "location" in response.get_json()


# ---- relationships and filtering ----
def test_deleting_a_location_deletes_its_items(client):
    location = make_location(client)
    item = make_item(client, location["id"])
    assert client.delete(f"/api/v1/locations/{location['id']}/").status_code == 204
    assert client.get(f"/api/v1/items/{item['id']}/").status_code == 404


def test_filter_items_by_location(client):
    shelf_a = make_location(client, "Shelf A")
    shelf_b = make_location(client, "Shelf B")
    make_item(client, shelf_a["id"], "Laptop")
    make_item(client, shelf_b["id"], "Router")
    response = client.get(f"/api/v1/items/?location={shelf_a['id']}")
    body = response.get_json()
    assert body["count"] == 1
    assert body["results"][0]["name"] == "Laptop"


# ---- pagination ----
def test_pagination_gives_20_then_the_rest(client):
    location = make_location(client)
    for i in range(25):
        make_item(client, location["id"], f"Item {i}")
    page1 = client.get("/api/v1/items/").get_json()
    page2 = client.get("/api/v1/items/?page=2").get_json()
    assert page1["count"] == 25
    assert len(page1["results"]) == 20
    assert len(page2["results"]) == 5


def test_page_beyond_the_end_returns_404(client):
    assert client.get("/api/v1/items/?page=99").status_code == 404


# ---- health ----
def test_health(client):
    response = client.get("/health/")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}