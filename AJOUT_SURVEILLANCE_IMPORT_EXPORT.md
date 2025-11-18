# ✅ Ajout du "Plan de Surveillance" dans Import/Export

## 📋 Modifications Effectuées

Le module **"Plan de Surveillance"** a été ajouté à la page Import/Export pour permettre l'import et l'export des données de surveillance.

---

## 🔧 FRONTEND

### **Fichier :** `/app/frontend/src/pages/ImportExport.jsx`

**Ligne 28 - Ajout dans la liste des modules :**
```javascript
const modules = [
  { value: 'all', label: 'Toutes les données' },
  { value: 'intervention-requests', label: 'Demandes d\'intervention' },
  { value: 'work-orders', label: 'Ordres de travail' },
  { value: 'improvement-requests', label: 'Demandes d\'amélioration' },
  { value: 'improvements', label: 'Améliorations' },
  { value: 'equipments', label: 'Équipements' },
  { value: 'meters', label: 'Compteurs' },
  { value: 'surveillance-items', label: 'Plan de Surveillance' },  // ✅ NOUVEAU
  { value: 'users', label: 'Utilisateurs (Équipes)' },
  { value: 'inventory', label: 'Inventaire' },
  { value: 'locations', label: 'Zones' },
  { value: 'vendors', label: 'Fournisseurs' },
  { value: 'purchase-history', label: 'Historique Achat' }
];
```

---

## 🔧 BACKEND

### **Fichier :** `/app/backend/server.py`

#### **1. Ajout dans EXPORT_MODULES (ligne 3077) :**
```python
EXPORT_MODULES = {
    "intervention-requests": "intervention_requests",
    "work-orders": "work_orders",
    "improvement-requests": "improvement_requests",
    "improvements": "improvements",
    "equipments": "equipments",
    "meters": "meters",
    "meter-readings": "meter_readings",
    "surveillance-items": "surveillance_items",  # ✅ NOUVEAU
    "users": "users",
    "inventory": "inventory",
    "locations": "locations",
    "vendors": "vendors",
    "purchase-history": "purchase_history"
}
```

#### **2. Ajout du mapping des colonnes (lignes ~3375) :**
```python
"surveillance-items": {
    "ID": "id",
    "Titre": "titre",
    "Title": "titre",
    "Catégorie": "category",
    "Category": "category",
    "Bâtiment": "batiment",
    "Building": "batiment",
    "Zone": "zone",
    "Équipement": "equipement",
    "Equipment": "equipement",
    "Responsable": "responsable",
    "Responsible": "responsable",
    "Périodicité": "periodicite",
    "Frequency": "periodicite",
    "Dernier contrôle": "dernierControle",
    "Last Check": "dernierControle",
    "Prochain contrôle": "prochainControle",
    "Next Check": "prochainControle",
    "Statut": "status",
    "Status": "status",
    "Commentaire": "commentaire",
    "Comment": "commentaire",
    "Durée rappel échéance": "duree_rappel_echeance",
    "Reminder Duration": "duree_rappel_echeance"
}
```

---

## 📊 COLONNES SUPPORTÉES POUR L'IMPORT/EXPORT

Le système supporte les colonnes suivantes pour le module "Plan de Surveillance" :

| Colonne (Français) | Colonne (Anglais) | Champ DB |
|-------------------|-------------------|----------|
| ID | ID | id |
| Titre | Title | titre |
| Catégorie | Category | category |
| Bâtiment | Building | batiment |
| Zone | Zone | zone |
| Équipement | Equipment | equipement |
| Responsable | Responsible | responsable |
| Périodicité | Frequency | periodicite |
| Dernier contrôle | Last Check | dernierControle |
| Prochain contrôle | Next Check | prochainControle |
| Statut | Status | status |
| Commentaire | Comment | commentaire |
| Durée rappel échéance | Reminder Duration | duree_rappel_echeance |

---

## 🚀 UTILISATION

