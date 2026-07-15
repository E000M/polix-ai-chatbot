# backend/auth.py

from flask import Blueprint, request, jsonify

from firebase_admin import auth

from datetime import datetime

import logging

auth_routes = Blueprint("auth_routes", __name__)

logger = logging.getLogger("auth_routes")

# ==========================================
# LOGIN
# ==========================================

@auth_routes.route("/login", methods=["POST"])
def login():

    data = request.get_json(silent=True) or {}

    token = data.get("idToken") or data.get("token")

    if not token:

        return jsonify({
            "status": "error",
            "message": "No token provided"
        }), 400

    try:

        # ======================================
        # VERIFY FIREBASE TOKEN
        # ======================================

        decoded = auth.verify_id_token(token)

        email = decoded.get("email")

        uid = decoded.get("uid")

        name = decoded.get("name", "Unknown User")

        # ======================================
        # FIRESTORE IMPORT + INIT
        # ======================================

        from firebase_admin import firestore

        db = firestore.client()

        # ======================================
        # SAVE USER TO FIREBASE
        # ======================================

        users_ref = db.collection("users")

        existing_user = users_ref.where(
            "email",
            "==",
            email
        ).limit(1).stream()

        existing_user = list(existing_user)

        current_time = datetime.now().strftime(
            "%d %B %Y - %H:%M"
        )

        # USER EXISTS → UPDATE LOGIN TIME

        if existing_user:

            doc_id = existing_user[0].id

            users_ref.document(doc_id).update({

                "last_login": current_time

            })

        # NEW USER → CREATE USER

        else:

            users_ref.add({

                "name": name,
                "email": email,
                "uid": uid,
                "last_login": current_time

            })

        logger.info(
            f"Successful login for uid={uid} email={email}"
        )

        return jsonify({

            "status": "success",
            "email": email,
            "uid": uid,
            "name": name

        })

    except Exception as e:

        print("FIREBASE ERROR:", e)

        return jsonify({
            "error": "User not found"
        }), 404