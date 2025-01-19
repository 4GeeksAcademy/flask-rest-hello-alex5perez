"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, People, Planet, FavoritePlanets
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/user', methods=['GET'])
def handle_hello():

    response_body = {
        "msg": "Hello, this is your GET /user response "
    }

    return jsonify(response_body), 200

# [GET] /people Listar todos los registros de people en la base de datos.
@app.route('/people', methods=['GET'])
def get_people():
    all_people = People.query.all()
    all_people_serialized = [person.serialize() for person in all_people]
    return jsonify({'msg': 'get people ok', 'data': all_people_serialized}), 200

# [GET] /people/<int:people_id> Muestra la información de un solo personaje según su id.
@app.route('/people/<int:people_id>', methods=['GET'])
def get_single_person(people_id):
    person = People.query.get(people_id)
    if person is None:
        return jsonify({'msg': f'El personaje con id {people_id} no existe'}), 404
    return jsonify({'data': person.serialize()}), 200

# [GET] /planets Listar todos los registros de planets en la base de datos.
@app.route('/planets', methods=['GET'])
def get_planets():
    all_planets = Planet.query.all()
    all_planets_serialized = [planet.serialize() for planet in all_planets]
    return jsonify({'msg': 'get planets ok', 'data': all_planets_serialized}), 200

# [GET] /planets/<int:planet_id> Muestra la información de un solo planeta según su id.
@app.route('/planet/<int:planet_id>', methods=['GET'])
def get_single_planet(planet_id):
    planet = Planet.query.get(planet_id)
    if planet is None:
        return jsonify({'msg': f'El planeta con id {planet_id} no existe'}), 404
    planet_serialized = planet.serialize()
    planet_serialized['people'] = [person.serialize() for person in planet.people]
    return jsonify({'msg': 'ok', 'data': planet_serialized}), 200

# [GET] /users Listar todos los usuarios del blog.
@app.route('/users', methods=['GET'])
def get_users():
    all_users = User.query.all()
    all_users_serialized = [user.serialize() for user in all_users]
    return jsonify({'msg': 'get users ok', 'data': all_users_serialized}), 200

# [GET] /users/<int:user_id>/favorites Listar todos los favoritos que pertenecen al usuario actual.
@app.route('/user/<int:user_id>/favorites', methods=['GET'])
def get_favorites_by_user(user_id):
    favorite_planets = FavoritePlanets.query.filter_by(user_id=user_id).all()
    if not favorite_planets:
        return jsonify({'msg': 'No se encontraron favoritos para este usuario'}), 404
    favorite_planets_serialized = [favorite.planets_favorites.serialize() for favorite in favorite_planets]
    return jsonify({'favorite_planets': favorite_planets_serialized, 'user': favorite_planets[0].users.serialize()}), 200

# [POST] /favorite/<int:user_id>/planet/<int:planet_id> Añade un nuevo planeta favorito
@app.route('/favorite/<int:user_id>/planet/<int:planet_id>', methods=['POST'])
def add_favorite_planet(user_id, planet_id):
    user = User.query.get(user_id)
    planet = Planet.query.get(planet_id)
    
    if user is None or planet is None:
        return jsonify({'msg': 'Usuario o planeta no encontrado'}), 404
    
    # Verificar si ya existe el favorito
    existing_favorite = FavoritePlanets.query.filter_by(user_id=user_id, planet_id=planet_id).first()
    if existing_favorite:
        return jsonify({'msg': 'Este planeta ya está en los favoritos del usuario'}), 400
    
    new_favorite = FavoritePlanets(user_id=user_id, planet_id=planet_id)
    db.session.add(new_favorite)
    db.session.commit()
    return jsonify({'msg': 'Favorito añadido'}), 200

# [POST] /favorite/<int:user_id>/people/<int:people_id> Añade un nuevo personaje favorito
@app.route('/favorite/<int:user_id>/people/<int:people_id>', methods=['POST'])
def add_favorite_people(user_id, people_id):
    user = User.query.get(user_id)
    person = People.query.get(people_id)
    
    if user is None or person is None:
        return jsonify({'msg': 'Usuario o personaje no encontrado'}), 404
    
    # Verificar si ya existe el favorito
    existing_favorite = FavoritePlanets.query.filter_by(user_id=user_id, people_id=people_id).first()
    if existing_favorite:
        return jsonify({'msg': 'Este personaje ya está en los favoritos del usuario'}), 400
    
    new_favorite = FavoritePlanets(user_id=user_id, people_id=people_id)
    db.session.add(new_favorite)
    db.session.commit()
    return jsonify({'msg': 'Favorito añadido'}), 200

# [DELETE] /favorite/<int:user_id>/planet/<int:planet_id> Elimina un planet favorito con el id = planet_id.
@app.route('/favorite/<int:user_id>/planet/<int:planet_id>', methods=['DELETE'])
def delete_favorite_planet(user_id, planet_id):
    favorite = FavoritePlanets.query.filter_by(user_id=user_id, planet_id=planet_id).first()
    if favorite is None:
        return jsonify({'msg': 'El favorito no existe'}), 404
    db.session.delete(favorite)
    db.session.commit()
    return jsonify({'msg': 'Favorito eliminado'}), 200

# [DELETE] /favorite/<int:user_id>/people/<int:people_id> Elimina un people favorito con el id = people_id.
@app.route('/favorite/<int:user_id>/people/<int:people_id>', methods=['DELETE'])
def delete_favorite_people(user_id, people_id):
    favorite = FavoritePlanets.query.filter_by(user_id=user_id, people_id=people_id).first()
    if favorite is None:
        return jsonify({'msg': 'El favorito no existe'}), 404
    db.session.delete(favorite)
    db.session.commit()
    return jsonify({'msg': 'Favorito eliminado'}), 200

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)

