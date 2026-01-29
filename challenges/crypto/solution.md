# Solution : Rainbow Tables Challenge 🌈

## 📋 Objectif
Craquer 5 hash MD5 pour récupérer les mots de passe en clair et obtenir le flag.

---

## 🎯 Méthode 1 : Outils en ligne (Recommandé pour débutants)

### Étape 1 : Copier les hash
Depuis l'interface du challenge, copiez chaque hash MD5 un par un.

### Étape 2 : Utiliser CrackStation.net
1. Allez sur **https://crackstation.net**
2. Collez le hash dans le champ
3. Résolvez le CAPTCHA
4. Cliquez sur "Crack Hashes"

### Étape 3 : Résultats attendus

| ID | Username | Hash MD5 | Mot de passe |
|----|----------|----------|--------------|
| 1 | admin | `5f4dcc3b5aa765d61d8327deb882cf99` | **password** |
| 2 | alice | `e10adc3949ba59abbe56e057f20f883e` | **123456** |
| 3 | bob | `098f6bcd4621d373cade4e832627b4f6` | **test** |
| 4 | secret_agent | `8621ffdbc5698829397d97767ac13db3` | **Arsenal** |
| 5 | FLAG_HOLDER | `be6ff0f4ad08295f7ecd1acf9330fbc7` | **CTF{r41nb0w_t4bl3s_pwn3d}** |

### Étape 4 : Soumettre le flag
Une fois tous les hash crackés, soumettez le flag : `CTF{r41nb0w_t4bl3s_pwn3d}`

---

## 🛠️ Méthode 2 : Script Python (Pour comprendre le fonctionnement)

```python
#!/usr/bin/env python3
"""
Script pour démontrer l'attaque par rainbow table
ATTENTION : À usage éducatif uniquement !
"""

import hashlib

# Hash MD5 à craquer
hashes = {
    '5f4dcc3b5aa765d61d8327deb882cf99': 'admin',
    'e10adc3949ba59abbe56e057f20f883e': 'alice',
    '098f6bcd4621d373cade4e832627b4f6': 'bob',
    '8621ffdbc5698829397d97767ac13db3': 'secret_agent',
    'be6ff0f4ad08295f7ecd1acf9330fbc7': 'FLAG_HOLDER'
}

# Dictionnaire de mots de passe courants
wordlist = [
    'password', '123456', 'admin', 'test', 'qwerty',
    'Arsenal', 'Chelsea', 'Liverpool', 'United',
    'CTF{r41nb0w_t4bl3s_pwn3d}'
]

print("🌈 Rainbow Table Attack Simulation")
print("=" * 50)

for target_hash, username in hashes.items():
    print(f"\n[*] Cracking hash for {username}...")
    print(f"    Hash: {target_hash}")
    
    for word in wordlist:
        # Calculer le hash MD5 du mot
        md5_hash = hashlib.md5(word.encode()).hexdigest()
        
        # Comparer avec le hash cible
        if md5_hash == target_hash:
            print(f"    ✅ FOUND: {word}")
            break
    else:
        print(f"    ❌ Not found in wordlist")

print("\n" + "=" * 50)
print("✅ Attack completed!")
```

**Exécution :**
```bash
python3 rainbow_crack.py
```

---

## ⚙️ Méthode 3 : Hashcat (Outil professionnel)

### Installation
```bash
# Sur Ubuntu/Debian
sudo apt install hashcat

# Sur macOS
brew install hashcat
```

### Utilisation

**Étape 1 : Créer un fichier avec les hash**
```bash
cat > hashes.txt << EOF
5f4dcc3b5aa765d61d8327deb882cf99
e10adc3949ba59abbe56e057f20f883e
098f6bcd4621d373cade4e832627b4f6
8621ffdbc5698829397d97767ac13db3
be6ff0f4ad08295f7ecd1acf9330fbc7
EOF
```

**Étape 2 : Télécharger un dictionnaire (rockyou.txt)**
```bash
wget https://github.com/brannondorsey/naive-hashcat/releases/download/data/rockyou.txt
```

**Étape 3 : Lancer l'attaque**
```bash
# Mode 0 = MD5
# -a 0 = Attaque par dictionnaire
hashcat -m 0 -a 0 hashes.txt rockyou.txt
```

