from flask import request, jsonify, abort, Blueprint

from sqlalchemy import or_

from .models import Channels

from app import db

channels = Blueprint('channels', __name__)


@channels.route("/channels", methods=["GET"])
def get_channels():
    if not is_user_authorized():
        abort(401, description="Пользователь не авторизован")

    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 10))
    access = request.args.get("access", None)
    role = request.args.get("role", None)

    if access is not None and access not in [True, False]:
        abort(403, description="Неверный фильтр")

    filters = []

    if access is not None:
        filters.append(Channels.access == access)

    # if role is not None:
    #     filters.append(Channels.access == access)

    start_index = (page - 1) * page_size
    end_index = start_index + page_size

    filtered_channels = db.session.query(Channels).filter(or_(*filters)).slice(start_index, end_index).all()

    formatted_results = []
    for channel in filtered_channels:
        formatted_channel = {
            "id": channel.id,
            "name": channel.name,
            "imageUrl": channel.photo_url,
            "url": channel.url,
            "owner": {
                "fullName": "test",
                "photoUrl": "test",
            }
        }
        formatted_results.append(formatted_channel)

    return jsonify(formatted_results), 200


@channels.route("/channels", methods=["POST"])
def create_channel():
    if not is_user_authorized():
        abort(401, description="Пользователь не авторизован")

    data = request.json
    name = data.get("name")
    url = data.get("url")
    public = True if data.get("public") is None else bool(int(data.get("public")))
    photo_url = data.get("photo_url")

    # Проверка наличия имени канала
    if not name:
        abort(400, description="Не указано имя канала")

    # Проверка уникальности имени канала в базе данных
    if db.session.query(Channels).filter_by(name=name).first():
        abort(400, description="Канал с таким именем уже существует")

    # Создание нового канала и сохранение в базе данных
    channel = Channels(name=name, url=url, public=public, photo_url=photo_url)
    db.session.add(channel)
    db.session.commit()

    # Возвращение ответа
    return jsonify({"message": "Канал успешно создан"}), 200


def is_user_authorized():
    return True


@channels.route("/channels/<int:channel_id>", methods=["PUT"])
def update_channel(channel_id):
    if not is_user_authorized():
        abort(401, description="Пользователь не авторизован")

    channel = db.session.query(Channels).get(channel_id)

    if not channel:
        abort(404, description="Канал не найден")

    data = request.json
    name = data.get("name")
    photo_url = data.get("photo_url")

    # Обновление информации о канале
    if name:
        channel.name = name
    if photo_url:
        channel.photo_url = photo_url

    db.session.commit()

    # Возвращение ответа
    return jsonify({"message": "Информация о канале обновлена"}), 200
