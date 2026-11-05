"""Additive identity adapter for callers that delegate user access tokens."""

from flask_jwt_extended import jwt_required
from flask_restful import Resource

from models.user_model import UserModel
from utils.authorization import principal_id


class CurrentUser(Resource):
    @jwt_required()
    def get(self):
        from models.manager_model import ManagerModel

        user = UserModel.find_by_id(principal_id())
        manager = ManagerModel.find_by_id(user.id)
        return {
            **user.json(),
            "is_manager": manager is not None,
            "subscriptionactive": bool(manager and manager.subscription_is_active()),
        }, 200
