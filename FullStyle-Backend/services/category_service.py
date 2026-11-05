from models.category_model import CategoryModel
from flask_restful import Resource, reqparse
from flask_jwt_extended import jwt_required
from utils.cache_helper import cache_result, CACHE_TTL

class Category(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('name', type=str, required=True, help="This field cannot be left blank!")

    @jwt_required()
    @cache_result(ttl=CACHE_TTL['categories'], use_request_args=False)
    def get(self):
        categories = CategoryModel.get_all_categories()

        if categories:
            categories_json = [category.json() for category in categories]
            return categories_json, 200
        return {"message": "Category not found"}, 404