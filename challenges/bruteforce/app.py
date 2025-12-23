from flask import Flask, render_template, request, session
import random

app = Flask(__name__)
app.secret_key = 'bruteforce_secret_key_ctf'

# Code secret aléatoire généré à chaque démarrage du conteneur
# Pour le CTF, on le fixe pour que tous les utilisateurs aient le même
SECRET_CODE = "7394"

@app.route('/', methods=['GET', 'POST'])
def vault():
    message = None
    flag = None
    attempts = session.get('attempts', 0)
    
    if request.method == 'POST':
        user_code = request.form.get('code', '').strip()
        attempts += 1
        session['attempts'] = attempts
        
        # Vérification du code
        if user_code == SECRET_CODE:
            flag = "CTF{Brut3F0rc3_M4st3r_7394}"
            message = f"🎉 Coffre-fort déverrouillé ! Vous avez trouvé le code en {attempts} tentative(s)."
            # Reset des tentatives
            session['attempts'] = 0
        else:
            message = f"❌ Code incorrect. Tentative #{attempts}"
            
            # Petit indice après 20 tentatives
            if attempts == 20:
                message += " | 💡 Indice : Le code contient 4 chiffres (0000-9999)"
            elif attempts == 50:
                message += " | 💡 Indice : Essayez d'automatiser avec un script !"
    
    return render_template('vault.html', message=message, flag=flag, attempts=attempts)

@app.route('/reset')
def reset():
    """Réinitialiser les tentatives"""
    session['attempts'] = 0
    return render_template('vault.html', message="✨ Compteur de tentatives réinitialisé.", attempts=0)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004, debug=True)