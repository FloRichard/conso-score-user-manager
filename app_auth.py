import os
import psycopg2
import json
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc
from flask import Flask, request, abort
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
from flask_cors import cross_origin

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})

app.config["SQLALCHEMY_DATABASE_URI"] = 'postgresql+psycopg2://'+"conso_score_user"+':'+"conso_score_user_pwd"+'@conso_score_postgresql:5432/consoscore'
db = SQLAlchemy(app)

with app.app_context():
    db.Model.metadata.reflect(bind=db.engine)

class User(db.Model):
    __table__ = db.Model.metadata.tables["user"]

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Status(db.Model):
    __table__ = db.Model.metadata.tables["status"]

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Maker(db.Model):
    __table__ = db.Model.metadata.tables["maker"]

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Seller(db.Model):
    __table__ = db.Model.metadata.tables["seller"]

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

@app.route('/register', methods=['POST'])
@cross_origin()
def register():
    body = request.get_json()
    password_hash = generate_password_hash(body['password'], method='sha256')
    if body['status'] == 'MAKER':
        maker = Maker(name=body['maker_name'], location=body['maker_location'])
        db.session.add(maker)
        db.session.flush()
        db.session.refresh(maker)
        status = Status(maker_id=maker.maker_id, label='MAKER')
    elif body['status'] == 'SELLER':
        seller = Seller(name=body['seller_name'], location=body['seller_location'])
        db.session.add(seller)
        db.session.flush()
        db.session.refresh(seller)
        status = Status(seller_id=seller.seller_id, label='SELLER')
    else:
        abort(400)
    db.session.add(status)
    db.session.flush()
    db.session.refresh(status)
    user = User(status_id=status.status_id, name=body['name'], login=body['login'], password=password_hash)
    db.session.add(user)
    db.session.commit()
    return "User is registered", 201

@app.route('/user/<string:user_id>', methods=['GET'])
@cross_origin()
def get_user(user_id):
    try:
        result = db.session.query(User, Status).join(Status).filter(User.user_id == user_id).first()
    except exc.StatementError: # wrong uuid format
        abort(400)
    if not result:
        abort(404)
    user, status = result
    r = {'name': user.name, 'status': status.label}
    if status.maker_id == None:
        seller = db.session.query(Seller).filter_by(seller_id=status.seller_id).first()
        r['seller_name'] = seller.name
        r['seller_location'] = seller.location
    else:
        maker = db.session.query(Maker).filter_by(maker_id=status.maker_id).first()
        r['maker_name'] = maker.name
        r['maker_location'] = maker.location
    return r

@app.route('/login', methods=['POST'])
@cross_origin()
def login():
    body = request.get_json()
    login = body['login']
    password = body['password']

    user = db.session.query(User).filter_by(login=login).first()

    if not user or not check_password_hash(user.password, password):
        abort(404)

    status = db.session.query(Status).filter_by(status_id=user.status_id).first()
    if status.label == 'MAKER':
        return {'user_id': user.user_id, 'entity_id': status.maker_id, 'status': status.label}
    else:
        return {'user_id': user.user_id, 'entity_id': status.seller_id, 'status': status.label}