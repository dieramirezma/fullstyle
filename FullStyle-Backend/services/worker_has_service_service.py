from utils.authorization import tenant_write
from models.worker_has_service_model import WorkerHasServiceModel
from flask_restful import Resource, reqparse
from utils.helpers import (
    check_worker_exists,
    check_service_allowed_for_site,
    check_worker_service_exists
)
from flask_jwt_extended import jwt_required

class WorkerHasService(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('worker_id', type=int, required=True, help="This field cannot be left blank!")
    parser.add_argument('service_id', type=int, required=True, help="This field cannot be left blank!")

    @jwt_required()
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('worker_id', type=int, location='args', required=False)
        parser.add_argument('service_id', type=int, location='args', required=False)
        args = parser.parse_args()

        query = WorkerHasServiceModel.query

        if args['worker_id']:
            query = query.filter_by(worker_id=args['worker_id'])

        if args['service_id']:
            query = query.filter_by(service_id=args['service_id'])

        worker_services = query.all()

        if worker_services:
            worker_services_json = [worker_service.json() for worker_service in worker_services]
            return worker_services_json, 200
        return {"message": "Worker-Has-Service not found"}, 404

    @jwt_required()
    @tenant_write()
    def post(self):
        data = WorkerHasService.parser.parse_args()

        # Check if worker exists
        worker, error = check_worker_exists(data['worker_id'])
        if error:
            return {"message": error}, 404

        # Check if the service is allowed for the worker's site
        allowed, error = check_service_allowed_for_site(worker.site_id, data['service_id'])
        if not allowed:
            return {"message": error}, 400

        # Check if worker-service relationship already exists
        unique, error = check_worker_service_exists(data['worker_id'], data['service_id'])
        if not unique:
            return {"message": error}, 400

        worker_service = WorkerHasServiceModel(data['worker_id'], data['service_id'])
        try:
            worker_service.save_to_db()
        except Exception as e:
            return {"message": f"An error occurred inserting the worker-service relationship: {str(e)}"}, 500

        return worker_service.json(), 201