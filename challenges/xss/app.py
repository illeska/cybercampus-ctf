from flask import Flask, render_template, request
from datetime import datetime

app = Flask(__name__)

comments = []

@app.route('/', methods=['GET', 'POST'])
def index():
    flag = None
    
    if request.method == 'POST':
        name = request.form.get('name', 'Anonyme')
        comment = request.form.get('comment', '')
        
        # Détection si le XSS a été exploité avec succès
        if '<script>' in comment.lower() or 'onerror' in comment.lower():
            flag = "CTF{XSS_r3fl3ct3d_pwn3d}"
        
        comments.append({
            'name': name,
            'comment': comment,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        })
    
    return render_template('comments.html', comments=comments, flag=flag)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)