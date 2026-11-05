"""Preserve operational routes while disabling unsafe shared Redis operations."""

from flask_jwt_extended import jwt_required
from flask_restful import Resource


class CacheStats(Resource):
    @jwt_required()
    def get(self):
        return {"message": "Use local Docker diagnostics for cache administration"}, 403


class CacheTest(CacheStats):
    pass


class CacheClear(Resource):
    @jwt_required()
    def delete(self):
        return {"message": "Shared Redis flush is disabled"}, 403
