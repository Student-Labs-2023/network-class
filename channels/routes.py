from flask import request, jsonify, abort, Blueprint
from sqlalchemy import or_

from channels.models import Channels, UserChannels

from database.database import db

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

    filtered_channels = Channels.query.filter(or_(*filters)).slice(start_index, end_index).all()

    formatted_results = []
    for channel in filtered_channels:
        owner_id_result = UserChannels.query.filter_by(channel_id=channel.id, role_id=1).first()
        owner_id = owner_id_result.user_id if owner_id_result is not None else str(owner_id_result)
        formatted_channel = {
            "id": channel.id,
            "name": channel.name,
            "imageUrl": channel.photo_url,
            "url": channel.url,
            "public": channel.public,
            "owner_id": owner_id
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
    owner_id = data.get("owner_id")
    photo_url = data.get("photo_url")

    # Проверка наличия имени канала
    if not name or not owner_id:
        abort(403, description="Неверный фильтр")

    # Проверка уникальности имени канала в базе данных
    if Channels.query.filter_by(name=name).first():
        abort(400, description="Канал с таким именем уже существует")

    # Создание нового канала и сохранение в базе данных
    channel = Channels(name=name, url=url, public=public, photo_url=photo_url)

    channel.create()
    user_channel = UserChannels(user_id=owner_id, channel_id=channel.id, role_id=1)
    user_channel.create()

    # Возвращение ответа
    return jsonify({"message": "Канал успешно создан"}), 200


def is_user_authorized():
    return True


@channels.route("/channels/<int:channel_id>", methods=["PUT"])
def update_channel(channel_id):
    if not is_user_authorized():
        abort(401, description="Пользователь не авторизован")

    channel = Channels.query.get(channel_id)

    if not channel:
        abort(404, description="Канал не найден")

    data = request.json
    name = data.get("name")
    photo_url = data.get("photo_url")
    url = data.get("url")
    public = data.get("public")

    # Обновление информации о канале
    if name:
        channel.name = name
    if photo_url:
        channel.photo_url = photo_url
    if public is not None:
        channel.public = bool(int(public))

    db.session.commit()

    # Возвращение ответа
    return jsonify({"message": "Информация о канале обновлена"}), 200


@channels.route("/channels", methods=['DELETE'])
def delete_channel():
    if not is_user_authorized():
        abort(401, description="Пользователь не авторизован")

    data = request.json
    channel_id = data.get("channel_id")

    # Проверка наличия имени канала
    if not channel_id:
        abort(403, description="Неверный фильтр")

    # Проверка уникальности имени канала в базе данных

    deleted_count_channels = Channels.query.filter_by(id=channel_id).delete()
    UserChannels.query.filter_by(channel_id=channel_id).delete()

    db.session.commit()

    # Возвращение ответа
    return jsonify({"message": f"Удалено {deleted_count_channels} каналов"}), 200
