#====================================================================================================
# START - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================

# THIS SECTION CONTAINS CRITICAL TESTING INSTRUCTIONS FOR BOTH AGENTS
# BOTH MAIN_AGENT AND TESTING_AGENT MUST PRESERVE THIS ENTIRE BLOCK

# Communication Protocol:
# If the `testing_agent` is available, main agent should delegate all testing tasks to it.
#
# You have access to a file called `test_result.md`. This file contains the complete testing state
# and history, and is the primary means of communication between main and the testing agent.
#
# Main and testing agents must follow this exact format to maintain testing data. 
# The testing data must be entered in yaml format Below is the data structure:
# 
## user_problem_statement: {problem_statement}
## backend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.py"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## frontend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.js"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## metadata:
##   created_by: "main_agent"
##   version: "1.0"
##   test_sequence: 0
##   run_ui: false
##
## test_plan:
##   current_focus:
##     - "Task name 1"
##     - "Task name 2"
##   stuck_tasks:
##     - "Task name with persistent issues"
##   test_all: false
##   test_priority: "high_first"  # or "sequential" or "stuck_first"
##
## agent_communication:
##     -agent: "main"  # or "testing" or "user"
##     -message: "Communication message between agents"

# Protocol Guidelines for Main agent
#
# 1. Update Test Result File Before Testing:
#    - Main agent must always update the `test_result.md` file before calling the testing agent
#    - Add implementation details to the status_history
#    - Set `needs_retesting` to true for tasks that need testing
#    - Update the `test_plan` section to guide testing priorities
#    - Add a message to `agent_communication` explaining what you've done
#
# 2. Incorporate User Feedback:
#    - When a user provides feedback that something is or isn't working, add this information to the relevant task's status_history
#    - Update the working status based on user feedback
#    - If a user reports an issue with a task that was marked as working, increment the stuck_count
#    - Whenever user reports issue in the app, if we have testing agent and task_result.md file so find the appropriate task for that and append in status_history of that task to contain the user concern and problem as well 
#
# 3. Track Stuck Tasks:
#    - Monitor which tasks have high stuck_count values or where you are fixing same issue again and again, analyze that when you read task_result.md
#    - For persistent issues, use websearch tool to find solutions
#    - Pay special attention to tasks in the stuck_tasks list
#    - When you fix an issue with a stuck task, don't reset the stuck_count until the testing agent confirms it's working
#
# 4. Provide Context to Testing Agent:
#    - When calling the testing agent, provide clear instructions about:
#      - Which tasks need testing (reference the test_plan)
#      - Any authentication details or configuration needed
#      - Specific test scenarios to focus on
#      - Any known issues or edge cases to verify
#
# 5. Call the testing agent with specific instructions referring to test_result.md
#
# IMPORTANT: Main agent must ALWAYS update test_result.md BEFORE calling the testing agent, as it relies on this file to understand what to test next.

#====================================================================================================
# END - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================



#====================================================================================================
# Testing Data - Main Agent and testing sub agent both should log testing data below this section
#====================================================================================================

user_problem_statement: |
  L'utilisateur demande l'implémentation d'une fonctionnalité Import/Export (Admin uniquement) :
  1. Créer une page Import/Export accessible uniquement aux administrateurs
  2. Permettre l'export des données en CSV ou XLSX pour chaque module ou toutes les données
  3. Permettre l'import de données avec deux modes : Ajouter ou Écraser
  4. Afficher un rapport détaillé après l'import (succès, duplicatas, erreurs)
  5. Interface intuitive et ergonomique pour utilisateurs découvrant le logiciel

