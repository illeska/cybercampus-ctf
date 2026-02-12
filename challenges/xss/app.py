from flask import Flask, render_template, request, session
from datetime import datetime
import os

app = Flask(__name__)

# Clé secrète nécessaire pour utiliser les sessions (stockage côté client)
app.secret_key = os.urandom(24) 

@app.route('/', methods=['GET', 'POST'])
def index():
    flag = None
    
    # On initialise la liste des commentaires dans la session si elle n'existe pas
    if 'my_comments' not in session:
        session['my_comments'] = []
    
    if request.method == 'POST':
        name = request.form.get('name', 'Anonyme')
        comment = request.form.get('comment', '')
        
        # Détection du XSS (inchangé)
        if '<script>' in comment.lower() or 'onerror' in comment.lower():
            flag = "CTF{XSS_r3fl3ct3d_pwn3d}"
        
        # On ajoute le commentaire UNIQUEMENT à la session de l'utilisateur actuel
        new_comment = {
            'name': name,
            'comment': comment,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }
        
        # Mise à jour de la session
        current_comments = session['my_comments']
        current_comments.append(new_comment)
        session['my_comments'] = current_comments
        session.modified = True # Force Flask à enregistrer la modification
    
    # On affiche uniquement les commentaires de la session actuelle
    return render_template('comments.html', comments=session['my_comments'], flag=flag)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)