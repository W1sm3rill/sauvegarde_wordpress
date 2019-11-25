#!/usr/bin/python3
# -*- coding: utf8 -*-

"""
Script pour sauvegarder sur un serveur distant, un site Wordpress et une base de donnee Mysql
via sftp.

OS testé : Ubuntu 19.10 Desktop / Server
           Ubuntu 18.04 Desktop / Server
"""


###########
# Modules #
###########

import os
import re
import subprocess
import tarfile
import datetime
import time
import shutil
import smtplib
import logging
import pysftp


#############
# Variables #
#############

MAIL = 'xxx@gmail.com'
MDP_MAIL = 'xxx'

SFTP_HOST = '192.168.122.232'
SFTP_USER = 'wismerill'
SFTP_PASSWD = 'wismerill'

DOSSIER_SAUVEGARDE = '/home/wismerill/sauvegarde' # Serveur hote.
DOSSIER_TEMPORAIRE = '/home/wismerill/sauvegarde' # Serveur distant.
DOSSIER_WORDPRESS = '/var/www/wordpress'
EXPIRATION = 14 # Duree en jour d expiration des archives.


#######
# LOG #
#######

logging.basicConfig(filename='sauvegarde_wordpress.log', level=logging.DEBUG,\
      format='%(asctime)s -- %(name)s -- %(levelname)s -- %(message)s')


########################
# Sauvegarde Wordpress #
########################

def sauvegarde_wordpress():
    """ Creer un dossier de sauvegarde, creer un dossier temporaire,
    copie le dossier wordpress dans le dossier temporaire,
    telecharge le dossier sur le serveur hote et supprime le dossier temporaire.
    Retourne le dossier de sauvegarde wordpress.
    """
    if not os.path.exists(DOSSIER_SAUVEGARDE+'/wordpress'):
        os.makedirs(DOSSIER_SAUVEGARDE+'/wordpress')
    sauvegarde = DOSSIER_SAUVEGARDE+'/wordpress'

    with pysftp.Connection(SFTP_HOST, username=SFTP_USER, password=SFTP_PASSWD) as sftp:
        if not sftp.exists(DOSSIER_TEMPORAIRE):
            sftp.makedirs(DOSSIER_TEMPORAIRE)
        sftp.execute('cp -r DOSSIER_WORDPRESS DOSSIER_TEMPORAIRE')
        sftp.get_d(DOSSIER_TEMPORAIRE, DOSSIER_SAUVEGARDE+'/wordpress')
        sftp.execute('rm -R DOSSIER_TEMPORAIRE')
        sftp.close()

    return sauvegarde


###########################################################################
# Recuperation des informations de connexion a la BDD via wp-config.php #
###########################################################################

def info_bdd(sauvegarde):
    """ Prend comme argument le dossier de sauvegarde wordpress,
    recupere les informations de connexion a Mysql dans le fichier wp-config.php
    et le retourne dans un dictionnaire.
    """
    fichier = os.path.normpath(sauvegarde+'/wp-config.php')
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


########################
# Sauvegarde de la BDD #
########################

def sauvegarde_bdd(informations):
    """ Prend comme argument le dictionnaire de info_bdd.
    Creer un dossier de sauvegarde, utilise le dictionnaire pour se connecter
    a mysql et sauvegarde sur le dossier de sauvegarde.
    Retourne le dossier de sauvegarde de la bdd.
    """
    if not os.path.exists(DOSSIER_SAUVEGARDE+'/bdd'):
        os.makedirs(DOSSIER_SAUVEGARDE+'/bdd')

    user = informations['user']
    password = informations['password']
    host = informations['host']
    database = informations['database']
    dumpname = os.path.normpath(os.path.join(
        DOSSIER_SAUVEGARDE+'/bdd', informations['database'] + '.sql'))
    cmd = "mysqldump  -u {} -p'{}' -h {} {}  > {}".format(
        user, password, host, database, dumpname).encode(encoding="utf8")
    subprocess.check_output(cmd, shell=True)

    return dumpname


#########################
# Creation de l archive #
#########################

def creation_archive(sauvegarde, dumpname):
    """ Prend comme argument le dossier de sauvegarde de wordpress et de la bdd.
    Compresse les dossiers dans un fichier .tar.gz a la date du jour.
    Supprime les dossiers de sauvegarde wordpress et bdd.
    Retourne le nom de l archive.
    """
    time_tag = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    dir_name = os.path.basename(sauvegarde.rstrip('/'))
    archive_name = os.path.normpath(DOSSIER_SAUVEGARDE+'/'+dir_name+'-'+time_tag+'.tar.gz')

    with tarfile.open(archive_name, "w:gz") as tar:
        tar.add(sauvegarde)
        tar.add(dumpname, arcname="sql.dump")

    if os.path.exists(sauvegarde):
        shutil.rmtree(sauvegarde)

    if os.path.exists(dumpname):
        shutil.rmtree(dumpname)

    return archive_name


####################################
# Suppression d anciennes archives #
####################################

def suppression_anciennes_archives(days=14):
    """ Prend comme argument le nombre de jour de peremption de l archive,
    compare la date du jour et la date du fichier, si superieur au nombre de
    jour specifie, suprime le fichier.
    """
    now = time.time()
    for file in os.listdir(DOSSIER_SAUVEGARDE):
        file_location = os.path.join(DOSSIER_SAUVEGARDE, file)
        if os.stat(file_location).st_mtime < now - days * 86400 and os.path.isfile(file_location):
            os.remove(file_location)



#########
# EMAIL #
#########

def envoi_mail(erreur):
    """ Prend comme argument l erreur survenu lors du deroulement du script.
    Envoi un mail pour avertir l admin.
    """
    serveur = smtplib.SMTP('smtp.gmail.com', 587)
    serveur.starttls()
    serveur.login(MAIL, MDP_MAIL)
    message = erreur
    serveur.sendmail(MAIL, MAIL, message)
    serveur.quit()


#######################
# Lancement du script #
#######################

SAUVEGARDE = sauvegarde_wordpress()
INFORMATIONS = info_bdd(SAUVEGARDE)
DUMPNAME = sauvegarde_bdd(INFORMATIONS)
creation_archive(SAUVEGARDE, DUMPNAME)
suppression_anciennes_archives(EXPIRATION)