**Étape 4 : Voir les résultats**
```bash
hashcat -m 0 hashes.txt --show
```

### Attaque avec règles (pour le dernier hash)
```bash
# Ajouter des variations (majuscules, chiffres, symboles)
hashcat -m 0 -a 0 hashes.txt rockyou.txt -r /usr/share/hashcat/rules/best64.rule
```

---

## 🔍 Méthode 4 : John the Ripper

```bash
# Installer John
sudo apt install john

# Créer le fichier de hash au format John
cat > john_hashes.txt << EOF
admin:5f4dcc3b5aa765d61d8327deb882cf99
alice:e10adc3949ba59abbe56e057f20f883e
bob:098f6bcd4621d373cade4e832627b4f6
secret_agent:8621ffdbc5698829397d97767ac13db3
FLAG_HOLDER:be6ff0f4ad08295f7ecd1acf9330fbc7
EOF

# Lancer l'attaque
john --format=Raw-MD5 --wordlist=rockyou.txt john_hashes.txt

# Afficher les résultats
john --show --format=Raw-MD5 john_hashes.txt
```

---

## 📚 Explications techniques

### Qu'est-ce qu'un hash MD5 ?
MD5 (Message Digest 5) est une fonction de hachage cryptographique qui :
- Prend une entrée de taille variable
- Produit un hash de 128 bits (32 caractères hexadécimaux)
- Est à sens unique (impossible de retrouver l'entrée depuis le hash... en théorie)

**Exemple :**
```python
import hashlib
hashlib.md5(b"password").hexdigest()
# Résultat : 5f4dcc3b5aa765d61d8327deb882cf99
```

### Pourquoi MD5 est cassé ?
1. **Rapidité** : On peut calculer des milliards de hash par seconde
2. **Pas de sel** : Le même mot de passe donne toujours le même hash
3. **Rainbow tables** : Bases de données pré-calculées de millions de hash
4. **Collisions** : Deux entrées différentes peuvent donner le même hash

### Qu'est-ce qu'une rainbow table ?
Une rainbow table est une **base de données pré-calculée** de hash :
- Contient des millions de mots de passe courants et leurs hash MD5
- Permet de retrouver instantanément le mot de passe depuis le hash
- Rend MD5 obsolète pour stocker des mots de passe

### Comment se protéger ?
1. **Utiliser bcrypt, Argon2 ou scrypt** (algorithmes modernes)
2. **Ajouter un sel unique** par mot de passe
3. **Utiliser un pepper** (sel secret côté serveur)
4. **Imposer des mots de passe forts** (12+ caractères)
5. **Activer le 2FA** (authentification à deux facteurs)

---

## 🎯 FLAG Final

```
CTF{r41nb0w_t4bl3s_pwn3d}
```

**Comment l'obtenir :**
1. Cracker les 4 premiers hash avec CrackStation
2. Cracker le dernier hash (FLAG_HOLDER)
3. Le mot de passe du FLAG_HOLDER EST le flag
4. Le soumettre dans le formulaire final

---

## ⚠️ Note éthique

Ce challenge est à usage **éducatif uniquement**. Les techniques présentées ne doivent JAMAIS être utilisées sur des systèmes réels sans autorisation explicite.

**Utilisations légales :**
- ✅ Environnements CTF et challenges
- ✅ Audit de sécurité avec autorisation
- ✅ Tests sur vos propres systèmes
- ✅ Recherche académique

**Utilisations illégales :**
- ❌ Attaquer des sites web sans permission
- ❌ Accéder à des comptes qui ne vous appartiennent pas
- ❌ Voler des données personnelles

La cybersécurité est une **responsabilité**, pas un jeu. Apprenez pour protéger, pas pour nuire.

---

## 📖 Ressources complémentaires

- **OWASP Password Storage Cheat Sheet** : https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html
- **CrackStation** : https://crackstation.net
- **Have I Been Pwned** : https://haveibeenpwned.com
- **Hashcat Documentation** : https://hashcat.net/wiki/
- **John the Ripper** : https://www.openwall.com/john/

---

**Bon hacking éthique ! 🌈🔓**