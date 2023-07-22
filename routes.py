from flask import Flask, request, jsonify, abort

from database.database import session
from database.models import Channels

app = Flask(__name__)

@app.route("/channels", methods=["GET"])
def get_channels():
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 10))
    access = request.args.get("access", None)
    role = request.args.get("role", None)

    filtered_channels = Channels

    if access:
        filtered_channels = [channel for channel in filtered_channels if channel.get("access") == access]

    if role:
        filtered_channels = [channel for channel in filtered_channels if channel.get("role") == role]

    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    paged_channels = filtered_channels[start_index:end_index]

    if access not in ["public", "private"]:
        abort(403, description="Неверный фильтр")

    if not paged_channels:
        return jsonify({"message": "No channels found matching the criteria"}), 404

    return jsonify(paged_channels), 200

@app.route("/channels", methods=["POST"])
def create_channel():
    if not is_user_authorized():
        abort(401, description="Пользователь не авторизован")

    data = request.json
    name = data.get("name")

    # Проверка наличия имени канала
    if not name:
        abort(400, description="Не указано имя канала")

    # Проверка уникальности имени канала в базе данных
    if session.query(Channels).filter_by(name=name).first():
        abort(400, description="Канал с таким именем уже существует")

    # Создание нового канала и сохранение в базе данных
    channel = Channels(id=20, name=name)
    session.add(channel)
    session.commit()

    # Возвращение ответа
    return jsonify({"message": "Канал успешно создан"}), 200


def is_user_authorized():
    return True


@app.route("/channels/<int:channel_id>", methods=["PUT"])
def update_channel(channel_id):
    if not is_user_authorized():
        abort(401, description="Пользователь не авторизован")

    channel = session.query(Channels).get(channel_id)

    if not channel:
        abort(404, description="Канал не найден")

    data = request.json
    name = data.get("name")
    image = data.get("image")

    # Обновление информации о канале
    if name:
        channel.name = name
    if image:
        channel.image = image

    session.commit()

    # Возвращение ответа
    return jsonify({"message": "Информация о канале обновлена"}), 200


if __name__ == '__main__':
    app.run()
