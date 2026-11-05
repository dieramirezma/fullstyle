import os
import time
from datetime import timedelta

from flask import current_app, make_response
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_jwt,
    jwt_required,
)
from flask_restful import Resource, reqparse
from google.auth.transport import requests
from google.oauth2 import id_token
from werkzeug.security import generate_password_hash

import utils.send_email as send_email
from config.db_config import db
from models.client_model import ClientModel
from models.manager_model import ManagerModel
from models.user_model import UserModel
from services.mfa_service import Enable2FA as Enable2FA
from services.mfa_service import Verify2FA as Verify2FA
from utils.authorization import principal_id, require_self


class User(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("name", type=str, required=True, help="This field cannot be blank.")
    parser.add_argument("email", type=str, required=True, help="This field cannot be blank.")
    parser.add_argument("password", type=str, required=True, help="This field cannot be blank.")

    @jwt_required()
    def get(self, id):
        require_self(id)
        user = UserModel.find_by_id(id)

        if user is not None and user.active:
            return user.json(), 200
        return {"message": "User not found"}, 404

    @jwt_required()
    def put(self, id):
        require_self(id)
        data = User.parser.parse_args()

        if data["password"] == "" or len(data["password"]) < 8:
            return {"message": "Password must be at least 8 characters"}, 400

        user = UserModel.find_by_id(id)
        if user is None:
            return {"message": "User not found"}, 404
        else:
            from utils.account_security import invalidate_sessions

            invalidate_sessions(user.id)
            user.password = generate_password_hash(data["password"], method="pbkdf2")
            if "google" in user.auth_provider:
                user.auth_provider = "credentials-google"
        try:
            user.save_to_db()
            return user.json(), 200
        except Exception:
            db.session.rollback()
            return {"message": "An error occurred updating the user."}, 500

    @jwt_required()
    def delete(self, id):
        require_self(id)
        user = UserModel.find_by_id(id)
        if user:
            from utils.account_security import invalidate_sessions

            invalidate_sessions(user.id)
            user.delete_from_db()
            return {"message": "User deleted"}, 200
        return {"message": "User not found"}, 404


class RegisterGoogle(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("name", type=str, required=True, help="This field cannot be blank.")
    parser.add_argument("email", type=str, required=True, help="This field cannot be blank.")

    def post(self):
        return LoginGoogle().post()


class LoginGoogle(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("email", type=str, required=True, help="This field cannot be blank.")
    parser.add_argument("token", type=str, required=True, help="Google token is required.")

    def post(self):
        data = LoginGoogle.parser.parse_args()
        if not data:
            return {"error": "No data provided"}, 400
        email = data["email"]
        token = data["token"]
        if os.getenv("LOCAL_RUNTIME") == "true":
            return {"message": "External Google login disabled locally"}, 503
        try:
            # Verificar el token de Google
            GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
            idinfo = id_token.verify_oauth2_token(token, requests.Request(), GOOGLE_CLIENT_ID)
            # Verificar que el email del token coincide con el proporcionado
            if idinfo["email"] != email:
                return {"error": "Email verification failed"}, 401
            # Verifica si el usuario ya existe
            existing_user = UserModel.query.filter_by(email=email, active=True).one_or_none()
            if not existing_user:
                new_user = UserModel(
                    email=idinfo["email"],
                    name=idinfo["name"],
                    password=None,
                    auth_provider="google",
                    google_id=idinfo["sub"],
                )
                new_user.save_to_db()
                access_token = create_access_token(identity=str(new_user.id))
                refresh_token = create_refresh_token(identity=str(new_user.id))
                response = make_response(
                    {
                        "message": "User created and logged in successfully.",
                        "user": new_user.json(),
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "manager": False,
                        "subscription_active": None,
                    }
                )
                return response
            if existing_user.password and existing_user.auth_provider == "credentials":
                # save google id to user
                existing_user.google_id = idinfo["sub"]
                existing_user.auth_provider += "-google"
                existing_user.save_to_db()

            from utils.account_security import policy

            state = policy(existing_user.id)
            if state and state.enabled:
                return {"message": "Use password and OTP authentication", "mfa_required": True}, 401
            is_manager_role = UserModel.is_manager(existing_user.id)

            # Obtener el estado de subscripción si es manager
            subscription_active = False
            if is_manager_role:
                manager = ManagerModel.find_by_id(existing_user.id)
                if manager:
                    subscription_active = manager.subscriptionactive

            # Crear tokens JWT
            from utils.account_security import session_pair

            tokens = session_pair(existing_user.id)
            access_token = tokens["access_token"]
            refresh_token = tokens["refresh_token"]
            # Crear la respuesta y establecer las cookies
            response = make_response(
                {
                    "message": "User login successfully.",
                    "user": existing_user.json(),
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "manager": is_manager_role,
                    "subscription_active": subscription_active if is_manager_role else None,
                }
            )
            return response
        except ValueError:
            # Token inválido
            current_app.logger.warning("Invalid Google token")
            return {"error": "Invalid token"}, 401
        except Exception as e:
            # Logea la excepción para depurar
            print(f"Error during login: {e}")
            return {"error": "Authentication error", "e": e}, 500


class UserRegister(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("name", type=str, required=True, help="This field cannot be blank.")
    parser.add_argument("email", type=str, required=True, help="This field cannot be blank.")
    parser.add_argument("password", type=str, required=True, help="This field cannot be blank.")

    def post(self):
        data = UserRegister.parser.parse_args()
        data["email"] = data["email"].lower()

        existing_user = UserModel.query.filter_by(email=data["email"], active=True).one_or_none()
        if (
            existing_user is not None
            and existing_user.id != id
            and UserModel.is_valid_email(data["email"])
        ):
            return {"message": "A user with that email already exists"}, 400

        if not UserModel.is_valid_email(data["email"]):
            return {"message": "Invalid email format"}, 400

        existing_user = UserModel.query.filter_by(email=data["email"], active=False).one_or_none()
        if existing_user is not None:
            user = UserModel.query.filter_by(email=data["email"], active=False).one_or_none()
            if not user.check_password(data["password"]):
                return {"message": "Invalid credentials"}, 401
            user.recover_user()
            existing_client = ClientModel.find_by_id(user.id)
            if not existing_client:
                new_client = ClientModel(id=user.id)
                new_client.save_to_db()

            return user.json(), 201

        if data["password"] == "" or len(data["password"]) < 8:
            return {"message": "Password must be at least 8 characters"}, 400

        try:
            user = UserModel(**data)
            user.password = generate_password_hash(data["password"], method="pbkdf2")
            user.save_to_db()

            # Crear nuevo cliente
            new_client = ClientModel(id=user.id)
            new_client.save_to_db()

            access_token = create_access_token(identity=str(user.id))
            refresh_token = create_refresh_token(identity=str(user.id))
            return {
                "user": user.json(),
                "access_token": access_token,
                "refresh_token": refresh_token,
            }, 200
        except Exception:
            db.session.rollback()
            return {"message": "An error occurred creating the user."}, 500


class ManagerRegister(Resource):
    parser = reqparse.RequestParser()
    # User fields
    parser.add_argument("name", type=str, required=True, help="This field cannot be blank.")
    parser.add_argument("email", type=str, required=True, help="This field cannot be blank.")
    parser.add_argument("password", type=str, required=True, help="This field cannot be blank.")
    # Manager specific fields
    parser.add_argument(
        "bankaccount", type=int, required=True, help="Bank account number is required."
    )
    parser.add_argument("accounttype", type=str, required=True, help="Account type is required.")
    parser.add_argument("bankentity", type=str, required=True, help="Bank entity is required.")

    def post(self):
        data = ManagerRegister.parser.parse_args()

        # Validate email
        existing_user = UserModel.query.filter_by(email=data["email"], active=True).one_or_none()
        if (
            existing_user is not None
            and existing_user.id != id
            and UserModel.is_valid_email(data["email"])
        ):
            return {"message": "A user with that email already exists"}, 400

        if not UserModel.is_valid_email(data["email"]):
            return {"message": "Invalid email format"}, 400

        # Check for inactive user
        existing_user = UserModel.query.filter_by(email=data["email"], active=False).one_or_none()
        if existing_user is not None:
            user = UserModel.query.filter_by(email=data["email"], active=False).one_or_none()
            if not user.check_password(data["password"]):
                return {"message": "Invalid credentials"}, 401
            user.recover_user()
            return user.json(), 201

        # Validate password
        if data["password"] == "" or len(data["password"]) < 8:
            return {"message": "Password must be at least 8 characters"}, 400

        try:
            # Crear savepoint
            with db.session.begin_nested():
                # Create user first
                user_data = {
                    "name": data["name"],
                    "email": data["email"].lower(),
                    "password": generate_password_hash(data["password"], method="pbkdf2"),
                }
                user = UserModel(**user_data)
                db.session.add(user)

                # Hacer flush para obtener el ID del usuario
                db.session.flush()

                # Create manager with reference to user
                manager_data = {
                    "bankaccount": data["bankaccount"],
                    "accounttype": data["accounttype"],
                    "bankentity": data["bankentity"],
                    "userModel": user,
                }
                manager = ManagerModel(**manager_data)
                db.session.add(manager)

            # Commit de la sesión principal
            db.session.commit()

            # Generate tokens
            access_token = create_access_token(identity=str(user.id))
            refresh_token = create_refresh_token(identity=str(user.id))

            return {
                "user": user.json(),
                "manager": manager.json(),
                "access_token": access_token,
                "refresh_token": refresh_token,
            }, 200
        except Exception as e:
            db.session.rollback()
            return {"message": f"Ocurrio un error registrando el gerente: {str(e)}"}, 500


class UserLogin(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("name", type=str, required=False, help="This field cannot be blank.")
    parser.add_argument("email", type=str, required=False, help="This field cannot be blank.")
    parser.add_argument("password", type=str, required=True, help="This field cannot be blank.")

    parser.add_argument("otp", type=str, required=False)

    def post(self):
        data = UserLogin.parser.parse_args()
        email = data["email"].lower() if data["email"] else None  # Convertir email a minúsculas
        name = data["name"]
        password = data["password"]

        if not email and not name:
            return {"message": "Invalid credentials"}, 401

        user_email = UserModel.query.filter_by(email=email, active=True).one_or_none()
        user_name = UserModel.query.filter_by(name=name, active=True).one_or_none()

        if user_email is None and user_name is None:
            return {"message": "Invalid credentials"}, 401

        user = user_email if user_email is not None else user_name

        if not user or not user.check_password(password):
            current_app.logger.warning(f"Intento de login fallido - Email: {email} - Name: {name}")
            return {"message": "Invalid credentials"}, 401

        # Usar el método is_manager que implementamos
        is_manager_role = UserModel.is_manager(user.id)

        # Obtener el estado de subscripción si es manager
        subscription_active = False
        if is_manager_role:
            manager = ManagerModel.find_by_id(user.id)
            if manager:
                subscription_active = manager.subscriptionactive

        from utils.account_security import password_login

        tokens = password_login(user, data.get("otp"), password)
        if tokens is None:
            return {"message": "MFA required or invalid OTP", "mfa_required": True}, 401
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]

        return {
            "user": user.json(),
            "access_token": access_token,
            "refresh_token": refresh_token,
            "manager": is_manager_role,
            "subscription_active": subscription_active if is_manager_role else None,
        }, 200


class UserLogout(Resource):
    @jwt_required(verify_type=False, skip_revocation_check=True)
    def delete(self):
        from sqlalchemy.exc import IntegrityError

        from models.session_model import RevokedToken

        claims = get_jwt()
        from sqlalchemy.dialects.postgresql import insert

        from utils.account_security import policy, session_valid

        policy(int(claims["sub"]), lock=True)
        if not session_valid(claims, int(claims["sub"])):
            db.session.rollback()
            return {"message": "Session policy changed"}, 401
        db.session.execute(
            insert(RevokedToken)
            .values(
                subject=claims["sub"],
                token_type="family",
                jti=claims.get("session_family", claims["jti"]),
                expires_at=int(time.time()) + 15 * 86400,
            )
            .on_conflict_do_nothing()
        )
        db.session.execute(
            insert(RevokedToken)
            .values(
                subject=claims["sub"],
                token_type=claims["type"],
                jti=claims["jti"],
                expires_at=claims["exp"],
            )
            .on_conflict_do_nothing()
        )
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
        return {"message": "Successfully logged out"}, 200


class User2FA(Resource):
    @jwt_required(verify_type=False)
    def get(self):
        user = UserModel.find_by_id(principal_id())
        if user is None:
            return {"message": "User not found"}, 404

        return {"message": "Use password-confirmed /api/enable-2fa enrollment"}, 409


class Test(Resource):
    @jwt_required()
    def get(self):
        users = [UserModel.find_by_id(principal_id())]

        if users:
            users_json = [user.json() for user in users]
            return users_json, 200
        return {"message": "User not found"}, 404


class ResetPasswordRequest(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("email", type=str, required=True, help="This field cannot be blank.")

    def post(self):
        try:
            data = ResetPasswordRequest.parser.parse_args()
            email = data["email"]

            user = UserModel.query.filter_by(email=email, active=True).first()
            if not user:
                return {"message": "User not found"}, 404

            reset_token = create_access_token(
                identity=str(user.id),
                expires_delta=timedelta(minutes=15),
                additional_claims={"purpose": "password-reset"},
            )

            send_email.ResetPassword(email, user.name, reset_token)
            return {"message": "A reset link has been sent to your email"}, 200
        except Exception as e:
            return {"message": f"Error: {str(e)}"}, 400


class ResetPasswordConfirm(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("token", type=str, required=True, help="Token is required.")
    parser.add_argument("password", type=str, required=True, help="New password is required.")

    def post(self):
        data = ResetPasswordConfirm.parser.parse_args()
        token = data["token"]
        new_password = data["password"]

        if len(new_password) < 8:
            return {"message": "Password must be at least 8 characters"}, 400

        try:
            decoded_token = decode_token(token)
            from utils.sessions import revoked

            if decoded_token.get("purpose") != "password-reset" or revoked(decoded_token):
                return {"message": "Invalid reset token"}, 400
            user_id = decoded_token.get("sub")

            user = UserModel.find_by_id(user_id)
            if not user:
                return {"message": "Invalid token or user not found"}, 400

            # Actualizar la contraseña
            user.password = generate_password_hash(new_password, method="pbkdf2")
            if "google" in user.auth_provider:
                user.auth_provider = "credentials-google"
            from models.session_model import RevokedToken

            db.session.add(
                RevokedToken(
                    subject=decoded_token["sub"],
                    token_type=decoded_token["type"],
                    jti=decoded_token["jti"],
                    expires_at=decoded_token["exp"],
                )
            )
            db.session.commit()
            return {"message": "Password successfully reset"}, 200

        except Exception:
            db.session.rollback()
            return {"message": "Invalid reset token"}, 400
