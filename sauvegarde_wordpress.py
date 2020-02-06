#!/usr/bin/python3
# -*- coding: utf8 -*-

"""Script pour sauvegarder un site Wordpress et sa base de donnees Mysql via sftp.
Les sauvegardes sont archivees dans un fichier .tar.gz avec la date du jour.
Les archives perimees sont supprimees.

Pour <import pysftp> il faut installer le module au prealable : pip3 install pysftp

Auteur: W1sm3rill
Contact: wismerillopenclassroom@gmail.com
"""


###########
# Modules #
###########

import os
import sys
import re
import subprocess
import tarfile
import datetime
import time
import shutil
import smtplib
import logging
import configparser
import pysftp


#############
# Variables #
#############

# Lecture du fichier informations et extraction des variables.
if os.path.isfile('informations'):
    config = configparser.RawConfigParser()
    config.read('informations')
    MAIL = config.get('MAIL', 'mail')
    MDP_MAIL = config.get('MAIL', 'mdp')

    SFTP_HOST = config.get('SFTP', 'host')
    SFTP_USER = config.get('SFTP', 'user')
    SFTP_PASSWD = config.get('SFTP', 'mdp')

    DOSSIER_SAUVEGARDE = config.get('VARIABLES', 'sauvegarde')
    DOSSIER_WORDPRESS = config.get('VARIABLES', 'wordpress')
    EXPIRATION = config.get('VARIABLES', 'expiration')
else:
    print('Vérifier la présence du fichier <informations>')


#######
# LOG #
#######

logging.basicConfig(filename='sauvegarde_wordpress.log', level=logging.DEBUG,\
      format='%(asctime)s -- %(name)s -- %(levelname)s -- %(message)s')


########################
# Sauvegarde Wordpress #
########################

def sauvegarde_wordpress():
    """Sauvegarde le dossier wordpress sur le serveur hote via sftp.

    Creer un dossier de sauvegarde wordpress sur le serveur hote,
    Se connecte au serveur distant,
    Telecharge le dossier wordpress dans le dossier de sauvegarde wordpress du serveur hote.

    Retourne un str de l emplacement du dossier de sauvergarde wordpress.
    """
    logging.info('Sauvegarde de Wordpress')

    try:
        if not os.path.exists(DOSSIER_SAUVEGARDE+'/wordpress'):
            os.makedirs(DOSSIER_SAUVEGARDE+'/wordpress')
        sauvegarde = DOSSIER_SAUVEGARDE+'/wordpress'

        with pysftp.Connection(SFTP_HOST, username=SFTP_USER, password=SFTP_PASSWD) as sftp:
            sftp.get_d(DOSSIER_WORDPRESS, sauvegarde)
            sftp.close()
        return sauvegarde

    except AuthenticationException as echec_authentication:
        # Probleme d authentification au serveur.
        logging.error(echec_authentication)
        envoi_mail('Erreur Sauvegarde de Wordpress')
        sys.exit(1)

    except PermissionError as permission_refuse:
        # Permission refuse.
        logging.error(permission_refuse)
        envoi_mail('Erreur Sauvegarde de Wordpress')
        sys.exit(1)

    except Exception as erreur_inconnue:
        # Tout autre erreur.
        logging.error(erreur_inconnue)
        envoi_mail('Erreur Sauvegarde de Wordpress')
        sys.exit(1)


#########################################################################
# Recuperation des informations de connexion a la BDD via wp-config.php #
#########################################################################

