from flask_jwt_extended import jwt_required
from flask_restful import Resource, reqparse

from models.manager_model import ManagerModel
from utils.authorization import require_self


class Subscription(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument(
        "subscriptionactive", type=bool, required=True, help="Subscription status is required."
    )
    parser.add_argument(
        "subscriptionstartdate",
        type=str,
        required=False,
        help="Start date of the subscription (format: YYYY-MM-DDThh:mm:ss)",
    )
    parser.add_argument("subscriptiontype", type=str, required=False, help="Type of subscription")
    parser.add_argument(
        "subscriptionfinishdate",
        type=str,
        required=False,
        help="End date of the subscription (format: YYYY-MM-DDThh:mm:ss)",
    )

    @jwt_required()
    def get(self, id):
        require_self(id)
        manager = ManagerModel.find_by_id(id)
        if not manager:
            return {"message": "Manager not found"}, 404

        return {
            "id": manager.id,
            "subscriptionactive": manager.subscription_is_active(),
            "subscriptionstartdate": manager.subscriptionstartdate.isoformat()
            if manager.subscriptionstartdate
            else None,
            "subscriptiontype": manager.subscriptiontype,
            "subscriptionfinishdate": manager.subscriptionfinishdate.isoformat()
            if manager.subscriptionfinishdate
            else None,
        }, 200

    @jwt_required()
    def put(self, id):
        require_self(id)
        manager = ManagerModel.find_by_id(id)
        if not manager:
            return {"message": "Manager not found"}, 404
        return {"message": "Subscription changes require a verified billing workflow"}, 403