backend:
  - task: "Endpoint GET /api/export/{module}"
    implemented: true
    working: true
    file: "/app/backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Endpoint existant pour exporter les données d'un module (work-orders, equipments, users, inventory, locations, vendors, all). Supporte CSV et XLSX. Admin uniquement."
      - working: true
        agent: "testing"
        comment: "✓ TESTÉ ET FONCTIONNEL - Tous les tests d'export passent avec succès : CSV pour modules spécifiques (work-orders, equipments, users, inventory, locations, vendors), XLSX pour modules spécifiques et toutes les données. Headers Content-Type et Content-Disposition corrects. Contrôle d'accès Admin fonctionnel (403 pour non-admin). Export CSV 'all' échoue correctement avec 400."

  - task: "Endpoint POST /api/import/{module}"
    implemented: true
    working: true
    file: "/app/backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Endpoint existant pour importer les données d'un module. Supporte CSV et XLSX. Deux modes : 'add' (ajouter) et 'replace' (écraser par ID). Retourne des statistiques détaillées. Admin uniquement."
      - working: true
        agent: "testing"
        comment: "✓ TESTÉ ET FONCTIONNEL - Tous les tests d'import passent avec succès : Mode 'add' fonctionne (3 locations ajoutées), Mode 'replace' fonctionne (1 location mise à jour), Support CSV et XLSX validé, Gestion d'erreurs correcte (module invalide=400, format invalide=400), Contrôle d'accès Admin fonctionnel (403 pour non-admin), Structure de réponse correcte avec statistiques détaillées (total, inserted, updated, skipped, errors)."

frontend:
  - task: "API functions pour import/export"
    implemented: true
    working: "NA"
    file: "/app/frontend/src/services/api.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Ajout de importExportAPI avec fonctions exportData et importData"

  - task: "Page ImportExport.jsx"
    implemented: true
    working: "NA"
    file: "/app/frontend/src/pages/ImportExport.jsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Page complète avec interface intuitive et ergonomique : sélection de module, choix de format (CSV/XLSX), mode d'import (Ajouter/Écraser), affichage du rapport d'import avec statistiques (total, ajoutés, mis à jour, ignorés) et guide d'utilisation"

  - task: "Navigation Import/Export (Admin uniquement)"
    implemented: true
    working: "NA"
    file: "/app/frontend/src/components/Layout/MainLayout.jsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Ajout du lien 'Import / Export' dans la navigation avec icône Database. Visible uniquement pour les utilisateurs ADMIN. Récupération du rôle depuis localStorage."

metadata:
  created_by: "main_agent"
  version: "1.0"
  test_sequence: 2
  run_ui: false

test_plan:
  current_focus: []
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication:
  - agent: "main"
    message: |
      J'ai implémenté la fonctionnalité complète Import/Export (Admin uniquement) :
      
      BACKEND (déjà existant, vérifié) :
      - Endpoint GET /api/export/{module} : export CSV ou XLSX pour modules spécifiques ou "all"
      - Endpoint POST /api/import/{module} : import CSV ou XLSX avec mode "add" ou "replace"
      - Dépendances installées : pandas, openpyxl, xlsxwriter
      - Protection Admin via get_current_admin_user
      
      FRONTEND (nouvelles modifications) :
      - MainLayout.jsx : Ajout du lien "Import / Export" avec icône Database (visible uniquement pour ADMIN)
      - ImportExport.jsx : Interface intuitive avec 3 sections principales :
        1. Export : Sélection module + format (CSV/XLSX) + bouton téléchargement
        2. Import : Sélection module + mode (Ajouter/Écraser) + upload fichier
        3. Rapport : Statistiques détaillées (total, ajoutés, mis à jour, ignorés) + liste des erreurs
      - api.js : Ajout de importExportAPI avec fonctions exportData et importData
      - Guide d'utilisation intégré sur la page
      
      TESTS À EFFECTUER :
      1. Vérifier l'accès Admin uniquement (endpoints et navigation)
      2. Tester l'export CSV d'un module spécifique
      3. Tester l'export XLSX d'un module spécifique
      4. Tester l'export XLSX de toutes les données
      5. Tester l'import en mode "add" (ajout)
      6. Tester l'import en mode "replace" (écrasement par ID)
      7. Vérifier le rapport d'import avec statistiques
      8. Vérifier la gestion des erreurs (fichier invalide, module invalide, etc.)
      
      CREDENTIALS DE TEST :
      - Email: admin@example.com
      - Password: password123