def info_bdd(sauvegarde):
    """Analyse et recupere des valeurs dans wp-config.php.

    Prend comme argument le dossier de sauvegarde wordpress.
    Lis le fichier wp-config.php et recupere les informations.

    Retourne dans un dictionnaire les cles/valeurs.
    """
    logging.info('Analyse des informations de connexion dans wp-config.php')

    try:
        fichier = os.path.normpath(sauvegarde+'/var/www/wordpress/wp-config.php') # Evite les séparateurs redondants.
        with open(fichier) as file:
            contenu = file.read()
            regex_db = r'define\(\s*?\'DB_NAME\'\s*?,\s*?\'(?P<DB>.*?)\'\s*?\);'
            regex_user = r'define\(\s*?\'DB_USER\'\s*?,\s*?\'(?P<USER>.*?)\'\s*?\);'
            regex_pass = r'define\(\s*?\'DB_PASSWORD\'\s*?,\s*?\'(?P<PASSWORD>.*?)\'\s*?\);'
            regex_host = r'define\(\s*?\'DB_HOST\'\s*?,\s*?\'(?P<HOST>.*?)\'\s*?\);'
            database = re.search(regex_db, contenu).group('DB')
            user = re.search(regex_user, contenu).group('USER')
            password = re.search(regex_pass, contenu).group('PASSWORD')
            host = re.search(regex_host, contenu).group('HOST')
        return {'database':database, 'user':user, 'password':password, 'host':host}

    except FileNotFoundError as fichier_introuvable:
        # Le fichier est introuvable.
        logging.error(fichier_introuvable)
        envoi_mail('Erreur Analyse wp-config')
        sys.exit(1)

    except PermissionError as permission_refuse:
        # Permisson refuse.
        logging.error(permission_refuse)
        envoi_mail('Erreur Analyse wp-config')
        sys.exit(1)

    except AttributeError as fichier_corrompu:
        # Le fichier est corrompu.
        logging.error(fichier_corrompu)
        envoi_mail('Erreur Analyse wp-config')
        sys.exit(1)

    except UnicodeEncodeError as erreur_analyse:
        # Erreur dans l analyse du fichier.
        logging.error(erreur_analyse)
        envoi_mail('Erreur Analyse wp-config')
        sys.exit(1)

    except Exception as erreur_inconnue:
        # Tout autre erreur.
        logging.error(erreur_inconnue)
        envoi_mail('Erreur Analyse wp-config')
        sys.exit(1)


########################
# Sauvegarde de la BDD #
########################

def sauvegarde_bdd(informations):
    """Sauvegarde la base de donnees mysql.

    Prend comme argument le dictionnaire de info_bdd.
    Creer un dossier de sauvegarde bdd sur le serveur hote,
    Utilise le dictionnaire pour se connecter a mysql,
    Sauvegarde sur le dossier de sauvegarde bdd.

    Retourne un str de l emplacement du fichier de sauvegarde bdd.
    """
    logging.info('Sauvegarde de la Base de donnee')

    try:
        if not os.path.exists(DOSSIER_SAUVEGARDE+'/bdd'):
            os.makedirs(DOSSIER_SAUVEGARDE+'/bdd')

        user = informations['user']
        password = informations['password']
        host = SFTP_HOST
        database = informations['database']
        dumpname = os.path.normpath(os.path.join( # Evite toute erreur de chemin.
            DOSSIER_SAUVEGARDE+'/bdd', informations['database'] + '.sql'))
        cmd = "mysqldump  -u {} -p'{}' -h {} {}  > {}".format(
            user, password, host, database, dumpname).encode(encoding="utf8")
        subprocess.check_output(cmd, shell=True) # Lance la commande et renvoie sa sortie.
        return dumpname

    except subprocess.CalledProcessError as echec_mysqldump:
        # Probleme de connexion a msql.
        logging.error(echec_mysqldump)
        envoi_mail('Erreur Sauvegarde BDD')
        sys.exit(1)

    except UnicodeEncodeError as info_nonascii:
        # Probleme dans l encodage, un caractere unicode non ascii.
        logging.error(info_nonascii)
        envoi_mail('Erreur Sauvegarde BDD')
        sys.exit(1)

    except Exception as erreur_inconnue:
        # Tout autre erreur.
        logging.error(erreur_inconnue)
        envoi_mail('Erreur Sauvegarde BDD')
        sys.exit(1)


#########################
# Creation de l archive #
#########################

