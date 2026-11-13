from flask import Blueprint, current_app, jsonify, request
from sqlalchemy.exc import IntegrityError

from . import db
from .models import Item, Location

bp = Blueprint("api", __name__)

NAME_MAX = 100


def bad_request(errors):
    return jsonify(errors), 400


def paginated(query, serializer):
    page = request.args.get("page", 1, type=int)
    p = query.paginate(
        page=page, per_page=current_app.config["PAGE_SIZE"], error_out=False
    )
    if page > 1 and not p.items:
        return jsonify(error="invalid page"), 404
    return jsonify(
        count=p.total,
        pages=p.pages,
        page=p.page,
        results=[serializer(x) for x in p.items],
    )


def validate_name(data, required=True):
    """Return (name, error_message)."""
    if "name" not in data:
        return None, "This field is required." if required else None
    name = data["name"]
    if not isinstance(name, str) or not name.strip():
        return None, "This field may not be blank."
    if len(name) > NAME_MAX:
        return None, f"Ensure this field has no more than {NAME_MAX} characters."
    return name, None


# ---------------------------------------------------------------- locations

@bp.get("/locations/")
def list_locations():
    return paginated(Location.query.order_by(Location.id), Location.to_dict)


@bp.post("/locations/")
def create_location():
    data = request.get_json(silent=True) or {}
    name, err = validate_name(data)
    if err:
        return bad_request({"name": [err]})
    loc = Location(name=name)
    db.session.add(loc)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return bad_request({"name": ["location with this name already exists."]})
    return jsonify(loc.to_dict()), 201


@bp.get("/locations/<int:id>/")
def get_location(id):
    return jsonify(db.get_or_404(Location, id).to_dict())


@bp.route("/locations/<int:id>/", methods=["PUT", "PATCH"])
def update_location(id):
    loc = db.get_or_404(Location, id)
    data = request.get_json(silent=True) or {}
    name, err = validate_name(data, required=request.method == "PUT")
    if err:
        return bad_request({"name": [err]})
    if name is not None:
        loc.name = name
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return bad_request({"name": ["location with this name already exists."]})
    return jsonify(loc.to_dict())


@bp.delete("/locations/<int:id>/")
def delete_location(id):
    db.session.delete(db.get_or_404(Location, id))
    db.session.commit()
    return "", 204


# -------------------------------------------------------------------- items

def validate_location(data, required=True):
    if "location" not in data:
        return None, "This field is required." if required else None
    loc_id = data["location"]
    if isinstance(loc_id, bool) or not isinstance(loc_id, int):
        return None, "A valid integer is required."
    if db.session.get(Location, loc_id) is None:
        return None, "Invalid pk - object does not exist."
    return loc_id, None


def validate_item(data, partial):
    errors = {}
    name, err = validate_name(data, required=not partial)
    if err:
        errors["name"] = [err]
    loc_id, err = validate_location(data, required=not partial)
    if err:
        errors["location"] = [err]
    description = data.get("description", None)
    if description is not None and not isinstance(description, str):
        errors["description"] = ["Not a valid string."]
    return name, description, loc_id, errors


@bp.get("/items/")
def list_items():
    q = Item.query.order_by(Item.id)
    location = request.args.get("location")
    if location is not None:
        if not location.isdigit():
            q = q.filter(db.false())
        else:
            q = q.filter_by(location_id=int(location))
    return paginated(q, Item.to_dict)


@bp.post("/items/")
def create_item():
    data = request.get_json(silent=True) or {}
    name, description, loc_id, errors = validate_item(data, partial=False)
    if errors:
        return bad_request(errors)
    item = Item(name=name, description=description or "", location_id=loc_id)
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201


@bp.get("/items/<int:id>/")
def get_item(id):
    return jsonify(db.get_or_404(Item, id).to_dict())


@bp.route("/items/<int:id>/", methods=["PUT", "PATCH"])
def update_item(id):
    item = db.get_or_404(Item, id)
    data = request.get_json(silent=True) or {}
    name, description, loc_id, errors = validate_item(
        data, partial=request.method == "PATCH"
    )
    if errors:
        return bad_request(errors)
    if name is not None:
        item.name = name
    if description is not None:
        item.description = description
    if loc_id is not None:
        item.location_id = loc_id
    db.session.commit()
    return jsonify(item.to_dict())


@bp.delete("/items/<int:id>/")
def delete_item(id):
    db.session.delete(db.get_or_404(Item, id))
    db.session.commit()
    return "", 204
