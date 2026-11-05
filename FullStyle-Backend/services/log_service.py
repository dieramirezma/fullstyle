"""Operational logs are unavailable over public application routes."""

from flask_jwt_extended import jwt_required
from flask_restful import Resource


class GetLogs(Resource):
    @jwt_required()
    def get(self):
        return {"message": "Use local Docker diagnostics for operational logs"}, 403
