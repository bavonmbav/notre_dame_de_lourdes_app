from PyQt6.QtWidgets import (  # type: ignore
    QApplication,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QDialog,
    QWidget,
    QVBoxLayout,
    QMessageBox,  # Ajout pour les boîtes de dialogue
    QTableWidgetItem,  # Ajout pour les éléments du tableau
    QFormLayout,
    QSpinBox,
    QMenu,
    QLabel,
    QInputDialog,
    QLineEdit,
)
from PyQt6.uic import loadUi  # type: ignore
from view.NotreDame import Ui_MainWindow  # type: ignore
from model.database import Database  # type: ignore
import sys
import json
from PyQt6.QtCore import Qt, QDateTime, QDate  # type: ignore # Ajout pour le menu contextuel
from PyQt6 import QtGui  # type: ignore # Import QtGui for setting window icon
from reportlab.lib.pagesizes import A4, letter, landscape  # type: ignore
from reportlab.pdfgen import canvas  # type: ignore
from reportlab.platypus import Table, TableStyle  # type: ignore # Ajout pour les tableaux PDF
from reportlab.lib import colors  # type: ignore # Ajout pour les couleurs des tableaux
import platform
import subprocess
import os
import pandas as pd  # type: ignore
from datetime import datetime
import bcrypt # type: ignore

def hash_password(password):
    """Hache un mot de passe en utilisant bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed
def verify_password(password, hashed_password):
    """Vérifie si un mot de passe correspond au hachage."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password)

class ModifierExamenDialog(QDialog):
    def __init__(self, examen_data, parent=None):
        super().__init__(parent)
        self.db = Database()
        self.setWindowTitle("Modifier Examen")
        self.setFixedSize(300, 200)
        self.setWindowIcon(QtGui.QIcon("img/marie.png"))

        # Layout principal
        layout = QFormLayout()

        # Champs de saisie
        self.nom_line_edit = QLineEdit(examen_data[1])  # type: ignore # Nom de l'examen
        self.prix_cach_spin = QSpinBox()
        self.prix_cach_spin.setMaximum(
            1000000
        )  # Définir la valeur maximale à 1 000 000
        self.prix_cach_spin.setValue(examen_data[2])  # Prix caché

        self.prix_abonner_spin = QSpinBox()
        self.prix_abonner_spin.setMaximum(
            1000000
        )  # Définir la valeur maximale à 1 000 000
        self.prix_abonner_spin.setValue(examen_data[3])  # Prix abonné

        # Ajouter les champs au layout
        layout.addRow("Nom:", self.nom_line_edit)
        layout.addRow("Prix Caché:", self.prix_cach_spin)
        layout.addRow("Prix Abonné:", self.prix_abonner_spin)

        # Boutons
        self.save_button = QPushButton("Sauvegarder")
        self.cancel_button = QPushButton("Annuler")

        self.save_button.clicked.connect(self.save_changes)
        self.cancel_button.clicked.connect(self.reject)

        # Layout pour les boutons
        button_layout = QVBoxLayout()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)

        # Ajouter le layout des boutons
        layout.addRow(button_layout)

        self.setLayout(layout)

        self.examen_data = examen_data  # Stocker les données de l'examen à modifier

    def save_changes(self):
        # Récupérer les nouvelles valeurs à modifier
        id_ = self.examen_data[0]  # L'ID est stocké dans examen_data
        nom = self.nom_line_edit.text()
        prix_cach = self.prix_cach_spin.value()
        prix_abonne = self.prix_abonner_spin.value()

        if not nom:
            QMessageBox.warning(self, "Champ requis", "Le nom de l'examen est requis.")
            return

        # Appeler la méthode pour mettre à jour les données dans la base
        success = self.db.update_examen(id_, nom, prix_cach, prix_abonne)

        if success:
            QMessageBox.information(self, "Succès", "Examen mis à jour avec succès.")
            self.accept()  # Fermer la boîte de dialogue après succès
        else:
            QMessageBox.critical(self, "Erreur", "Échec de la mise à jour de l'examen.")

    def reject(self):
        self.close()  # Fermer la fenêtre si l'utilisateur annule


class LoginWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Connexion")
        self.setFixedSize(300, 200)
        self.db = Database() 
        # Layout principal
        layout = QVBoxLayout()

        # Champs de saisie
        self.label_username = QLabel("Nom d'utilisateur:")
        self.input_username = QLineEdit()
        self.input_username.setPlaceholderText("Entrez votre nom d'utilisateur")

        self.label_password = QLabel("Mot de passe:")
        self.input_password = QLineEdit()
        self.input_password.setPlaceholderText("Entrez votre mot de passe")
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)

        # Boutons
        self.btn_login = QPushButton("Connexion")
        self.btn_quit = QPushButton("Quitter")

        # Ajouter les widgets au layout
        layout.addWidget(self.label_username)
        layout.addWidget(self.input_username)
        layout.addWidget(self.label_password)
        layout.addWidget(self.input_password)
        layout.addWidget(self.btn_login)
        layout.addWidget(self.btn_quit)

        self.setLayout(layout)

        # Connexions des boutons
        self.btn_login.clicked.connect(self.check_credentials)
        self.btn_quit.clicked.connect(self.close)

    def check_credentials(self):
        username = self.input_username.text()
        password = self.input_password.text()

        # Vérifier les identifiants dans la base de données
        if self.db.check_user_credentials(username, password):
            QMessageBox.information(self, "Succès", "Connexion réussie !")
            self.accept()  # Fermer la fenêtre de connexion avec succès
        else:
            QMessageBox.critical(self, "Erreur", "Identifiants incorrects !")


