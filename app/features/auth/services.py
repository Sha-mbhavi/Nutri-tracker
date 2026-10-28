from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models import ActivityLog, Profile, User


def register_user(name, email, password):
    user = User(name=name, email=email)
    user.set_password(password)
    db.session.add(user)
    try:
        db.session.flush()
        db.session.add(Profile(user_id=user.id))
        db.session.add(ActivityLog(user_id=user.id, action="register", details="Account created"))
        db.session.commit()
        return user, None
    except IntegrityError:
        db.session.rollback()
        return None, "An account with that email already exists."
