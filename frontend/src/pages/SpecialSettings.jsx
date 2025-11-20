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
  Save,
  AlertCircle,
  Globe
} from 'lucide-react';
import api, { usersAPI } from '../services/api';
import { useToast } from '../hooks/use-toast';
import { useConfirmDialog } from '../components/ui/confirm-dialog';
import { formatErrorMessage } from '../utils/errorFormatter';

const SpecialSettings = () => {
  const { confirm, ConfirmDialog } = useConfirmDialog();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [resetting, setResetting] = useState(null);
  const [tempPassword, setTempPassword] = useState(null);
  const [showPassword, setShowPassword] = useState(false);
  const [inactivityTimeout, setInactivityTimeout] = useState(15);
  const [loadingSettings, setLoadingSettings] = useState(true);
  const [savingSettings, setSavingSettings] = useState(false);
  
  // États SMTP
  const [smtpConfig, setSmtpConfig] = useState({
    smtp_host: '',
    smtp_port: 587,
    smtp_user: '',
    smtp_password: '',
    smtp_from_email: '',
    smtp_from_name: 'GMAO Iris',
    smtp_use_tls: true,
    frontend_url: '',
    backend_url: ''
  });
  const [loadingSmtp, setLoadingSmtp] = useState(true);
  const [savingSmtp, setSavingSmtp] = useState(false);
  const [testingSmtp, setTestingSmtp] = useState(false);
  const [testEmail, setTestEmail] = useState('');
  const [showSmtpPassword, setShowSmtpPassword] = useState(false);
  
  // États Tailscale
  const [tailscaleIP, setTailscaleIP] = useState('');
  const [loadingTailscale, setLoadingTailscale] = useState(true);
  const [savingTailscale, setSavingTailscale] = useState(false);
  const [restoringTailscale, setRestoringTailscale] = useState(false);
  const [tailscaleStatus, setTailscaleStatus] = useState(null);
  
  const { toast } = useToast();

  useEffect(() => {
    loadUsers();
    loadSettings();
    loadSmtpConfig();
    loadTailscaleConfig();
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
        description: formatErrorMessage(error, 'Impossible de sauvegarder les paramètres'),
        variant: 'destructive'
      });
    } finally {
      setSavingSettings(false);
    }
  };



  // Fonctions SMTP
  const loadSmtpConfig = async () => {
    try {
      setLoadingSmtp(true);
      const response = await api.get('/smtp/config');
      setSmtpConfig(response.data);
      // Initialiser l'email de test avec l'email de l'utilisateur connecté
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      if (user.email) {
        setTestEmail(user.email);
      }
    } catch (error) {
      toast({
        title: 'Erreur',
        description: 'Impossible de charger la configuration SMTP',
        variant: 'destructive'
      });
    } finally {
      setLoadingSmtp(false);
    }
  };

  const handleSaveSmtpConfig = async () => {
    try {
      setSavingSmtp(true);
      await api.put('/smtp/config', smtpConfig);
      
      toast({
        title: 'Configuration sauvegardée',
        description: 'La configuration SMTP a été mise à jour avec succès',
      });
    } catch (error) {
      toast({
        title: 'Erreur',
        description: formatErrorMessage(error, 'Impossible de sauvegarder la configuration SMTP'),
        variant: 'destructive'
      });
    } finally {
      setSavingSmtp(false);
    }
  };

  const handleTestSmtp = async () => {
    if (!testEmail || !testEmail.includes('@')) {
      toast({
        title: 'Email invalide',
        description: 'Veuillez entrer une adresse email valide',
        variant: 'destructive'
      });
      return;
    }

    try {
      setTestingSmtp(true);
      const response = await api.post('/smtp/test', {
        test_email: testEmail
      });
      
      if (response.data.success) {
        toast({
          title: 'Test réussi',
          description: `Email de test envoyé avec succès à ${testEmail}`,
        });
      } else {
        toast({
          title: 'Test échoué',
          description: response.data.message || 'L\'envoi de l\'email de test a échoué',
          variant: 'destructive'
        });
      }
    } catch (error) {
      toast({
        title: 'Erreur',
        description: formatErrorMessage(error, 'Erreur lors du test SMTP'),
        variant: 'destructive'
      });
    } finally {
      setTestingSmtp(false);
    }
  };

  // Fonctions Tailscale
  const loadTailscaleConfig = async () => {
    try {
      setLoadingTailscale(true);
      const response = await api.get('/tailscale/config');
      setTailscaleIP(response.data.tailscale_ip || '');
      setTailscaleStatus(response.data.status);
    } catch (error) {
      console.error('Erreur chargement config Tailscale:', error);
      // Pas de toast d'erreur car cette fonctionnalité n'est peut-être pas disponible sur tous les environnements
    } finally {
      setLoadingTailscale(false);
    }
  };

  const handleSaveTailscaleConfig = () => {
    // Validation de l'IP
    const ipRegex = /^(\d{1,3}\.){3}\d{1,3}$/;
    if (!ipRegex.test(tailscaleIP)) {
      toast({
        title: 'IP invalide',
        description: 'Veuillez entrer une adresse IP valide (ex: 100.105.2.113)',
        variant: 'destructive'
      });
      return;
    }

    const parts = tailscaleIP.split('.');
    if (parts.some(part => parseInt(part) > 255)) {
      toast({
        title: 'IP invalide',
        description: 'Chaque partie de l\'IP doit être entre 0 et 255',
        variant: 'destructive'
      });
      return;
    }

    // Utiliser le pattern confirm avec callback
    confirm({
      title: 'Modifier l\'adresse IP Tailscale',
      description: `Êtes-vous sûr de vouloir changer l'IP en ${tailscaleIP} ?\n\n⚠️ Cette action va :\n\n- Modifier le fichier .env du frontend\n- Recompiler l'application (1-2 minutes)\n- Redémarrer les services\n\nVous devrez peut-être rafraîchir votre navigateur après.`,
      confirmText: 'Confirmer et Appliquer',
      cancelText: 'Annuler',
      variant: 'default',
      onConfirm: async () => {
        try {
          setSavingTailscale(true);
          const response = await api.post('/tailscale/configure', {
            tailscale_ip: tailscaleIP
          });
          
          if (response.data.success) {
            toast({
              title: '⏳ Configuration en cours...',
              description: `L'IP Tailscale est en cours de configuration (${tailscaleIP}). Le système va se recharger dans 30 secondes. ATTENDEZ au moins 2 minutes avant de tester !`,
              duration: 30000, // 30 secondes
            });
            
            // Recharger la page après 30 secondes pour laisser le temps au backend
            setTimeout(() => {
              window.location.href = `http://${tailscaleIP}`;
            }, 30000);
          } else {
            toast({
              title: 'Erreur',
              description: response.data.message || 'La configuration a échoué',
              variant: 'destructive'
            });
          }
        } catch (error) {
          toast({
            title: 'Erreur',
            description: formatErrorMessage(error, 'Impossible de modifier la configuration Tailscale'),
            variant: 'destructive'
          });
        } finally {
          setSavingTailscale(false);
        }
      }
    });
  };

  const handleRestoreTailscaleConfig = () => {
    confirm({
      title: 'Restaurer la configuration précédente',
      description: 'Êtes-vous sûr de vouloir restaurer la configuration IP précédente ?\n\n⚠️ Cette action va :\n\n- Restaurer l\'ancien fichier .env\n- Recompiler l\'application (1-2 minutes)\n- Redémarrer les services\n\nUtilisez cette fonction si vous rencontrez des problèmes après un changement d\'IP.',
      confirmText: 'Restaurer',
      cancelText: 'Annuler',
      variant: 'default',
      onConfirm: async () => {
        try {
          setRestoringTailscale(true);
          const response = await api.post('/tailscale/restore');
          
          if (response.data.success) {
            toast({
              title: 'Configuration restaurée',
              description: 'La configuration précédente a été restaurée. Rechargement de la page dans 3 secondes...',
            });
            
            setTimeout(() => {
              window.location.reload();
            }, 3000);
          } else {
            toast({
              title: 'Erreur',
              description: response.data.message || 'La restauration a échoué',
              variant: 'destructive'
            });
          }
        } catch (error) {
          toast({
            title: 'Erreur',
            description: formatErrorMessage(error, 'Impossible de restaurer la configuration'),
            variant: 'destructive'
          });
        } finally {
          setRestoringTailscale(false);
        }
      }
    });
  };

  const handleResetPassword = async (userId, userName) => {
    confirm({
      title: 'Réinitialiser le mot de passe',
      description: `Êtes-vous sûr de vouloir réinitialiser le mot de passe de ${userName} ?\n\nUn nouveau mot de passe temporaire sera généré.`,
      confirmText: 'Réinitialiser',
      cancelText: 'Annuler',
      variant: 'default',
      onConfirm: async () => {
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
            description: formatErrorMessage(error, 'Impossible de réinitialiser le mot de passe'),
            variant: 'destructive'
          });
        } finally {
          setResetting(null);
        }
      }
    });
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

      {/* Section Configuration Tailscale */}
      <div className="mt-6 bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="border-b border-gray-200 px-6 py-4">
          <div className="flex items-center gap-2">
            <Globe className="h-5 w-5 text-gray-600" />
            <h2 className="text-lg font-semibold text-gray-900">Configuration Tailscale (IP)</h2>
          </div>
          <p className="text-sm text-gray-600 mt-1">
            Modifier l'adresse IP Tailscale pour l'accès à distance (Proxmox uniquement)
          </p>
        </div>

        <div className="p-6">
          {loadingTailscale ? (
            <div className="text-center py-8">
              <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-2" />
              <p className="text-gray-600">Chargement de la configuration...</p>
            </div>
          ) : (
            <div className="max-w-2xl">
              {/* Info Box */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                <div className="flex items-start gap-2">
                  <Globe className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-blue-800">
                    <p className="font-semibold mb-1">À propos de cette fonctionnalité :</p>
                    <ul className="list-disc list-inside space-y-1">
                      <li>Cette fonction remplace le script SSH "configure-tailscale.sh"</li>
                      <li>Modifie automatiquement l'URL du backend pour Tailscale</li>
                      <li>L'application sera recompilée (1-2 minutes)</li>
                      <li><strong>Fonctionne uniquement sur le serveur Proxmox</strong></li>
                    </ul>
                  </div>
                </div>
              </div>

              {/* Status actuel si disponible */}
              {tailscaleStatus && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-5 w-5 text-green-600" />
                    <div>
                      <p className="text-sm font-semibold text-green-800">Configuration actuelle</p>
                      <p className="text-sm text-green-700 mt-1">
                        IP Tailscale : <span className="font-mono font-semibold">{tailscaleStatus.current_ip || 'Non configuré'}</span>
                      </p>
                      {tailscaleStatus.backend_url && (
                        <p className="text-xs text-green-600 mt-1">
                          URL Backend : {tailscaleStatus.backend_url}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Formulaire */}
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Adresse IP Tailscale <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={tailscaleIP}
                    onChange={(e) => setTailscaleIP(e.target.value)}
                    placeholder="Ex: 100.105.2.113"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-lg"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Format : XXX.XXX.XXX.XXX (chaque partie entre 0 et 255)
                  </p>
                </div>

                {/* Avertissement */}
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                  <div className="flex items-start gap-2">
                    <AlertTriangle className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" />
                    <div className="text-sm text-amber-800">
                      <p className="font-semibold mb-1">⚠️ Attention :</p>
                      <ul className="list-disc list-inside space-y-1">
                        <li>Cette modification recompilera le frontend (1-2 minutes)</li>
                        <li>Les services backend et nginx seront redémarrés</li>
                        <li>Vous devrez rafraîchir votre navigateur après (F5)</li>
                        <li>Assurez-vous que l'IP est correcte avant de confirmer</li>
                        <li><strong>ATTENDEZ 2 minutes complètes avant de tester</strong></li>
                      </ul>
                    </div>
                  </div>
                </div>

                {/* Guide de dépannage */}
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="flex items-start gap-2">
                    <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
                    <div className="text-sm text-red-800">
                      <p className="font-semibold mb-1">🆘 Si vous voyez "Bad Gateway" après le changement :</p>
                      <ol className="list-decimal list-inside space-y-1 ml-2">
                        <li><strong>Attendez 2 minutes complètes</strong> - Le backend met du temps à démarrer</li>
                        <li>Rafraîchissez votre navigateur (Ctrl+F5 ou Cmd+Shift+R)</li>
                        <li>Utilisez le bouton <span className="font-semibold">"Restaurer l'ancienne IP"</span> (bouton orange)</li>
                        <li>Si le problème persiste, connectez-vous en SSH et exécutez :
                          <code className="block bg-red-100 p-2 mt-1 rounded text-xs">
                            cd /opt/gmao-iris/frontend && cp .env.backup .env && yarn build && systemctl restart nginx
                          </code>
                        </li>
                      </ol>
                    </div>
                  </div>
                </div>

                {/* Boutons */}
                <div className="grid grid-cols-2 gap-4">
                  <button
                    onClick={handleRestoreTailscaleConfig}
                    disabled={restoringTailscale || savingTailscale}
                    className="flex items-center justify-center gap-2 px-6 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                  >
                    {restoringTailscale ? (
                      <>
                        <RefreshCw className="h-5 w-5 animate-spin" />
                        <span>Restauration...</span>
                      </>
                    ) : (
                      <>
                        <RefreshCw className="h-5 w-5" />
                        <span>Restaurer l'ancienne IP</span>
                      </>
                    )}
                  </button>
                  
                  <button
                    onClick={handleSaveTailscaleConfig}
                    disabled={savingTailscale || restoringTailscale || !tailscaleIP}
                    className="flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                  >
                    {savingTailscale ? (
                      <>
                        <RefreshCw className="h-5 w-5 animate-spin" />
                        <span>Configuration en cours (1-2 min)...</span>
                      </>
                    ) : (
                      <>
                        <Save className="h-5 w-5" />
                        <span>Appliquer la nouvelle IP</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Section Configuration SMTP */}
      <div className="mt-6 bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="border-b border-gray-200 px-6 py-4">
          <div className="flex items-center gap-2">
            <Mail className="h-5 w-5 text-gray-600" />
            <h2 className="text-lg font-semibold text-gray-900">Configuration SMTP (Email)</h2>
          </div>
          <p className="text-sm text-gray-600 mt-1">
            Configurer les paramètres d'envoi d'emails pour les notifications et alertes
          </p>
        </div>

        <div className="p-6">
          {loadingSmtp ? (
            <div className="text-center py-8">
              <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-2" />
              <p className="text-gray-600">Chargement de la configuration SMTP...</p>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Info Box */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-start gap-2">
                  <Mail className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-blue-800">
                    <p className="font-semibold mb-1">Configuration recommandée pour Gmail :</p>
                    <ul className="list-disc list-inside space-y-1">
                      <li>Serveur SMTP : smtp.gmail.com</li>
                      <li>Port : 587 (TLS activé)</li>
                      <li>Utiliser un "Mot de passe d'application" (pas votre mot de passe Gmail principal)</li>
                      <li><a href="https://support.google.com/accounts/answer/185833" target="_blank" rel="noopener noreferrer" className="underline hover:text-blue-900">Comment créer un mot de passe d'application Gmail</a></li>
                    </ul>
                  </div>
                </div>
              </div>

              {/* Formulaire de configuration */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Serveur SMTP */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Serveur SMTP <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={smtpConfig.smtp_host}
                    onChange={(e) => setSmtpConfig({...smtpConfig, smtp_host: e.target.value})}
                    placeholder="smtp.gmail.com"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                {/* Port */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Port SMTP <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="number"
                    value={smtpConfig.smtp_port}
                    onChange={(e) => setSmtpConfig({...smtpConfig, smtp_port: parseInt(e.target.value)})}
                    placeholder="587"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                {/* Utilisateur / Email */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Nom d'utilisateur / Email <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={smtpConfig.smtp_user}
                    onChange={(e) => setSmtpConfig({...smtpConfig, smtp_user: e.target.value})}
                    placeholder="votre-email@gmail.com"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                {/* Mot de passe */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Mot de passe <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <input
                      type={showSmtpPassword ? "text" : "password"}
                      value={smtpConfig.smtp_password}
                      onChange={(e) => setSmtpConfig({...smtpConfig, smtp_password: e.target.value})}
                      placeholder="Mot de passe d'application"
                      className="w-full px-4 py-2 pr-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                    <button
                      type="button"
                      onClick={() => setShowSmtpPassword(!showSmtpPassword)}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
                    >
                      {showSmtpPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                    </button>
                  </div>
                </div>

                {/* Email expéditeur */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Email expéditeur <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="email"
                    value={smtpConfig.smtp_from_email}
                    onChange={(e) => setSmtpConfig({...smtpConfig, smtp_from_email: e.target.value})}
                    placeholder="noreply@votre-entreprise.com"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                {/* Nom expéditeur */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Nom expéditeur
                  </label>
                  <input
                    type="text"
                    value={smtpConfig.smtp_from_name}
                    onChange={(e) => setSmtpConfig({...smtpConfig, smtp_from_name: e.target.value})}
                    placeholder="GMAO Iris"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>

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
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Exemple : https://surveil-plan.preview.emergentagent.com
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
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Exemple : https://surveil-plan.preview.emergentagent.com
                    </p>
                  </div>
                </div>

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

              {/* Utiliser TLS */}
              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  id="smtp_use_tls"
                  checked={smtpConfig.smtp_use_tls}
                  onChange={(e) => setSmtpConfig({...smtpConfig, smtp_use_tls: e.target.checked})}
                  className="w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <label htmlFor="smtp_use_tls" className="text-sm font-medium text-gray-700">
                  Utiliser TLS/STARTTLS (recommandé)
                </label>
              </div>

              {/* Bouton Sauvegarder */}
              <div className="flex items-center gap-4 pt-4 border-t border-gray-200">
                <button
                  onClick={handleSaveSmtpConfig}
                  disabled={savingSmtp}
                  className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                >
                  {savingSmtp ? (
                    <>
                      <RefreshCw className="h-5 w-5 animate-spin" />
                      <span>Sauvegarde...</span>
                    </>
                  ) : (
                    <>
                      <Save className="h-5 w-5" />
                      <span>Sauvegarder la configuration</span>
                    </>
                  )}
                </button>
              </div>

              {/* Section Test */}
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mt-6">
                <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
                  <CheckCircle className="h-5 w-5 text-green-600" />
                  Tester la configuration
                </h3>
                <p className="text-sm text-gray-600 mb-4">
                  Envoyez un email de test pour vérifier que la configuration fonctionne correctement
                </p>
                <div className="flex items-end gap-4">
                  <div className="flex-1">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Adresse email de test
                    </label>
                    <input
                      type="email"
                      value={testEmail}
                      onChange={(e) => setTestEmail(e.target.value)}
                      placeholder="votre-email@example.com"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    />
                  </div>
                  <button
                    onClick={handleTestSmtp}
                    disabled={testingSmtp || !testEmail}
                    className="flex items-center gap-2 px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                  >
                    {testingSmtp ? (
                      <>
                        <RefreshCw className="h-5 w-5 animate-spin" />
                        <span>Envoi...</span>
                      </>
                    ) : (
                      <>
                        <Mail className="h-5 w-5" />
                        <span>Envoyer un test</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Confirm Dialog */}
      <ConfirmDialog />
    </div>
  );
};

export default SpecialSettings;
