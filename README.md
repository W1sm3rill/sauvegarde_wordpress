Script pour sauvegarder sur un serveur distant,
un site Wordpress et une base de donnee Mysql via sftp.
Les sauvegardes sont archivées dans un fichier ".tar.gz" avec la date du jour. 
Les archives périmées sont suprimeés.

Pour <import pysftp> il faut installer le module au préalable via
pip3 install pysftp

Le script et le fichier "informations" doivent être dans le même dossier.
"informations" contient les variables nécessaire au script :

[MAIL]
mail: vôtre adresse gmail
mdp: le mot de passe de l'adresse gmail

[SFTP]
host: l'IP du serveur web
user: l'utilisateur du serveur web
mdp: le mot de passe de l'utilisateur

[VARIABLES]
sauvegarde: le chemin du dossier de sauvegarde de la machine hôte
temporaire: le chemin du dossier de sauvegarde temporaire de la machine distant
wordpress: le chemin du dossier wordpress
expiration: péremption des archives exprimés en jour