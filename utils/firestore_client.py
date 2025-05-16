from google.cloud import firestore
import os

# Inisialisasi Firestore dengan service account JSON
db = firestore.Client.from_service_account_json("aplikasilogin-70f9b-0dedec8143e4.json")