### **EXPORT :**

1. Aller dans **"Import / Export"** (menu sidebar)
2. Dans la section **"Exporter les données"** :
   - Sélectionner **"Plan de Surveillance"** dans le menu déroulant
   - Choisir le format : **CSV** ou **Excel (XLSX)**
   - Cliquer sur **"Exporter"**
3. Le fichier sera téléchargé avec toutes les données de surveillance

**Export "Toutes les données" :**
- Pour exporter tous les modules (y compris Plan de Surveillance)
- Utiliser uniquement le format **XLSX**
- Chaque module sera dans une feuille Excel séparée

---

### **IMPORT :**

1. Aller dans **"Import / Export"**
2. Dans la section **"Importer les données"** :
   - Sélectionner **"Plan de Surveillance"** dans le menu déroulant
   - Choisir le mode :
     * **"Ajouter aux données existantes"** : Ajoute de nouvelles entrées
     * **"Écraser les données existantes (par ID)"** : Met à jour les entrées existantes
   - Sélectionner le fichier **CSV** ou **Excel**
   - Cliquer sur **"Importer"**
3. Le résultat s'affichera avec :
   - Nombre d'entrées ajoutées
   - Nombre d'entrées mises à jour
   - Nombre d'entrées ignorées
   - Liste des erreurs éventuelles

---

## 📝 FORMAT DE FICHIER ATTENDU

### **Format CSV :**
```csv
ID,Titre,Catégorie,Bâtiment,Zone,Équipement,Responsable,Périodicité,Dernier contrôle,Prochain contrôle,Statut,Commentaire,Durée rappel échéance
uuid-1,Vérification extincteurs,INCENDIE,BATIMENT 1,Zone A,Extincteur 01,MAINT,Mensuel,2025-01-01,2025-02-01,PLANIFIE,RAS,30
uuid-2,Test alarme incendie,INCENDIE,BATIMENT 2,Zone B,Alarme 02,QHSE,Trimestriel,2025-01-15,2025-04-15,REALISE,Conforme,45
```

### **Format Excel (XLSX) :**
- Même structure que CSV mais dans un fichier Excel
- Pour "Toutes les données", chaque module dans une feuille :
  * Feuille "surveillance-items"
  * Feuille "work-orders"
  * Feuille "equipments"
  * etc.

---

## ✅ TESTS EFFECTUÉS

- ✅ Backend redémarré sans erreur
- ✅ Module "surveillance-items" ajouté dans EXPORT_MODULES
- ✅ Mapping des colonnes configuré pour l'import/export
- ✅ Frontend mis à jour avec la nouvelle option

---

## 📁 FICHIERS MODIFIÉS

1. `/app/frontend/src/pages/ImportExport.jsx` - Ligne 28
2. `/app/backend/server.py` - Lignes 3077 et 3375

---

## 🚀 PRÊT POUR GITHUB

```bash
cd /app
git add frontend/src/pages/ImportExport.jsx
git add backend/server.py
git commit -m "feat: Ajout Plan de Surveillance dans Import/Export

- Ajout surveillance-items dans les modules d'import/export
- Configuration du mapping des colonnes (FR/EN)
- Support des formats CSV et XLSX"
git push origin main
```

---

## 💡 NOTES

**Valeurs Enum à respecter pour l'import :**

- **Catégorie** : MMRI, INCENDIE, SECURITE_ENVIRONNEMENT, ELECTRIQUE, MANUTENTION, EXTRACTION, AUTRE
- **Responsable** : MAINT, PROD, QHSE, LOGISTIQUE, AUTRE
- **Statut** : PLANIFIER, PLANIFIE, REALISE

**Champs obligatoires :**
- Titre
- Catégorie
- Responsable

**Dates :** Format ISO (YYYY-MM-DD) ou format français (DD/MM/YYYY)

---

**✅ Module "Plan de Surveillance" maintenant disponible dans Import/Export**
