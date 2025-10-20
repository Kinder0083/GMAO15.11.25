#!/usr/bin/env python3
"""
Script pour nettoyer et convertir le fichier Requêteur.xlsx
en un format compatible pour l'import
"""
import pandas as pd
import sys
from datetime import datetime

def clean_purchase_file(input_file, output_file=None):
    """Nettoyer le fichier d'achat et le sauvegarder"""
    
    if output_file is None:
        output_file = input_file.replace('.xlsx', '_cleaned.xlsx')
    
    print(f"📖 Lecture du fichier : {input_file}")
    
    # Mapping des colonnes
    column_mapping = {
        "Fournisseur": "fournisseur",
        "N° Commande": "numeroCommande",
        "N° reception": "numeroReception",
        "Date de création": "dateCreation",
        "Article": "article",
        "Description": "description",
        "Groupe statistique STK": "groupeStatistique",
        "quantité": "quantite",
        "Quantité": "quantite",
        "Montant ligne HT": "montantLigneHT",
        "Quantité retournée": "quantiteRetournee",
        "Site": "site",
        "Creation user": "creationUser"
    }
    
    try:
        # Essayer de lire avec openpyxl (plus robuste)
        df = pd.read_excel(input_file, engine='openpyxl')
        print(f"✅ Fichier lu avec succès ({len(df)} lignes)")
        
        # Afficher les colonnes trouvées
        print(f"\n📋 Colonnes trouvées : {list(df.columns)}")
        
        # Renommer les colonnes
        df = df.rename(columns=column_mapping)
        print(f"✅ Colonnes renommées")
        
        # Nettoyer les données
        df = df.dropna(how='all')  # Supprimer les lignes complètement vides
        print(f"✅ Lignes vides supprimées ({len(df)} lignes restantes)")
        
        # Convertir les types
        if 'quantite' in df.columns:
            df['quantite'] = pd.to_numeric(df['quantite'], errors='coerce').fillna(0)
        
        if 'montantLigneHT' in df.columns:
            df['montantLigneHT'] = pd.to_numeric(df['montantLigneHT'], errors='coerce').fillna(0)
        
        if 'quantiteRetournee' in df.columns:
            df['quantiteRetournee'] = pd.to_numeric(df['quantiteRetournee'], errors='coerce').fillna(0)
        
        # Sauvegarder
        df.to_excel(output_file, index=False, engine='openpyxl')
        print(f"\n✅ Fichier nettoyé sauvegardé : {output_file}")
        print(f"📊 Colonnes dans le fichier de sortie : {list(df.columns)}")
        print(f"📈 {len(df)} lignes prêtes pour l'import")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur : {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 clean_purchase_file.py <fichier_input.xlsx> [fichier_output.xlsx]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = clean_purchase_file(input_file, output_file)
    sys.exit(0 if success else 1)
