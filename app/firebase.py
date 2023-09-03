import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

_cred = credentials.Certificate("/app/secret/secret.json")
firebase_admin.initialize_app(_cred)
DB = firestore.client()