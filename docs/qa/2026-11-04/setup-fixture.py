"""Optional local QA preconditions; this does not test business creation in the UI."""

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner-email", required=True)
    parser.add_argument(
        "--apply", action="store_true", help="Create synthetic rows; default is dry run"
    )
    options = parser.parse_args()
    email = options.owner_email
    if not email.startswith("qa_owner_") or not email.endswith("@synthetic.invalid"):
        parser.error("Use a QA owner registered in the UI at qa_owner_*@synthetic.invalid")
    if not options.apply:
        print("DRY RUN: would create one site, category, service, worker and seven schedules.")
        print("Register the owner in the UI and activate its synthetic subscription first.")
        return

    from start_local import preflight

    preflight()
    output = ROOT / ".quality/qa-reproduction-fixture.json"
    if not output.resolve().is_relative_to(ROOT) or output.exists():
        raise ValueError("Output must be a new private file within this checkout")
    code = (
        "EMAIL="
        + repr(email)
        + "\n"
        + """
import json
from datetime import time
from config.db_config import db
from config.server_config import create_app
from models.user_model import UserModel
from models.manager_model import ManagerModel
from models.site_model import SiteModel
from models.worker_model import WorkerModel
from models.category_model import CategoryModel
from models.service_model import ServiceModel
from models.detail_model import DetailModel
from models.availability_model import AvailabilityModel
from models.site_has_category_model import SiteHasCategoryModel
from models.worker_has_service_model import WorkerHasServiceModel

app = create_app()
with app.app_context():
    owner = UserModel.query.filter_by(email=EMAIL).one()
    manager = db.session.get(ManagerModel, owner.id)
    assert manager and manager.subscriptionactive, "Activate the synthetic subscription first"
    assert SiteModel.query.filter_by(manager_id=owner.id).count() == 0, "Owner already has a site"
    site = SiteModel(id=None, name='Sede QA FullStyle', address='Direccion sintetica QA, Bogota',
                     phone='3000000000', manager_id=owner.id, photos=[])
    category = CategoryModel(name='Categoria QA FullStyle')
    db.session.add_all([site, category]); db.session.flush()
    worker = WorkerModel(name='Profesional QA FullStyle', site_id=site.id)
    service = ServiceModel(category_id=category.id, name='Corte QA FullStyle')
    db.session.add_all([worker, service]); db.session.flush()
    db.session.add(DetailModel(site_id=site.id, service_id=service.id,
        description='Servicio sintetico para QA de interfaz', price=20000, duration=30, photos=[]))
    db.session.add(SiteHasCategoryModel(site.id, category.id))
    db.session.add(WorkerHasServiceModel(worker.id, service.id))
    for day in ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']:
        db.session.add(AvailabilityModel(worker_id=worker.id, weekday=day,
            starttime=time(9), endtime=time(17)))
    db.session.commit()
    print(json.dumps({'synthetic_only':True, 'site_id':site.id, 'worker_id':worker.id,
                     'service_id':service.id, 'category_id':category.id}))
"""
    )
    result = subprocess.run(
        ["docker", "exec", "-i", "fullstyle-portfolio-backend-1", "python", "-"],
        input=code.encode(),
        capture_output=True,
        check=True,
    )
    fixture = json.loads(result.stdout.decode().strip().splitlines()[-1])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(fixture, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(fixture))


if __name__ == "__main__":
    main()
