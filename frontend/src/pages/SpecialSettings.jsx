import React, { useState, useEffect } from 'react';
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
  Save
} from 'lucide-react';
import api, { usersAPI } from '../services/api';
import { useToast } from '../hooks/use-toast';

const SpecialSettings = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [resetting, setResetting] = useState(null);
  const [tempPassword, setTempPassword] = useState(null);
  const [showPassword, setShowPassword] = useState(false);
  const [inactivityTimeout, setInactivityTimeout] = useState(15);
  const [loadingSettings, setLoadingSettings] = useState(true);
  const [savingSettings, setSavingSettings] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    loadUsers();
    loadSettings();
  }, []);

  const loadUsers = async () => {
    try {
      setLoading(true);
      const response = await usersAPI.getAll();
      setUsers(response.data);
    } catch (error) {
      toast({
        title: 'Erreur',
        description: 'Impossible de charger la liste des utilisateurs',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const loadSettings = async () => {
    try {
      setLoadingSettings(true);
      const response = await api.settings.getSettings();
      setInactivityTimeout(response.data.inactivity_timeout_minutes);
    } catch (error) {
      toast({
        title: 'Erreur',
        description: 'Impossible de charger les paramètres système',
        variant: 'destructive'
      });
    } finally {
      setLoadingSettings(false);
    }
  };

  const handleSaveSettings = async () => {
    if (inactivityTimeout < 1 || inactivityTimeout > 120) {
      toast({
        title: 'Erreur',
        description: 'Le temps d\'inactivité doit être entre 1 et 120 minutes',
        variant: 'destructive'
      });
      return;
    }

    try {
      setSavingSettings(true);
      await api.settings.updateSettings({
        inactivity_timeout_minutes: inactivityTimeout
      });
      
      toast({
        title: 'Paramètres sauvegardés',
        description: 'Les paramètres de déconnexion automatique ont été mis à jour',
      });

      // Recharger la page pour appliquer les nouveaux paramètres
      setTimeout(() => {
        window.location.reload();
      }, 1500);
    } catch (error) {
      toast({
        title: 'Erreur',
        description: error.response?.data?.detail || 'Impossible de sauvegarder les paramètres',
        variant: 'destructive'
      });
    } finally {
      setSavingSettings(false);
    }
  };

  const handleResetPassword = async (userId, userName) => {
    if (!window.confirm(`Êtes-vous sûr de vouloir réinitialiser le mot de passe de ${userName} ?`)) {
      return;
    }

    try {
      setResetting(userId);
      const response = await usersAPI.resetPasswordByAdmin(userId);
      
      setTempPassword({
        userId,
        userName,
        password: response.data.tempPassword
      });

      toast({
        title: 'Mot de passe réinitialisé',
        description: `Un nouveau mot de passe temporaire a été généré pour ${userName}`,
      });

      loadUsers(); // Recharger pour mettre à jour firstLogin
    } catch (error) {
      toast({
        title: 'Erreur',
        description: error.response?.data?.detail || 'Impossible de réinitialiser le mot de passe',
        variant: 'destructive'
      });
    } finally {
      setResetting(null);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast({
      title: 'Copié',
      description: 'Mot de passe copié dans le presse-papiers',
    });
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="bg-red-100 p-3 rounded-lg">
            <Shield className="h-6 w-6 text-red-600" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Paramètres Spéciaux</h1>
            <p className="text-gray-600">Gestion avancée de l'application (Admin uniquement)</p>
          </div>
        </div>
      </div>

      {/* Avertissement de sécurité */}
      <div className="bg-orange-50 border-l-4 border-orange-400 p-4 mb-6">
        <div className="flex items-start">
          <AlertTriangle className="h-5 w-5 text-orange-400 mt-0.5 mr-3 flex-shrink-0" />
          <div>
            <h3 className="text-sm font-medium text-orange-800">Zone de sécurité élevée</h3>
            <p className="text-sm text-orange-700 mt-1">
              Cette section contient des fonctionnalités critiques. Utilisez-les avec précaution.
              Toutes les actions sont enregistrées dans le journal d'audit.
            </p>
          </div>
        </div>
      </div>

      {/* Popup de mot de passe temporaire */}
      {tempPassword && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4 shadow-2xl">
            <div className="flex items-center gap-3 mb-4">
              <div className="bg-green-100 p-3 rounded-full">
                <CheckCircle className="h-6 w-6 text-green-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Mot de passe réinitialisé</h3>
                <p className="text-sm text-gray-600">{tempPassword.userName}</p>
              </div>
            </div>

            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
              <div className="flex items-start gap-2 mb-3">
                <AlertTriangle className="h-5 w-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                <div className="text-sm text-yellow-800">
                  <p className="font-semibold mb-1">Important :</p>
                  <ul className="list-disc list-inside space-y-1">
                    <li>Ce mot de passe ne sera affiché qu'UNE SEULE FOIS</li>
                    <li>Notez-le et communiquez-le à l'utilisateur de manière sécurisée</li>
                    <li>L'utilisateur devra le changer à sa prochaine connexion</li>
                  </ul>
                </div>
              </div>

              <div className="relative">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Mot de passe temporaire :
                </label>
                <div className="flex gap-2">
                  <input
                    type={showPassword ? "text" : "password"}
                    value={tempPassword.password}
                    readOnly
                    className="flex-1 px-4 py-3 bg-white border border-gray-300 rounded-lg font-mono text-lg"
                  />
                  <button
                    onClick={() => setShowPassword(!showPassword)}
                    className="px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                  </button>
                  <button
                    onClick={() => copyToClipboard(tempPassword.password)}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  >
                    Copier
                  </button>
                </div>
              </div>
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => setTempPassword(null)}
                className="flex-1 px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800"
              >
                J'ai noté le mot de passe
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Section Gestion des utilisateurs */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="border-b border-gray-200 px-6 py-4">
          <div className="flex items-center gap-2">
            <UsersIcon className="h-5 w-5 text-gray-600" />
            <h2 className="text-lg font-semibold text-gray-900">Gestion des Utilisateurs</h2>
          </div>
          <p className="text-sm text-gray-600 mt-1">
            Réinitialiser les mots de passe des utilisateurs en cas de perte
          </p>
        </div>

        <div className="p-6">
          {loading ? (
            <div className="text-center py-8">
              <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-2" />
              <p className="text-gray-600">Chargement des utilisateurs...</p>
            </div>
          ) : (
            <div className="space-y-3">
              {users.map((user) => (
                <div
                  key={user.id}
                  className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
                >
                  <div className="flex items-center gap-4 flex-1">
                    <div className="bg-blue-100 p-2 rounded-full">
                      <UsersIcon className="h-5 w-5 text-blue-600" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-gray-900">
                          {user.prenom} {user.nom}
                        </h3>
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          user.role === 'ADMIN' ? 'bg-red-100 text-red-700' :
                          user.role === 'TECHNICIEN' ? 'bg-blue-100 text-blue-700' :
                          'bg-gray-100 text-gray-700'
                        }`}>
                          {user.role}
                        </span>
                        {user.firstLogin && (
                          <span className="px-2 py-1 text-xs rounded-full bg-orange-100 text-orange-700">
                            Premier login requis
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-600">{user.email}</p>
                    </div>
                  </div>

                  <button
                    onClick={() => handleResetPassword(user.id, `${user.prenom} ${user.nom}`)}
                    disabled={resetting === user.id}
                    className="flex items-center gap-2 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                  >
                    {resetting === user.id ? (
                      <>
                        <RefreshCw className="h-4 w-4 animate-spin" />
                        <span>Réinitialisation...</span>
                      </>
                    ) : (
                      <>
                        <Key className="h-4 w-4" />
                        <span>Réinitialiser le mot de passe</span>
                      </>
                    )}
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Section Paramètres de sécurité */}
      <div className="mt-6 bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="border-b border-gray-200 px-6 py-4">
          <div className="flex items-center gap-2">
            <Clock className="h-5 w-5 text-gray-600" />
            <h2 className="text-lg font-semibold text-gray-900">Déconnexion Automatique</h2>
          </div>
          <p className="text-sm text-gray-600 mt-1">
            Configurer le temps d'inactivité avant déconnexion automatique
          </p>
        </div>

        <div className="p-6">
          {loadingSettings ? (
            <div className="text-center py-8">
              <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-2" />
              <p className="text-gray-600">Chargement des paramètres...</p>
            </div>
          ) : (
            <div className="max-w-2xl">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                <div className="flex items-start gap-2">
                  <Clock className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-blue-800">
                    <p className="font-semibold mb-1">Fonctionnement :</p>
                    <ul className="list-disc list-inside space-y-1">
                      <li>Les utilisateurs inactifs seront avertis 60 secondes avant la déconnexion</li>
                      <li>Ils peuvent cliquer sur "Rester connecté" pour prolonger leur session</li>
                      <li>Cette mesure améliore la sécurité des postes partagés</li>
                    </ul>
                  </div>
                </div>
              </div>

              <div className="flex items-end gap-4">
                <div className="flex-1">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Temps d'inactivité (minutes)
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="120"
                    value={inactivityTimeout}
                    onChange={(e) => setInactivityTimeout(parseInt(e.target.value))}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-lg"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Valeur actuelle : {inactivityTimeout} minute{inactivityTimeout > 1 ? 's' : ''}
                    {' '}(min: 1, max: 120)
                  </p>
                </div>

                <button
                  onClick={handleSaveSettings}
                  disabled={savingSettings || inactivityTimeout < 1 || inactivityTimeout > 120}
                  className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                >
                  {savingSettings ? (
                    <>
                      <RefreshCw className="h-5 w-5 animate-spin" />
                      <span>Sauvegarde...</span>
                    </>
                  ) : (
                    <>
                      <Save className="h-5 w-5" />
                      <span>Sauvegarder</span>
                    </>
                  )}
                </button>
              </div>

              {(inactivityTimeout < 1 || inactivityTimeout > 120) && (
                <div className="mt-3 bg-red-50 border border-red-200 rounded-lg p-3">
                  <p className="text-sm text-red-800">
                    ⚠️ Le temps doit être entre 1 et 120 minutes
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Autres sections futures */}
      <div className="mt-6 bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
        <Shield className="h-12 w-12 text-gray-400 mx-auto mb-3" />
        <h3 className="text-lg font-semibold text-gray-700 mb-2">
          Autres paramètres à venir
        </h3>
        <p className="text-gray-600">
          D'autres options de configuration avancée seront ajoutées ici
        </p>
      </div>
    </div>
  );
};

export default SpecialSettings;
