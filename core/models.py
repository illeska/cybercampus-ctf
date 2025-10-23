# ------------------------------
# CyberCampus CTF - Modèles de la base de données
# ------------------------------

from datetime import datetime
import hashlib
from core import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    __tablename__ = "User"

    id = db.Column(db.Integer, primary_key=True)
    pseudo = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="user")
    created_at = db.Column(db.DateTime, default=db.func.now())

    submissions = db.relationship("Submission", backref="user", lazy="dynamic")
    scoreboard = db.relationship("Scoreboard", backref="user", uselist=False)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def getScore(self) -> int:
        if self.scoreboard:
            return self.scoreboard.points_total
        total = 0
        for s in self.submissions.filter_by(correct=True).all():
            if s.challenge and s.challenge.points:
                total += s.challenge.points
        return total


class Challenge(db.Model):
    __tablename__ = "Challenge"

    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    points = db.Column(db.Integer, default=0)
    actif = db.Column(db.Boolean, default=True)

    submissions = db.relationship("Submission", backref="challenge", lazy="dynamic")
    flag = db.relationship("Flag", backref="challenge", uselist=False, cascade="all, delete-orphan")

    def activer(self):
        self.actif = True
        db.session.commit()

    def desactiver(self):
        self.actif = False
        db.session.commit()


class Flag(db.Model):
    __tablename__ = "Flag"

    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey("Challenge.id"), nullable=False)
    flag_hash = db.Column(db.String(255), nullable=False)

    @staticmethod
    def _hash(flag_plain: str) -> str:
        return hashlib.sha256(flag_plain.encode("utf-8")).hexdigest()

    def setFlag(self, flag_plain: str):
        self.flag_hash = self._hash(flag_plain)

    def verifierFlag(self, flag_soumis: str) -> bool:
        return self.flag_hash == self._hash(flag_soumis)


class Submission(db.Model):
    __tablename__ = "Submission"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("User.id"), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey("Challenge.id"), nullable=False)
    flag_soumis = db.Column(db.String(255), nullable=False)
    correct = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def verifier(self) -> bool:
        if not self.challenge or not self.challenge.flag:
            return False
        return self.challenge.flag.verifierFlag(self.flag_soumis)

    def enregistrer(self) -> bool:
        self.correct = self.verifier()
        self.timestamp = datetime.utcnow()  
        db.session.add(self)
        db.session.commit()

        if self.correct:
            from core.models import Scoreboard, Submission 
            sb = Scoreboard.query.filter_by(user_id=self.user_id).first()
            if not sb:
                sb = Scoreboard(user_id=self.user_id, points_total=0)
                db.session.add(sb)
                db.session.commit()

            already = Submission.query.filter_by(
                user_id=self.user_id, challenge_id=self.challenge_id, correct=True
            ).count()

            if already <= 1:
                sb.points_total = (sb.points_total or 0) + (self.challenge.points or 0)
                db.session.commit()

        return self.correct


class Scoreboard(db.Model):
    __tablename__ = "Scoreboard"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("User.id"), nullable=False)
    points_total = db.Column(db.Integer, default=0)

    @staticmethod
    def calculerScore(user_id: int) -> int:
        total = 0
        subs = Submission.query.filter_by(user_id=user_id, correct=True).all()
        for s in subs:
            if s.challenge and s.challenge.points:
                total += s.challenge.points
        sb = Scoreboard.query.filter_by(user_id=user_id).first()
        if not sb:
            sb = Scoreboard(user_id=user_id, points_total=total)
            db.session.add(sb)
        else:
            sb.points_total = total
        db.session.commit()
        return total

    @staticmethod
    def afficherClassement(limit: int = 50):
        return db.session.query(Scoreboard, User).join(User, Scoreboard.user_id == User.id) \
            .order_by(Scoreboard.points_total.desc()).limit(limit).all()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
