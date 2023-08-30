import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

_cred = credentials.Certificate("./secret/typhoon-advisory-firebase-adminsdk-zpkxr-8431cceb31.json")
firebase_admin.initialize_app(_cred)
DB = firestore.client()