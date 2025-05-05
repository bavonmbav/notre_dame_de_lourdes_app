import sqlite3
import os
import json
import bcrypt # type: ignore
from pathlib import Path  # Ajout de l'importation manquante
from shutil import copyfile  # Import nécessaire pour copier les fichiers
import threading
import sys
import shutil


db_lock = threading.Lock()
# DB_NAME = "laboratoire.db"

def get_appdata_db_path():
    app_dir = Path(os.getenv("APPDATA")) / "tarifs"
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir / "laboratoire.db"


def ensure_database_exists():
    db_path = get_appdata_db_path()
    if not db_path.exists():
        # Copier le fichier de base de données par défaut
        default_db_path = Path(__file__).parent / "laboratoire.db"
        if not default_db_path.exists():
            raise FileNotFoundError(f"Le fichier de base de données par défaut est introuvable : {default_db_path}")
        shutil.copy(default_db_path, db_path)
    return db_path


class Database:

    def __init__(self, db_name="laboratoire.db"):
        db_path = ensure_database_exists()
        print(f"Chemin de la base de données : {db_path}")
        self.conn = sqlite3.connect(db_path, timeout=10)  # Timeout ajouté
        self.cursor = self.conn.cursor()
        self.create_table()
        self.conn.commit()

    def execute_query(self, query, params=()):
        with db_lock:  # Utiliser un verrou pour synchroniser l'accès
            try:
                self.cursor.execute(query, params)
                self.conn.commit()
            except sqlite3.Error as e:
                print(f"Erreur lors de l'exécution de la requête : {e}")
                raise

    def create_table(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS examens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                prix_cach INTEGER NOT NULL,
                prix_abonner INTEGER NOT NULL
            )
            """
        )

        self.cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS factures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom_patient TEXT NOT NULL,
                    nom_demandeur TEXT NOT NULL,
                    societe TEXT,
                    fonction TEXT,
                    service TEXT,
                    type_client TEXT CHECK(type_client IN ('abonne', 'cache')) NOT NULL,
                    examens TEXT NOT NULL,  -- Stocker les examens en JSON texte
                    montant_total INTEGER NOT NULL,
                    montant_donne INTEGER NOT NULL,
                    reste_a_payer INTEGER NOT NULL,
                    montant_a_rendre INTEGER NOT NULL,
                    date_vente TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
        )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
            """
        )
        # Créer un utilisateur par défaut si la table est vide
        self.insert_user("admin", "password")
        self.conn.commit()

    def insert_examen(self, nom, prix_cach, prix_abonner):
        try:
            query = (
                "INSERT INTO examens (nom, prix_cach, prix_abonner) VALUES (?, ?, ?)"
            )
            self.cursor.execute(query, (nom, prix_cach, prix_abonner))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Erreur SQLite : {e}")
            return False

    def get_all_examens(self):
        self.cursor.execute("SELECT * FROM examens")
        return self.cursor.fetchall()

    def update_examen(self, id_, nom, prix_cach, prix_abonne):
        try:
            self.cursor.execute(
                """
                UPDATE examens
                SET nom = ?, prix_cach = ?, prix_abonner = ?
                WHERE id = ?
                """,
                (nom, prix_cach, prix_abonne, id_),
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Erreur SQLite : {e}")
            return False

    def delete_examen(self, id_):
        self.cursor.execute(
            """
            DELETE FROM examens WHERE id = ?
        """,
            (id_,),
        )
        self.conn.commit()

    # ======================== la partie de vente =========================
    # methode pour charger les examens
    # def load_examens(self):
    #     self.cursor.execute("SELECT nom, prix_cach, prix_abonner FROM examens")
    #     return self.cursor.fetchall()

    # reccuperer un examen par son nom
    def get_examen_by_nom(self, nom):
        """Récupérer un examen par son nom."""
        self.cursor.execute("SELECT * FROM examens WHERE nom = ?", (nom,))
        return self.cursor.fetchone()
    # insert de la facture
    def insert_facture(self, nom_patient, nom_demandeur, societe, fonction, service, type_client, examens, montant_total, montant_donne, reste_a_payer, montant_a_rendre):
        examens_json = json.dumps(examens)  # Convertir en JSON pour stockage
        self.cursor.execute(
            """
            INSERT INTO factures (nom_patient,nom_demandeur, societe, fonction, service, type_client, examens, montant_total, montant_donne, reste_a_payer, montant_a_rendre)
            VALUES (?, ?,?,?,?,? ?, ?, ?, ?, ?)
            """,
            (
                nom_patient,
                nom_demandeur,
                societe,
                fonction,
                service,
                type_client,
                examens_json,
                montant_total,
                montant_donne,
                reste_a_payer,
                montant_a_rendre,
            ),
        )
        self.conn.commit()
    # selectionner les examens pour la table de vente
    def get_all_examens(self):
        self.cursor.execute("SELECT * FROM examens")
        return self.cursor.fetchall()

    def get_prix_examen(
        self, examen_nom, type_client
    ):  # type_client = "abonne" ou "cache"
        self.cursor.execute(
            "SELECT prix_cach, prix_abonner FROM examens WHERE nom = ?", (examen_nom,)
        )
        result = self.cursor.fetchone()
        if result:
            prix_cach, prix_abonner = result
            if type_client == "abonne":
                return prix_abonner
            else:
                return prix_cach
        else:
            raise ValueError("Examen non trouvé.")
        # ============== la methode insert_facture ============== pour ajouter une facture

    def insert_facture(
        self,
        nom_patient,
        nom_demandeur, 
        societe, 
        fonction, 
        service,
        type_client,
        examens,
        montant_total,
        montant_donne,
        reste_a_payer,
        montant_a_rendre,
    ):
        try:
            query = "INSERT INTO factures (nom_patient, nom_demandeur, societe, fonction, service, type_client, examens, montant_total, montant_donne, reste_a_payer, montant_a_rendre) VALUES (?, ?, ?,?,?,?,?, ?, ?, ?, ?)"
            self.cursor.execute(
                query,
                (
                    nom_patient,
                    nom_demandeur,
                    societe,
                    fonction,
                    service,
                    type_client,
                    examens,
                    montant_total,
                    montant_donne,
                    reste_a_payer,
                    montant_a_rendre,
                ),
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Erreur SQLite : {e}")
            return False
    # méthode pour récupérer toutes les factures
    def recuperer_factures(self, filtre_nom="", date_debut=None, date_fin=None):
        query = """
            SELECT id, nom_patient, nom_demandeur, societe, fonction, service, type_client, examens, montant_total, montant_donne, reste_a_payer, date_vente
            FROM factures
            WHERE 1=1
        """
        params = []

        if filtre_nom:
            query += " AND (nom_patient LIKE ? OR societe LIKE ?)"
            params.extend([f"%{filtre_nom}%", f"%{filtre_nom}%"])

        if date_debut and date_fin:
            query += " AND date_vente BETWEEN ? AND ?"
            params.extend([date_debut, date_fin])

        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def delete_facture(self, id_):
        """Supprime une facture par son ID."""
        try:
            self.cursor.execute(
                "DELETE FROM factures WHERE id = ?", (id_,)
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Erreur SQLite lors de la suppression de la facture : {e}")
            return False

    def insert_user(self, username, password):
        try:
            # Vérifier si le nom d'utilisateur existe déjà
            self.cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if self.cursor.fetchone():
                print(f"Utilisateur '{username}' existe déjà.")
                return False

            # Hacher le mot de passe
            hashed_password = hash_password(password)
            query = "INSERT INTO users (username, password) VALUES (?, ?)"
            self.cursor.execute(query, (username, hashed_password))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Erreur SQLite : {e}")
            return False

    def check_user_credentials(self, username, password):
        self.cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        result = self.cursor.fetchone()
        if result:
            hashed_password = result[0]
            if isinstance(hashed_password, str):
                hashed_password = hashed_password.encode('utf-8')  # Convertir en bytes si nécessaire
            return verify_password(password, hashed_password)
        return False

    def close(self):
        self.conn.close()

    def get_resource_path(relative_path):
        """Obtenir le chemin absolu des fichiers inclus dans l'exécutable."""
        if hasattr(sys, "_MEIPASS"):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)


def hash_password(password):
    """Hache un mot de passe en utilisant bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed

def verify_password(password, hashed_password):
    """Vérifie si un mot de passe correspond au hachage."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password)


# Exemple d'utilisation
if __name__ == "__main__":
    db = Database()
  # Ajouter un utilisateur avec un mot de passe haché
    db.close()