class ChangePasswordDialog(QDialog):
    def __init__(self, username, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Modifier le mot de passe")
        self.setFixedSize(300, 200)

        self.db = Database()
        self.username = username

        # Layout principal
        layout = QVBoxLayout()

        # Champs de saisie
        self.label_old_password = QLabel("Ancien mot de passe:")
        self.input_old_password = QLineEdit()
        self.input_old_password.setEchoMode(QLineEdit.EchoMode.Password)

        self.label_new_password = QLabel("Nouveau mot de passe:")
        self.input_new_password = QLineEdit()
        self.input_new_password.setEchoMode(QLineEdit.EchoMode.Password)

        self.label_confirm_password = QLabel("Confirmer le mot de passe:")
        self.input_confirm_password = QLineEdit()
        self.input_confirm_password.setEchoMode(QLineEdit.EchoMode.Password)

        # Boutons
        self.btn_save = QPushButton("Sauvegarder")
        self.btn_cancel = QPushButton("Annuler")

        # Ajouter les widgets au layout
        layout.addWidget(self.label_old_password)
        layout.addWidget(self.input_old_password)
        layout.addWidget(self.label_new_password)
        layout.addWidget(self.input_new_password)
        layout.addWidget(self.label_confirm_password)
        layout.addWidget(self.input_confirm_password)
        layout.addWidget(self.btn_save)
        layout.addWidget(self.btn_cancel)

        self.setLayout(layout)

        # Connexions des boutons
        self.btn_save.clicked.connect(self.change_password)
        self.btn_cancel.clicked.connect(self.close)

    def change_password(self):
        old_password = self.input_old_password.text()
        new_password = self.input_new_password.text()
        confirm_password = self.input_confirm_password.text()

        # Vérifier l'ancien mot de passe
        self.db.cursor.execute(
            "SELECT password FROM users WHERE username = ?", (self.username,)
        )
        result = self.db.cursor.fetchone()

        if not result:
            QMessageBox.critical(self, "Erreur", "Utilisateur introuvable.")
            return

        hashed_password = result[0]

        # Vérifier si l'ancien mot de passe correspond au hachage
        if not verify_password(old_password, hashed_password):
            QMessageBox.critical(self, "Erreur", "L'ancien mot de passe est incorrect.")
            return

        # Vérifier que les nouveaux mots de passe correspondent
        if new_password != confirm_password:
            QMessageBox.critical(self, "Erreur", "Les mots de passe ne correspondent pas.")
            return

        # Mettre à jour le mot de passe dans la base de données
        hashed_new_password = hash_password(new_password)
        self.db.cursor.execute(
            "UPDATE users SET password = ? WHERE username = ?", (hashed_new_password, self.username)
        )
        self.db.conn.commit()

        QMessageBox.information(self, "Succès", "Mot de passe modifié avec succès.")
        self.accept()

    def change_user_password(self, username, new_password):
        try:
            hashed_password = hash_password(new_password)  # Hacher le nouveau mot de passe
            query = "UPDATE users SET password = ? WHERE username = ?"
            self.cursor.execute(query, (hashed_password, username))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Erreur SQLite : {e}")
            return False


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Charger l'interface .ui
        # loadUi("view/NotreDame.ui", self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.db = Database()  # ✅ Connexion à la base

        # Connexion des boutons à leurs fonctions respectives
        self.ui.btn_facture.clicked.connect(self.page_facture)
        self.ui.btn_examen.clicked.connect(self.page_examen)
        self.ui.btn_historique.clicked.connect(self.page_historique)
        # connexion avec le bouton ajouter examen
        self.ui.Btn_ajouter_examen.clicked.connect(self.ajouter_examens)
        self.ui.Table_examen.itemClicked.connect(self.remplir_recherche_depuis_table)
        self.ui.Btn_generer_certificat.clicked.connect(
            self.generer_certificat_depuis_selection
        )
        self.ui.btn_logout.clicked.connect(self.logout)
        self.ui.btn_parametres.clicked.connect(self.ouvrir_parametres)

        self.afficher_examens()  # Afficher les examens lors de l'ouverture de l'application
        self.rechercher_examens()  # Charger les examens dans le tableau
        self.ui.Btn_ajouter_au_panier.clicked.connect(self.ajouter_au_panier)
        self.ui.Btn_valider_facture.clicked.connect(self.valider_facture)
        self.ui.Txt_recherche_examen.textChanged.connect(self.rechercher_examens)
        self.charger_factures()
        self.ui.Txt_recherche_filtre.textChanged.connect(self.rechercher_combinee)
        self.ui.Btn_recherche_par_date.clicked.connect(self.rechercher_combinee)
        self.ui.Btn_generer_rapport.clicked.connect(self.recharger_tout)
        self.ui.Btn_exporter_pdf.clicked.connect(self.exporter_factures_en_pdf)
        self.ui.Btn_exporter_excel.clicked.connect(self.exporter_factures_en_excel)
        self.ui.Table_historiqu_payement.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.ui.Table_historiqu_payement.customContextMenuRequested.connect(
            self.open_menu_contextuel
        )
        self.setWindowTitle("CAISSE")
        self.setWindowIcon(QtGui.QIcon("img/marie.png"))
        # Activer le menu contextuel pour le tableau
        self.ui.Table_Tous_examens.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.ui.Table_Tous_examens.customContextMenuRequested.connect(
            self.afficher_menu_contextuel
        )
        self.ui.Table_panier.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.Table_panier.customContextMenuRequested.connect(self.open_menu_contextuel_panier)

    def page_facture(self):
        self.ui.stackedWidget.setCurrentWidget(self.ui.facture)

    def page_examen(self):
        self.ui.stackedWidget.setCurrentWidget(self.ui.ajouterExamen)
        self.afficher_examens()  # Afficher les examens lors de l'ouverture de la page

    def page_historique(self):
        self.ui.stackedWidget.setCurrentWidget(self.ui.tablefacture)

    # =========================opperation a la base de donnees======================
    def ajouter_examens(self):
        nom = self.ui.Txt_nom_examen.text()
        prix_cach = self.ui.Txt_prix_cach.value()
        prix_abonner = self.ui.Txt_prix_abonner.value()

        if not nom:
            QMessageBox.warning(self, "Champ requis", "Le nom de l'examen est requis.")
            return

        try:
            success = self.db.insert_examen(nom, prix_cach, prix_abonner)

            if success:
                QMessageBox.information(self, "Succès", "Examen ajouté avec succès.")
                self.ui.Txt_nom_examen.clear()
                self.ui.Txt_prix_cach.setValue(0)
                self.ui.Txt_prix_abonner.setValue(0)
            else:
                QMessageBox.critical(self, "Erreur", "Échec de l'ajout de l'examen.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Une erreur s'est produite : {e}")
        self.afficher_examens()
        self.rechercher_examens()

    # affichage de la liste des examens
    def afficher_examens(self):
        examens = self.db.get_all_examens()
        self.ui.Table_Tous_examens.setRowCount(len(examens))
        for row, examen in enumerate(examens):
            for column, value in enumerate(examen):
                item = QTableWidgetItem(str(value))  # type: ignore
                self.ui.Table_Tous_examens.setItem(row, column, item)

    def afficher_menu_contextuel(self, position):
        # Obtenir l'indice de la ligne sélectionnée
        index = self.ui.Table_Tous_examens.indexAt(position)
        if not index.isValid():
            return

        # Créer le menu contextuel
        menu = QMenu(self)
        action_modifier = menu.addAction("✏️Modifier")
        action_supprimer = menu.addAction("🗑️Supprimer")

        # Exécuter le menu et obtenir l'action sélectionnée
        action = menu.exec(self.ui.Table_Tous_examens.viewport().mapToGlobal(position))

        if action == action_modifier:
            self.modifier_ligne(index.row())
        elif action == action_supprimer:
            self.supprimer_ligne(index.row())

    def modifier_ligne(self, row):
        # Récupérer les données de la ligne
        id_ = self.ui.Table_Tous_examens.item(row, 0).text()
        nom = self.ui.Table_Tous_examens.item(row, 1).text()
        prix_cach = self.ui.Table_Tous_examens.item(row, 2).text()
        prix_abonner = self.ui.Table_Tous_examens.item(row, 3).text()

        examen_data = (
            id_,
            nom,
            int(prix_cach),
            int(prix_abonner),
        )  # Créer un tuple avec les données de l'examen

        # Ouvrir la fenêtre de modification avec les données existantes
        dialog = ModifierExamenDialog(examen_data, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.afficher_examens()  # Rafraîchir la liste des examens

    def supprimer_ligne(self, row):
        # Demander une confirmation avant de supprimer
        reply = QMessageBox.question(
            self,
            "Confirmation",
            "Voulez-vous vraiment supprimer cet examen ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Supprimer la ligne de la base de données
            id_ = self.ui.Table_Tous_examens.item(row, 0).text()
            try:
                self.db.delete_examen(int(id_))
                self.ui.Table_Tous_examens.removeRow(row)
                QMessageBox.information(
                    self, "Supprimer", "Examen supprimé avec succès."
                )
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Une erreur s'est produite : {e}")

    def rechercher_examens(self):
        texte_recherche = self.ui.Txt_recherche_examen.text().lower()
        self.ui.Table_examen.setRowCount(0)  # Effacer les lignes existantes
        examens = (
            self.db.get_all_examens()
        )  # On suppose que cette fonction existe et retourne une liste d'examens

        for examen in examens:
            nom_examen = examen[1]
            prix_cache = examen[2]
            prix_abonne = examen[3]

            if texte_recherche in nom_examen.lower():
                row_position = self.ui.Table_examen.rowCount()
                self.ui.Table_examen.insertRow(row_position)
                self.ui.Table_examen.setItem(
                    row_position, 0, QTableWidgetItem(nom_examen)
                )
                self.ui.Table_examen.setItem(
                    row_position, 1, QTableWidgetItem(str(prix_cache))
                )
                self.ui.Table_examen.setItem(
                    row_position, 2, QTableWidgetItem(str(prix_abonne))
                )

    # Méthode pour ajouter une facture au panier d'abord
    def ajouter_au_panier(self):
        if not self.ui.Radio_abonner.isChecked() and not self.ui.Radio_cach.isChecked():
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un type de client avant d'ajouter au panier.")
            return

        nom_recherche = self.ui.Txt_recherche_examen.text()
        examen = self.db.get_examen_by_nom(nom_recherche)

        if examen:
            id_examen, nom, prix_cach, prix_abonner = examen
            if self.ui.Radio_abonner.isChecked():
                prix = prix_abonner
            else:
                prix = prix_cach

            quantite = self.ui.Txt_nombre_sejour.value()
            total = prix * quantite

            row_position = self.ui.Table_panier.rowCount()
            self.ui.Table_panier.insertRow(row_position)
            self.ui.Table_panier.setItem(row_position, 0, QTableWidgetItem(nom))
            self.ui.Table_panier.setItem(row_position, 1, QTableWidgetItem(str(prix)))
            self.ui.Table_panier.setItem(row_position, 2, QTableWidgetItem(str(quantite)))

            self.mettre_a_jour_total()
            self.ui.Txt_recherche_examen.clear()
            self.ui.Txt_nombre_sejour.setValue(1)
        else:
            QMessageBox.warning(self, "Erreur", "Examen non trouvé.")

    def mettre_a_jour_total(self):
        total = 0
        for row in range(self.ui.Table_panier.rowCount()):
            prix_item = self.ui.Table_panier.item(row, 1)
            quantite_item = self.ui.Table_panier.item(row, 2)
            if prix_item and quantite_item:
                prix = int(prix_item.text())
                quantite = int(quantite_item.text())
                total += prix * quantite
        self.ui.label_total.setText(f"Total: {total} $")

    def valider_facture(self):
        nom_patient = self.ui.Txt_Nom.text()
        montant_donne = self.ui.Sp_montant.value()
        nom_demandeur = self.ui.Txt_demandeur.text()
        societe = self.ui.Txt_societe.text()
        fonction = self.ui.combo_type_operation.currentText()
        service = self.ui.Combo_type_service.currentText()

        total_text = (
            self.ui.label_total.text().replace("Total: ", "").replace("$", "").strip()
        )
        montant_total = int(total_text) if total_text else 0

        reste_a_payer = 0
        montant_a_rendre = 0

        if montant_donne < montant_total:
            reste_a_payer = montant_total - montant_donne
        else:
            montant_a_rendre = montant_donne - montant_total

        # Déterminer type de client
        if self.ui.Radio_abonner.isChecked():
            type_client = "abonne"
        else:
            type_client = "cache"

        # Construire liste des examens
        examens_list = []
        for row in range(self.ui.Table_panier.rowCount()):
            examen_data = {
                "nom": self.ui.Table_panier.item(row, 0).text(),
                "prix": int(self.ui.Table_panier.item(row, 1).text()),
                "quantite": int(self.ui.Table_panier.item(row, 2).text()),
            }
            examens_list.append(examen_data)
        examens_json = json.dumps(examens_list)
        # Enregistrer dans la base
        try:
            self.db.insert_facture(
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
            )
            # 2. Créer et imprimer la facture en PDF
            self.imprimer_facture()
            QMessageBox.information(
                self.ui.facture,
                "Succès",
                "Facture enregistrée et imprimée avec succès !.",
            )
            self.reinitialiser_formulaire()
        except Exception as e:
            QMessageBox.critical(
                self.ui.facture, "Erreur", f"Une erreur est survenue : {str(e)}"
            )

    def reinitialiser_formulaire(self):
        self.ui.Txt_Nom.clear()
        self.ui.Txt_recherche_examen.clear()
        self.ui.Txt_nombre_sejour.setValue(1)
        self.ui.Table_panier.setRowCount(0)
        self.ui.label_total.setText("Total: 0 $")
        self.ui.Sp_montant.setValue(0)
        self.ui.Radio_abonner.setChecked(False)
        self.ui.Radio_cach.setChecked(False)

    # remplire la zone de recherche
    def remplir_recherche_depuis_table(self):
        selected_items = self.ui.Table_examen.selectedItems()
        if selected_items:
            nom_examen = selected_items[0].text()  # Le premier colonne est le nom
            self.ui.Txt_recherche_examen.setText(nom_examen)

    # Méthode pour imprimer une facture
    def imprimer_facture(self):
        # Créer le dossier 'factures' s'il n'existe pas
        # Obtenir le dossier Documents/Factures
        documents_dir = os.path.join(os.path.expanduser("~"), "Documents")
        factures_dir = os.path.join(documents_dir, "Factures")
        if not os.path.exists(factures_dir):
            os.makedirs(factures_dir)

        # Nom fichier
        vente_id = QDateTime.currentDateTime().toString("yyyyMMdd_hhmmss")
        file_path = os.path.join(factures_dir, f"facture_{vente_id}.pdf")

        c = canvas.Canvas(file_path, pagesize=A4)
        width, height = A4
        margin = 50

        # Ajouter logos si disponibles
        try:
            c.drawImage("img/marie.png", margin, height - 100, width=80, height=80)
            c.drawImage("img/croix.jps", width - 130, height - 100, width=80, height=80)
        except:
            pass  # ignorer si image non trouvée

        # En-tête
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(width / 2, height - 40, "REPUBLIQUE DEMOCRATIQUE DU CONGO")
        c.setFont("Helvetica", 11)
        c.drawCentredString(width / 2, height - 60, "PROVINCE DU HAUT-KATANGA")
        c.drawCentredString(width / 2, height - 80, "CENTRE DE SANTE DE REFERENCE")
        c.drawCentredString(width / 2, height - 100, "NOTRE DAME DE LOURDES DE KASUMBALESA")
        c.drawCentredString(width / 2, height - 120, "AV. DON BOSCO N°08 NEW KOYO/KASUMBALESA")
        c.drawCentredString(width / 2, height - 140, "DIOCESE DE SAKANIA-KIPUSHI")
        c.line(margin, height - 150, width - margin, height - 150)

        # Infos client
        infos = [
            ["Date", datetime.now().strftime('%d/%m/%Y %H:%M')],
            ["Patient", self.ui.Txt_Nom.text()],
            ["Demandeur", self.ui.Txt_demandeur.text()],
            ["Société", self.ui.Txt_societe.text()],
            ["Service", self.ui.Combo_type_service.currentText()],
            ["Fonction", self.ui.combo_type_operation.currentText()],
            ["Type Client", "Abonné" if self.ui.Radio_abonner.isChecked() else "Client Cash"],
        ]

        # Organisation en deux colonnes
        infos_table = []
        for i in range(0, len(infos), 2):
            row = []
            row.append(f"{infos[i][0]} : {infos[i][1]}")
            if i + 1 < len(infos):
                row.append(f"{infos[i+1][0]} : {infos[i+1][1]}")
            else:
                row.append("")
            infos_table.append(row)

        # Tableau infos
        table_info = Table(infos_table, colWidths=[250, 250])
        table_info.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), 0.3, colors.black),
            ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
            ("FONTSIZE", (0,0), (-1,-1), 10),
        ]))
        table_info.wrapOn(c, width, height)
        table_info.drawOn(c, margin, height - 320)

        # Tableau des examens
        data = [["ACTES", "Prix Unitaire", "SEJOUR", "Total"]]
        for row in range(self.ui.Table_panier.rowCount()):
            nom = self.ui.Table_panier.item(row, 0).text()
            prix = int(self.ui.Table_panier.item(row, 1).text())
            qte = int(self.ui.Table_panier.item(row, 2).text())
            total = prix * qte
            data.append([nom, f"{prix} $", str(qte), f"{total} $"])

        # Montants
        montant_total = int(self.ui.label_total.text().replace("Total: ", "").replace("$", "").strip())
        montant_donne = self.ui.Sp_montant.value()
        reste = max(0, montant_total - montant_donne)
        rendre = max(0, montant_donne - montant_total)

        data.append(["", "", "Total Général :", f"{montant_total} $"])
        data.append(["", "", "Montant Donné :", f"{montant_donne} $"])
        data.append(["", "", "Reste à payer :", f"{reste} $"])
        data.append(["", "", "Montant à rendre :", f"{rendre} $"])

        table = Table(data, colWidths=[170, 90, 90, 100])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4B4B4B")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.black),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (0, 1), (-1, -1), "CENTER"),
            ("ALIGN", (-2, -4), (-1, -1), "RIGHT"),
            ("BACKGROUND", (-2, -4), (-1, -1), colors.lightgrey),
            ("SPAN", (0, -4), (1, -4)),
            ("SPAN", (0, -3), (1, -3)),
            ("SPAN", (0, -2), (1, -2)),
            ("SPAN", (0, -1), (1, -1)),
        ]))
        table.wrapOn(c, width, height)
        table.drawOn(c, margin, height - 320 - len(data) * 20 - 30)

        # Bas de page
        c.setFont("Helvetica-Oblique", 9)
        c.drawCentredString(width / 2, 40, "Merci pour votre confiance.")
        c.drawCentredString(width / 2, 25, "notre dame de lourdes - Votre santé, notre priorité.")
        c.save()

        # Impression automatique
        systeme = platform.system()
        if systeme == "Windows":
            os.startfile(file_path, "print")
        elif systeme in ["Linux", "Darwin"]:
            subprocess.run(["lpr", file_path])
        else:
            print("Impression automatique non supportée.")

    # ✅ PDF enregistré et imprimé !

    # Méthode pour afficher l'historique des factures
    def charger_factures(self, filtre_nom="", date_debut=None, date_fin=None):
        self.ui.Table_historiqu_payement.setRowCount(0)

        # Récupérer les factures depuis la base de données avec les filtres
        factures = self.db.recuperer_factures(filtre_nom, date_debut, date_fin)

        for facture in factures:
            row_position = self.ui.Table_historiqu_payement.rowCount()
            self.ui.Table_historiqu_payement.insertRow(row_position)

            for col, value in enumerate(facture):
                # Si la colonne correspond aux examens (par exemple, index 7)
                if col == 7:  # Supposons que la colonne des examens est à l'index 7
                    try:
                        # Charger les examens depuis le JSON et extraire uniquement les noms
                        examens = json.loads(value)
                        noms_examens = ", ".join([examen["nom"] for examen in examens])
                        item = QTableWidgetItem(noms_examens)
                    except Exception as e:
                        item = QTableWidgetItem("Erreur lors du chargement")
                else:
                    item = QTableWidgetItem(str(value))

                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.ui.Table_historiqu_payement.setItem(row_position, col, item)

    def rechercher_par_nom(self):
        filtre = self.ui.Txt_recherche_filtre.text()
        self.charger_factures(filtre_nom=filtre)

    def rechercher_par_date(self):
        date_debut = self.ui.date_debut.date().toString("yyyy-MM-dd")
        date_fin = self.ui.date_fin.date().toString("yyyy-MM-dd")
        self.charger_factures(date_debut=date_debut, date_fin=date_fin)

    def recharger_tout(self):
        self.ui.Txt_recherche_filtre.clear()
        self.ui.date_debut.setDate(QDate.currentDate())
        self.ui.date_fin.setDate(QDate.currentDate())
        self.charger_factures()

    def rechercher_combinee(self):
        filtre_nom = self.ui.Txt_recherche_filtre.text()
        date_debut = self.ui.date_debut.date().toString("yyyy-MM-dd")
        date_fin = self.ui.date_fin.date().toString("yyyy-MM-dd")

        # Vérifier si les champs sont remplis
        if not filtre_nom and not date_debut and not date_fin:
            QMessageBox.warning(self, "Erreur", "Veuillez remplir au moins un champ pour effectuer une recherche.")
            return

        # Effectuer la recherche combinée
        self.charger_factures(filtre_nom=filtre_nom, date_debut=date_debut, date_fin=date_fin)

    # exportation des factures en pdf
    def exporter_factures_en_pdf(self):
        dossier = self.get_factures_directory()
        chemin_pdf = os.path.abspath(os.path.join(dossier, "historique_factures.pdf"))

        try:
            c = canvas.Canvas(chemin_pdf, pagesize=landscape(A4))  # Mode paysage
            width, height = landscape(A4)  # Dimensions paysage
            margin = 50

            # Logo et entête
            try:
                c.drawImage("img/marie.png", margin, height - 100, width=60, height=60)
                c.drawImage("img/croix.jps", width - 100, height - 100, width=60, height=60)
            except:
                pass  # Éviter plantage si image manquante

            c.setFont("Helvetica-Bold", 14)
            c.drawCentredString(
                width / 2, height - 40, "REPUBLIQUE DEMOCRATIQUE DU CONGO"
            )
            c.setFont("Helvetica", 11)
            c.drawCentredString(width / 2, height - 60, "PROVINCE DU HAUT-KATANGA")
            c.drawCentredString(width / 2, height - 80, "CENTRE DE SANTE DE REFERENCE")
            c.drawCentredString(
                width / 2, height - 100, "NOTRE DAME DE LOURDES DE KASUMBALESA"
            )
            c.drawCentredString(
                width / 2, height - 120, "AV. DON BOSCO N°08 NEW KOYO/KASUMBALESA"
            )
            c.drawCentredString(width / 2, height - 140, "DIOCESE DE SAKANIA-KIPUSHI")

            c.line(margin, height - 150, width - margin, height - 150)

            # Colonnes
            colonnes = [
                "ID", "CLIENT", "DEMANDEUR", "SOCIETE", "FONCTION", "SERVICE",
                "TYPE CLIENT", "EXAMENS", "MONTANT", "PAYER", "DETTE", "DATE"
            ]
            data = [colonnes]

            # Données du tableau
            for row in range(self.ui.Table_historiqu_payement.rowCount()):
                ligne = []
                for col in range(self.ui.Table_historiqu_payement.columnCount()):
                    item = self.ui.Table_historiqu_payement.item(row, col)
                    texte = item.text() if item else ""
                    ligne.append(texte)
                data.append(ligne)

            # Ajuster dynamiquement les largeurs des colonnes
            col_widths = [width / len(colonnes) for _ in colonnes]

            # Créer un tableau stylisé
            table = Table(data, colWidths=col_widths)
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
                ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
            ]))

            # Positionner le tableau
            table.wrapOn(c, width, height)
            table.drawOn(c, margin, height - 300)

            # Bas de page
            c.setFont("Helvetica-Oblique", 10)
            c.drawCentredString(width / 2, 40, "Merci pour votre confiance.")
            c.save()

            QMessageBox.information(
                self, "Export PDF", f"Factures exportées avec succès dans {chemin_pdf}"
            )
        except PermissionError:
            QMessageBox.critical(
                self,
                "Erreur",
                f"Impossible de créer le fichier. Vérifiez que le fichier n'est pas ouvert ou que vous avez les permissions nécessaires.\nChemin : {chemin_pdf}",
            )
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue : {e}")

    # Fin de l'exportation des factures en excel

    def get_factures_directory(self):
        # Obtenir le chemin du dossier Documents de l'utilisateur
        documents_dir = os.path.join(os.path.expanduser("~"), "Documents")
        factures_dir = os.path.join(documents_dir, "exporter_factures")

        # Créer le dossier Factures s'il n'existe pas
        if not os.path.exists(factures_dir):
            os.makedirs(factures_dir)

        return factures_dir

    def exporter_factures_en_excel(self):
        dossier = self.get_factures_directory()
        
        chemin_excel = os.path.join(dossier, "historique_factures.xlsx")

        data = []
        colonnes = []

        for col in range(self.ui.Table_historiqu_payement.columnCount()):
            item = self.ui.Table_historiqu_payement.horizontalHeaderItem(col)
            colonnes.append(item.text() if item else f"Colonne {col}")

        for row in range(self.ui.Table_historiqu_payement.rowCount()):
            ligne = []
            for col in range(self.ui.Table_historiqu_payement.columnCount()):
                item = self.ui.Table_historiqu_payement.item(row, col)
                ligne.append(item.text() if item else "")
            data.append(ligne)

        df = pd.DataFrame(data, columns=colonnes)
        df.to_excel(chemin_excel, index=False)

        QMessageBox.information(
            self, "Export Excel", f"Factures exportées avec succès dans {chemin_excel}"
        )

    # Méthode pour ouvrir le menu contextuel
    def open_menu_contextuel(self, position):
        menu = QMenu()

        action_supprimer = menu.addAction("🗑️ Supprimer")
        action_rembourser = menu.addAction("💰 Rembourser dette")
        action_afficher = menu.addAction("📄 Afficher historique remboursement")

        action = menu.exec(
            self.ui.Table_historiqu_payement.viewport().mapToGlobal(position)
        )

        if action == action_supprimer:
            self.supprimer_facture_selectionnee()
        elif action == action_rembourser:
            self.rembourser_dette()
        elif action == action_afficher:
            self.afficher_historique_remboursement()

    # methode pour supprimer une facture selectionnee
    def supprimer_facture_selectionnee(self):
        selected = self.ui.Table_historiqu_payement.currentRow()
        if selected < 0:
            QMessageBox.warning(
                self, "Attention", "Veuillez sélectionner une facture à supprimer."
            )
            return

        item = self.ui.Table_historiqu_payement.item(selected, 0)
        if item is None:
            QMessageBox.warning(
                self, "Erreur", "La facture sélectionnée est invalide ou vide."
            )
            return

        id_facture = item.text()

        confirm = QMessageBox.question(
            self,
            "Confirmer suppression",
            "Voulez-vous vraiment supprimer cette facture ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if confirm == QMessageBox.StandardButton.Yes:
            try:
                self.db.delete_facture(
                    int(id_facture)
                )  # Assurez-vous que cette méthode existe dans votre classe Database
                QMessageBox.information(
                    self, "Succès", "Facture supprimée avec succès."
                )
                self.charger_factures()  # Recharge la table
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Une erreur est survenue : {e}")

    # Méthode pour rembourser une dette
    def rembourser_dette(self):
        selected = self.ui.Table_historiqu_payement.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner une facture.")
            return

        item_id = self.ui.Table_historiqu_payement.item(selected, 0)
        item_nom = self.ui.Table_historiqu_payement.item(selected, 1)
        item_reste = self.ui.Table_historiqu_payement.item(selected, 10)
        item_montant_donne = self.ui.Table_historiqu_payement.item(selected, 9)

        if not item_id or not item_nom or not item_reste or not item_montant_donne:
            QMessageBox.warning(
                self, "Erreur", "Les informations de la facture sont invalides."
            )
            return

        id_facture = int(item_id.text())
        nom_patient = item_nom.text()
        reste = int(item_reste.text())
        montant_donne = int(item_montant_donne.text())

        montant, ok = QInputDialog.getInt(
            self,
            "Rembourser dette",
            f"Montant payé par {nom_patient} (reste : {reste}):",
            min=1,
            max=reste,
        )
        # maximum de qinputdialog zonne de saisie 100
        if montant > reste:
            QMessageBox.warning(
                self,
                "Erreur",
                f"Le montant ne peut pas dépasser le reste à payer ({reste}).",
            )
            return

        if ok:
            try:
                # Mise à jour des montants
                nouveau_reste = reste - montant
                nouveau_montant_donne = montant_donne + montant

                # Mettre à jour la facture dans la base de données
                self.db.cursor.execute(
                    """
                    UPDATE factures
                    SET reste_a_payer = ?, montant_donne = ?
                    WHERE id = ?
                    """,
                    (nouveau_reste, nouveau_montant_donne, id_facture),
                )
                self.db.conn.commit()

                # Enregistrer le remboursement dans une nouvelle table
                self.db.cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS remboursements (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        facture_id INTEGER,
                        montant_rembourse INTEGER,
                        date_remboursement TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                self.db.cursor.execute(
                    "INSERT INTO remboursements (facture_id, montant_rembourse) VALUES (?, ?)",
                    (id_facture, montant),
                )
                self.db.conn.commit()

                QMessageBox.information(
                    self, "Succès", f"Remboursement de {montant} $ enregistré."
                )
                self.charger_factures()  # Rafraîchir la table des factures
                if nouveau_reste == 0:
                    self.generer_certificat_remboursement(id_facture, nom_patient)
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Une erreur est survenue : {e}")

    def afficher_historique_remboursement(self):
        selected = self.ui.Table_historiqu_payement.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner une facture.")
            return

        item = self.ui.Table_historiqu_payement.item(selected, 0)
        if not item:
            QMessageBox.warning(
                self, "Erreur", "La facture sélectionnée est invalide ou vide."
            )
            return

        id_facture = item.text()

        try:
            # Récupérer les remboursements depuis la base de données
            self.db.cursor.execute(
                """
                SELECT montant_rembourse, date_remboursement
                FROM remboursements
                WHERE facture_id = ?
                ORDER BY date_remboursement ASC
                """,
                (id_facture,),
            )
            remboursements = self.db.cursor.fetchall()

            if not remboursements:
                QMessageBox.information(self, "Info", "Aucun remboursement trouvé.")
                return

            # Construire le texte de l'historique
            texte = f"Historique des remboursements de la facture {id_facture}:\n\n"
            total = 0
            for montant, date in remboursements:
                texte += f"- {montant} $ le {date}\n"
                total += montant

            texte += f"\nTotal remboursé : {total} $"

            QMessageBox.information(self, "Historique Remboursements", texte)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue : {e}")

    def generer_certificat_remboursement(self, id_facture, nom_patient):
        dossier = self.get_factures_directory()
        # Créer le dossier s'il n'existe pas
        chemin_fichier = os.path.abspath(
            os.path.join(dossier, f"certificat_remboursement_{id_facture}.pdf")
        )

        try:
            c = canvas.Canvas(chemin_fichier, pagesize=A4)
            largeur, hauteur = A4

            c.setFont("Helvetica-Bold", 18)
            c.drawCentredString(
                largeur / 2, hauteur - 100, "CERTIFICAT DE REMBOURSEMENT DE DETTE"
            )

            c.setFont("Helvetica", 12)
            c.drawString(100, hauteur - 150, f"Patient : {nom_patient}")
            c.drawString(100, hauteur - 170, f"Numéro de Facture : {id_facture}")
            c.drawString(
                100,
                hauteur - 190,
                f"Date d'édition : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            )

            c.setFont("Helvetica", 14)
            c.drawString(
                100,
                hauteur - 240,
                "Nous certifions par la présente que le patient a entièrement réglé sa dette.",
            )

            c.save()

            QMessageBox.information(
                self,
                "Certificat généré",
                f"Le certificat de remboursement a été créé dans le dossier :\n{chemin_fichier}",
            )

            # Optionnel : Ouvrir le PDF automatiquement
            try:
                os.startfile(chemin_fichier)  # Windows
            except AttributeError:
                os.system(f"open {chemin_fichier}")  # Mac/Linux
        except PermissionError:
            QMessageBox.critical(
                self,
                "Erreur",
                f"Impossible de créer le fichier. Vérifiez que le fichier n'est pas ouvert ou que vous avez les permissions nécessaires.\nChemin : {chemin_fichier}",
            )

    def generer_certificat_depuis_selection(self):
        ligne_selectionnee = self.ui.Table_historiqu_payement.currentRow()

        if ligne_selectionnee == -1:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner une facture.")
            return

        id_facture = int(
            self.ui.Table_historiqu_payement.item(ligne_selectionnee, 0).text()
        )
        nom_patient = self.ui.Table_historiqu_payement.item(
            ligne_selectionnee, 1
        ).text()
        reste_a_payer = int(
            self.ui.Table_historiqu_payement.item(ligne_selectionnee, 6).text()
        )

        if reste_a_payer != 0:
            QMessageBox.warning(
                self, "Erreur", "Le patient n'a pas encore réglé toute sa dette."
            )
            return

        self.generer_certificat_remboursement(id_facture, nom_patient)

    def open_menu_contextuel_panier(self, position):
        menu = QMenu()

        action_annuler_examen = menu.addAction("🗑️ Annuler cet ACTE")
        action_annuler_facture = menu.addAction("❌ Annuler toute la facture")

        action = menu.exec(self.ui.Table_panier.viewport().mapToGlobal(position))

        if action == action_annuler_examen:
            self.annuler_examen_selectionne()
        elif action == action_annuler_facture:
            self.annuler_facture()

    def annuler_examen_selectionne(self):
        selected_row = self.ui.Table_panier.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un examen à annuler.")
            return

        self.ui.Table_panier.removeRow(selected_row)
        self.mettre_a_jour_total()
        QMessageBox.information(self, "Succès", "Examen annulé avec succès.")

    def annuler_facture(self):
        confirmation = QMessageBox.question(
            self,
            "Confirmation",
            "Voulez-vous vraiment annuler toute la facture ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if confirmation == QMessageBox.StandardButton.Yes:
            self.ui.Table_panier.setRowCount(0)
            self.mettre_a_jour_total()
            QMessageBox.information(self, "Succès", "Facture annulée avec succès.")

    def logout(self):
        confirmation = QMessageBox.question(
            self,
            "Déconnexion",
            "Êtes-vous sûr de vouloir vous déconnecter ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirmation == QMessageBox.StandardButton.Yes:
            self.close()  # Ferme la fenêtre principale
            # Réouvrir la fenêtre de connexion
            login_window = LoginWindow()
            if login_window.exec() == QDialog.DialogCode.Accepted:
                # Si la connexion est réussie, rouvrir la fenêtre principale
                self.__init__()  # Réinitialiser la fenêtre principale
                self.show()

    def ouvrir_parametres(self):
        dialog = ChangePasswordDialog(username="admin", parent=self)  # Remplacez "admin" par l'utilisateur connecté
        dialog.exec()


# Exécution de l'application
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Afficher la fenêtre de connexion
    login_window = LoginWindow()
    if login_window.exec() == QDialog.DialogCode.Accepted:
        # Si la connexion est réussie, afficher la fenêtre principale
        main_window = MainWindow()
        main_window.show()
        sys.exit(app.exec())
