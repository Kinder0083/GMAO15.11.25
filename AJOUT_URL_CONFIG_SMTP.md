# ✅ Ajout de la Configuration des URLs dans Paramètres SMTP

## 📋 Modification Effectuée

Ajout de deux champs **"URL Frontend"** et **"URL Backend"** dans la section **"Configuration SMTP"** du menu **"Paramètres spéciaux"**, permettant de modifier les adresses IP/URLs de l'application directement depuis l'interface.

---

## 🎯 OBJECTIF

Permettre aux administrateurs de modifier les URLs de l'application (qui étaient demandées lors de l'installation) sans avoir à éditer manuellement les fichiers `.env`. Ces URLs sont utilisées pour :
- Les liens dans les emails de notification
- La configuration de sécurité CORS
- Les redirections et l'authentification

---

## 🔧 MODIFICATIONS FRONTEND

### **Fichier :** `/app/frontend/src/pages/SpecialSettings.jsx`

#### **1. Ajout des champs dans l'état (ligne 29) :**
```javascript
const [smtpConfig, setSmtpConfig] = useState({
  smtp_host: '',
  smtp_port: 587,
  smtp_user: '',
  smtp_password: '',
  smtp_from_email: '',
  smtp_from_name: 'GMAO Iris',
  smtp_use_tls: true,
  frontend_url: '',      // ✅ NOUVEAU
  backend_url: ''        // ✅ NOUVEAU
});
```

#### **2. Ajout des imports d'icônes (ligne 1) :**
```javascript
import { 
  Shield, 
  Users as UsersIcon, 
  Key, 
  RefreshCw, 
  Eye, 
  EyeOff, 
  Mail,
  AlertTriangle,
  CheckCircle,
  Clock,
  Save,
  AlertCircle,    // ✅ NOUVEAU
  Globe           // ✅ NOUVEAU
} from 'lucide-react';
```

#### **3. Ajout de la section formulaire (après "Nom expéditeur") :**
```jsx
{/* Section Adresses IP / URLs */}
<div className="mt-6 pt-6 border-t border-gray-200">
  <h3 className="text-md font-semibold text-gray-900 mb-4 flex items-center gap-2">
    <Globe className="h-5 w-5 text-gray-600" />
    Configuration des URLs de l'application
  </h3>
  <p className="text-sm text-gray-600 mb-4">
    Ces URLs sont utilisées pour les liens dans les emails et la sécurité CORS
  </p>
  
  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
    {/* URL Frontend */}
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">
        URL Frontend (Interface utilisateur) <span className="text-red-500">*</span>
      </label>
      <input
        type="url"
        value={smtpConfig.frontend_url}
        onChange={(e) => setSmtpConfig({...smtpConfig, frontend_url: e.target.value})}
        placeholder="https://votre-domaine.com"
        className="w-full px-4 py-2 border border-gray-300 rounded-lg..."
      />
      <p className="text-xs text-gray-500 mt-1">
        Exemple : https://gmao-iris-1.preview.emergentagent.com
      </p>
    </div>

    {/* URL Backend */}
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">
        URL Backend (API) <span className="text-red-500">*</span>
      </label>
      <input
        type="url"
        value={smtpConfig.backend_url}
        onChange={(e) => setSmtpConfig({...smtpConfig, backend_url: e.target.value})}
        placeholder="https://votre-domaine.com"
        className="w-full px-4 py-2 border border-gray-300 rounded-lg..."
      />
      <p className="text-xs text-gray-500 mt-1">
        Exemple : https://gmao-iris-1.preview.emergentagent.com
      </p>
    </div>
  </div>

  {/* Message d'avertissement */}
  <div className="mt-4 bg-amber-50 border border-amber-200 rounded-lg p-4">
    <div className="flex items-start gap-2">
      <AlertCircle className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" />
      <div className="text-sm text-amber-800">
        <p className="font-semibold mb-1">⚠️ Important :</p>
        <ul className="list-disc list-inside space-y-1">
          <li>Ces URLs doivent correspondre au domaine ou à l'adresse IP de votre serveur</li>
          <li>Modifiez ces paramètres seulement si vous avez changé de domaine ou d'IP</li>
          <li>Un redémarrage de l'application peut être nécessaire après modification</li>
        </ul>
      </div>
    </div>
  </div>
</div>
```

---

## 🔧 MODIFICATIONS BACKEND

### **Fichier :** `/app/backend/models.py`

#### **Ajout des champs dans les modèles (lignes 1057-1075) :**

```python
class SMTPConfig(BaseModel):
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_from_name: str = "GMAO Iris"
    smtp_use_tls: bool = True
    frontend_url: str = ""      # ✅ NOUVEAU
    backend_url: str = ""        # ✅ NOUVEAU

class SMTPConfigUpdate(BaseModel):
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: Optional[str] = None
    smtp_from_name: Optional[str] = None
    smtp_use_tls: Optional[bool] = None
    frontend_url: Optional[str] = None   # ✅ NOUVEAU
    backend_url: Optional[str] = None    # ✅ NOUVEAU
```

### **Fichier :** `/app/backend/server.py`

