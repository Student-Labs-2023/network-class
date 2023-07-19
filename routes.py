from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "Затычка"
db = SQLAlchemy(app)

class Channel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    image = db.Column(db.Text)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "image": self.image
        }

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
    if Channel.query.filter_by(name=name).first():
        abort(400, description="Канал с таким именем уже существует")

    # Создание нового канала и сохранение в базе данных
    channel = Channel(name=name)
    db.session.add(channel)
    db.session.commit()

    # Возвращение ответа
    return jsonify({"message": "Канал успешно создан"}), 200

def is_user_authorized():
    return True

@app.route("/channels/<int:channel_id>", methods=["PUT"])
def update_channel(channel_id):
    if not is_user_authorized():
        abort(401, description="Пользователь не авторизован")

    channel = Channel.query.get(channel_id)

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

    db.session.commit()

    # Возвращение ответа
    return jsonify({"message": "Информация о канале обновлена"}), 200

if __name__ == '__main__':
    app.run()