"""Logical emulator manifest and synthetic restore canary, without logging identities."""

import hashlib
import json
import os
import sys
import urllib.request

import firebase_admin
from firebase_admin import auth
from google.auth.credentials import AnonymousCredentials
from google.cloud.firestore import Client

assert os.environ["GCLOUD_PROJECT"] == "demo-fullstyle"
assert os.environ["FIREBASE_AUTH_EMULATOR_HOST"].endswith(":9099")
assert os.environ["FIRESTORE_EMULATOR_HOST"].endswith(":8085")
firebase_admin.initialize_app(options={"projectId": "demo-fullstyle"})
client = Client(project="demo-fullstyle", credentials=AnonymousCredentials())
mode, canary = sys.argv[1:]
uid = "backup-" + canary
doc = client.collection("backup_canary").document(canary)
if mode == "seed":
    auth.create_user(
        uid=uid,
        email=uid + "@synthetic.invalid",
        password="SyntheticBackup123!",
        email_verified=True,
    )
    auth.set_custom_user_claims(uid, {"synthetic_backup": True})
    doc.set({"synthetic": True, "values": [1, True, "retained"]})
    doc.collection("nested").document("proof").set(
        {"payload": "nested-data", "bytes": b"test"}
    )
elif mode == "cleanup":
    doc.collection("nested").document("proof").delete()
    doc.delete()
    auth.delete_user(uid)
elif mode == "manifest":
    users = [
        {
            "uid": u.uid,
            "email": u.email,
            "verified": u.email_verified,
            "disabled": u.disabled,
            "claims": u.custom_claims,
            "hash": u.password_hash,
            "salt": u.password_salt,
            "providers": [
                {"uid": p.uid, "provider": p.provider_id, "email": p.email}
                for p in u.provider_data
            ],
        }
        for u in auth.list_users().iterate_all()
    ]
    documents = {}

    def walk(collection):
        for ref in collection.list_documents():
            snapshot = ref.get()
            if snapshot.exists:
                documents[ref.path] = snapshot.to_dict()
            for child in ref.collections():
                walk(child)

    for collection in client.collections():
        walk(collection)

    def digest(value):
        return hashlib.sha256(
            json.dumps(value, sort_keys=True, default=str).encode()
        ).hexdigest()

    result = {
        "auth_count": len(users),
        "auth_hash": digest(sorted(users, key=lambda u: u["uid"])),
        "document_count": len(documents),
        "firestore_hash": digest(documents),
    }
    print(json.dumps(result))
elif mode == "verify":
    user = auth.get_user(uid)
    assert user.custom_claims == {"synthetic_backup": True} and user.email_verified
    assert doc.get().to_dict() == {"synthetic": True, "values": [1, True, "retained"]}
    assert (
        doc.collection("nested").document("proof").get().to_dict()["bytes"] == b"test"
    )
    request = urllib.request.Request(
        "http://"
        + os.environ["FIREBASE_AUTH_EMULATOR_HOST"]
        + "/identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=synthetic-only",
        data=json.dumps(
            {
                "email": uid + "@synthetic.invalid",
                "password": "SyntheticBackup123!",
                "returnSecureToken": True,
            }
        ).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        assert json.load(response)["localId"] == uid
    print("PASS: restored login, claims, typed fields and nested document")
else:
    raise ValueError(mode)
