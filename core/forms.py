# ------------------------------
# CyberCampus CTF - Formulaires Flask-WTF
# ------------------------------

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
import re

# Formulaire d'inscription
class RegisterForm(FlaskForm):
    pseudo = StringField("Pseudo", validators=[
        DataRequired(message="Le pseudo est obligatoire."),
        Length(min=3, max=50, message="Le pseudo doit contenir entre 3 et 50 caractères.")
    ])
    
    email = StringField("Email", validators=[
        DataRequired(message="L'email est obligatoire."),
        Email(message="Veuillez entrer un email valide.")
    ])
    
    password = PasswordField("Mot de passe", validators=[
        DataRequired(message="Le mot de passe est obligatoire."),
        Length(min=8, message="Le mot de passe doit contenir au moins 8 caractères.")
    ])

    def validate_password(self, field):
        """Validation personnalisée du mot de passe"""
        password = field.data
        if not re.search(r'\d', password):
            raise ValidationError("Le mot de passe doit contenir au moins un chiffre.")
        if not re.search(r'[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\\/~`]', password):
            raise ValidationError("Le mot de passe doit contenir au moins un caractère spécial.")
    
    confirm_password = PasswordField("Confirmer le mot de passe", validators=[
        DataRequired(message="Veuillez confirmer votre mot de passe."),
        EqualTo('password', message="Les mots de passe ne correspondent pas.")
    ])
    
    submit = SubmitField("Créer mon compte")

# Formulaire de connexion
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[
        DataRequired(message="L'email est obligatoire."),
        Email(message="Veuillez entrer un email valide.")
    ])

    password = PasswordField("Mot de passe", validators=[
        DataRequired(message="Le mot de passe est obligatoire.")
    ])

    submit = SubmitField("Se connecter")