def creation_archive(sauvegarde, dumpname):
    """Creer une archive des dossiers de sauvegarde.

    Prend comme argument le dossier de sauvegarde de wordpress et de la bdd.
    Compresse les dossiers dans un fichier .tar.gz a la date du jour.
    Supprime les dossiers de sauvegarde wordpress et bdd.

    Retourne un str de l emplacement de l archive.
    """
    logging.info('Archivage des sauvegardes wordpress et mysql')

    try:
        time_tag = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        dir_name = os.path.basename(sauvegarde.rstrip('/')) # Supprime les /.
        archive_name = os.path.normpath(DOSSIER_SAUVEGARDE+'/'+dir_name+'-'+time_tag+'.tar.gz')

        with tarfile.open(archive_name, "w:gz") as tar:
            tar.add(sauvegarde)
            tar.add(dumpname, arcname="sql.dump") # arcname : le nom de l archive.

        if os.path.exists(sauvegarde):
            shutil.rmtree(sauvegarde)
        if os.path.exists(DOSSIER_SAUVEGARDE+'/bdd'):
            shutil.rmtree(DOSSIER_SAUVEGARDE+'/bdd')
        return archive_name

    except FileNotFoundError as fichier_introuvable:
        # Le fichier est introuvable.
        logging.error(fichier_introuvable)
        envoi_mail('Erreur Archivage')
        sys.exit(1)

    except PermissionError as permission_refuse:
        # Permission refuse.
        logging.error(permission_refuse)
        envoi_mail('Erreur Archivage')
        sys.exit(1)

    except Exception as erreur_inconnue:
        # Tout autre erreur.
        logging.error(erreur_inconnue)
        envoi_mail('Erreur Archivage')
        sys.exit(1)


####################################
# Suppression d anciennes archives #
####################################

def suppression_anciennes_archives(days=14):
    """Supprime les anciennes archives.

    Prend comme argument le nombre de jour de peremption de l archive,
    Compare la date du jour et la date du fichier,
    Si superieur au nombre de jour specifie, supprime le fichier.
    """
    logging.info('Suppression des anciennes archives')

    try:
        now = time.time()
        for file in os.listdir(DOSSIER_SAUVEGARDE): # Contenu du repertoire.
            file_save = os.path.join(DOSSIER_SAUVEGARDE, file)
            if os.stat(file_save).st_mtime < now - float(days) * 86400 and os.path.isfile(file_save):
                os.remove(file_save)

    except Exception as erreur_inconnue:
        # Tout autre erreur.
        logging.error(erreur_inconnue)
        envoi_mail('Erreur Suppression ancienne archive')
        sys.exit(1)


#########
# EMAIL #
#########

def envoi_mail(erreur):
    """Envoi un mail.

    Prend comme argument l erreur survenu lors du deroulement du script.    
    Envoi un mail pour avertir l admin.
    """
    logging.info('Envoi d un email')

    try:
        serveur = smtplib.SMTP('smtp.gmail.com', 587) # Connexion au serveur.
        serveur.starttls() # Specification de la securisation.
        serveur.login(MAIL, MDP_MAIL) # Authentification.
        message = erreur # Message a envoyer.
        serveur.sendmail(MAIL, MAIL, message) # Envoie du message.
        serveur.quit() # Deconnexion du serveur.

    except Exception as erreur_inconnue:
        # Tout autre erreur.
        logging.error(erreur_inconnue)
        sys.exit(1)


#######################
# Lancement du script #
#######################

if os.path.exists(DOSSIER_SAUVEGARDE):
    print('==> Sauvergarde commencée <==')

    # Appel de la fonction sauvegarde_wordpress dans la variable SAUVEGARDE.
    SAUVEGARDE = sauvegarde_wordpress()

    # Appel de la fonction info_bdd avec l argument SAUVEGARDE dans la variable INFORMATIONS.
    INFORMATIONS = info_bdd(SAUVEGARDE)

    # Appel de la fonction sauvegarde_bdd avec l argument INFORMATIONS dans la variable DUMPNAME.
    DUMPNAME = sauvegarde_bdd(INFORMATIONS)

    # Appel de la fonction creation_archive avec l argument SAUVEGARDE et DUMPNAME.
    creation_archive(SAUVEGARDE, DUMPNAME)

    # Appel de la fonction suppression_anciennes_archives avec l argument EXPIRATION.
    suppression_anciennes_archives(EXPIRATION)

    print('==> Sauvegarde terminée <==')

else:
    print('Le dossier de sauvegarde:', DOSSIER_SAUVEGARDE, 'est inexistant')
    print('Vérifier la variable DOSSIER_SAUVEGARDE')
    logging.error('DOSSIER_SAUVEGARDE inexistant')