#### **1. Endpoint GET /smtp/config (ligne 2424) :**
```python
@api_router.get("/smtp/config")
async def get_smtp_config(current_user: dict = Depends(get_current_admin_user)):
    """Récupérer la configuration SMTP actuelle (Admin uniquement)"""
    try:
        config = SMTPConfig(
            smtp_host=os.environ.get('SMTP_HOST', 'smtp.gmail.com'),
            smtp_port=int(os.environ.get('SMTP_PORT', '587')),
            smtp_user=os.environ.get('SMTP_USER', ''),
            smtp_password='****' if os.environ.get('SMTP_PASSWORD') else '',
            smtp_from_email=os.environ.get('SMTP_FROM_EMAIL', ''),
            smtp_from_name=os.environ.get('SMTP_FROM_NAME', 'GMAO Iris'),
            smtp_use_tls=os.environ.get('SMTP_USE_TLS', 'true').lower() == 'true',
            frontend_url=os.environ.get('FRONTEND_URL', ''),     # ✅ NOUVEAU
            backend_url=os.environ.get('BACKEND_URL', '')        # ✅ NOUVEAU
        )
        return config
```

#### **2. Endpoint PUT /smtp/config (ligne 2462) :**
```python
# Mettre à jour les variables
if smtp_update.smtp_host is not None:
    env_vars['SMTP_HOST'] = smtp_update.smtp_host
# ... autres champs ...
if smtp_update.frontend_url is not None:         # ✅ NOUVEAU
    env_vars['FRONTEND_URL'] = smtp_update.frontend_url
if smtp_update.backend_url is not None:          # ✅ NOUVEAU
    env_vars['BACKEND_URL'] = smtp_update.backend_url
```

---

## 🚀 UTILISATION

### **Accès à la page :**
1. Se connecter en tant qu'**administrateur**
2. Aller dans **"Paramètres spéciaux"** (menu sidebar)
3. Scroller jusqu'à la section **"Configuration SMTP (Email)"**
4. Après les champs SMTP standards, trouver la section **"Configuration des URLs de l'application"**

### **Modification des URLs :**
1. Remplir **"URL Frontend (Interface utilisateur)"** :
   - Exemple : `https://gmao-iris-1.preview.emergentagent.com`
   - Correspond à l'adresse où les utilisateurs accèdent à l'interface

2. Remplir **"URL Backend (API)"** :
   - Exemple : `https://gmao-iris-1.preview.emergentagent.com`
   - Généralement identique au Frontend (même domaine)

3. Cliquer sur **"Sauvegarder la configuration SMTP"**

4. ⚠️ **Important** : Un redémarrage du backend peut être nécessaire pour appliquer les changements CORS

---

## 📝 IMPACT DES MODIFICATIONS

### **1. Sécurité CORS :**
Les URLs configurées sont utilisées pour définir les origines autorisées dans la configuration CORS du backend. Seules ces origines peuvent faire des requêtes à l'API.

### **2. Emails de notification :**
Les liens dans les emails (réinitialisation de mot de passe, notifications, etc.) utilisent l'URL Frontend configurée.

### **3. Authentification :**
Les redirections après login/logout utilisent ces URLs.

---

## ⚠️ AVERTISSEMENTS AFFICHÉS

**Message d'avertissement dans l'interface :**
```
⚠️ Important :
• Ces URLs doivent correspondre au domaine ou à l'adresse IP de votre serveur
• Modifiez ces paramètres seulement si vous avez changé de domaine ou d'IP
• Un redémarrage de l'application peut être nécessaire après modification
```

---

## ✅ TESTS EFFECTUÉS

- ✅ Backend redémarré sans erreur
- ✅ Endpoints GET et PUT /smtp/config fonctionnels
- ✅ Champs frontend_url et backend_url sauvegardés dans .env
- ✅ Interface affiche correctement les nouveaux champs
- ✅ Validation frontend (type="url") active

---

## 📁 FICHIERS MODIFIÉS (3 fichiers)

1. `/app/frontend/src/pages/SpecialSettings.jsx`
   - Ajout des champs frontend_url et backend_url dans l'état
   - Ajout de la section formulaire avec 2 inputs
   - Ajout des imports AlertCircle et Globe

2. `/app/backend/models.py`
   - Ajout frontend_url et backend_url dans SMTPConfig
   - Ajout frontend_url et backend_url dans SMTPConfigUpdate

3. `/app/backend/server.py`
   - Lecture des variables FRONTEND_URL et BACKEND_URL dans GET /smtp/config
   - Sauvegarde des variables dans PUT /smtp/config

---

## 🔄 REDÉMARRAGE NÉCESSAIRE ?

**Après modification des URLs :**
- ✅ Les variables sont sauvegardées dans `/app/backend/.env`
- ✅ Les variables sont mises à jour en mémoire dans le processus backend
- ⚠️ Pour que le CORS prenne effet, **redémarrer le backend** :
  ```bash
  sudo supervisorctl restart backend
  ```

---

## 📝 EXEMPLE DE CONFIGURATION

**Configuration type pour une installation :**
```
URL Frontend : https://votre-domaine.com
URL Backend  : https://votre-domaine.com
```

**Ou avec adresse IP :**
```
URL Frontend : http://192.168.1.100:3000
URL Backend  : http://192.168.1.100:8001
```

**Ou en local (développement) :**
```
URL Frontend : http://localhost:3000
URL Backend  : http://localhost:8001
```

---

## 🚀 PRÊT POUR GITHUB

```bash
cd /app
git add frontend/src/pages/SpecialSettings.jsx
git add backend/models.py
git add backend/server.py
git commit -m "feat: Ajout configuration URLs dans Paramètres SMTP

- Ajout champs frontend_url et backend_url dans la section SMTP
- Permet de modifier les URLs depuis l'interface admin
- Sauvegarde automatique dans le fichier .env
- Message d'avertissement pour les modifications sensibles"
git push origin main
```

---

**✅ Configuration des URLs maintenant modifiable depuis l'interface !**
