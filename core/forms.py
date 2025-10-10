# ------------------------------
# CyberCampus CTF - Formulaires Flask-WTF
# ------------------------------

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length

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
        Length(min=6, message="Le mot de passe doit contenir au moins 6 caractères.")
    ])
    
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

