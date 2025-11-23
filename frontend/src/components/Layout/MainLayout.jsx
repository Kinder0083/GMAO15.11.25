import React, { useState, useEffect } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  ClipboardList,
  Package,
  MapPin,
  Wrench,
  BarChart3,
  Users,
  ShoppingCart,
  ShoppingBag,
  Calendar,
  Settings,
  Menu,
  X,
  ChevronLeft,
  ChevronRight,
  LogOut,
  Bell,
  Database,
  RefreshCw,
  FileText,
  Gauge,
  MessageSquare,
  Lightbulb,
  Sparkles,
  Shield,
  Eye,
  AlertTriangle,
  FolderOpen,
  Terminal
} from 'lucide-react';
import FirstLoginPasswordDialog from '../Common/FirstLoginPasswordDialog';
import UpdateNotificationBadge from '../Common/UpdateNotificationBadge';
import RecentUpdatePopup from '../Common/RecentUpdatePopup';
import InactivityHandler from '../Common/InactivityHandler';
import TokenValidator from '../Common/TokenValidator';
import { usePermissions } from '../../hooks/usePermissions';
import { getBackendURL } from '../../utils/config';

const MainLayout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [firstLoginDialogOpen, setFirstLoginDialogOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const [user, setUser] = useState({ nom: 'Utilisateur', role: 'VIEWER', firstLogin: false, id: '' });
  const [workOrdersCount, setWorkOrdersCount] = useState(0);
  const [overdueCount, setOverdueCount] = useState(0); // Nombre d'échéances dépassées TOTAL
  const [overdueDetails, setOverdueDetails] = useState({}); // Détails par module
  const [overdueMenuOpen, setOverdueMenuOpen] = useState(false); // Menu déroulant échéances
  // Compteurs séparés par catégorie
  const [overdueExecutionCount, setOverdueExecutionCount] = useState(0); // Work orders + Improvements (orange)
  const [overdueRequestsCount, setOverdueRequestsCount] = useState(0); // Demandes d'inter. + Demandes d'amél. (jaune)
  const [overdueMaintenanceCount, setOverdueMaintenanceCount] = useState(0); // Maintenances préventives (bleu)
  const [surveillanceBadge, setSurveillanceBadge] = useState({ echeances_proches: 0, pourcentage_realisation: 0 });
  const [inventoryStats, setInventoryStats] = useState({ rupture: 0, niveau_bas: 0 }); // Stats inventaire
  const { canView, isAdmin } = usePermissions();

  useEffect(() => {
    // Récupérer les informations de l'utilisateur depuis localStorage
    const userInfo = localStorage.getItem('user');
    if (userInfo) {
      try {
        const parsedUser = JSON.parse(userInfo);
        setUser({
          nom: `${parsedUser.prenom || ''} ${parsedUser.nom || ''}`.trim() || 'Utilisateur',
          role: parsedUser.role || 'VIEWER',
          firstLogin: parsedUser.firstLogin || false,
          id: parsedUser.id
        });
        
        // Afficher le dialog de changement de mot de passe si c'est la première connexion
        if (parsedUser.firstLogin === true) {
          setFirstLoginDialogOpen(true);
        }

        // Charger le nombre d'ordres de travail assignés
        loadWorkOrdersCount(parsedUser.id);
        // Charger le nombre d'échéances dépassées
        loadOverdueCount();
        // Charger les stats du badge de surveillance
        loadSurveillanceBadgeStats();
        // Charger les stats de l'inventaire
        loadInventoryStats();
        
        // Rafraîchir les notifications toutes les 60 secondes
        const intervalId = setInterval(() => {
          loadWorkOrdersCount(parsedUser.id);
          loadOverdueCount();
          loadSurveillanceBadgeStats();
          loadInventoryStats();
        }, 60000); // 60 secondes
        
        // Écouter les événements de création/modification/suppression
        const handleWorkOrderChange = () => {
          loadWorkOrdersCount(parsedUser.id);
          loadOverdueCount(); // Aussi rafraîchir les échéances
        };
        
        const handleSurveillanceChange = () => {
          loadSurveillanceBadgeStats();
        };
        
        window.addEventListener('workOrderCreated', handleWorkOrderChange);
        window.addEventListener('workOrderUpdated', handleWorkOrderChange);
        window.addEventListener('workOrderDeleted', handleWorkOrderChange);
        window.addEventListener('improvementCreated', handleWorkOrderChange);
        window.addEventListener('improvementUpdated', handleWorkOrderChange);
        window.addEventListener('improvementDeleted', handleWorkOrderChange);
        window.addEventListener('surveillanceItemCreated', handleSurveillanceChange);
        window.addEventListener('surveillanceItemUpdated', handleSurveillanceChange);
        window.addEventListener('surveillanceItemDeleted', handleSurveillanceChange);
        
        // Nettoyer les listeners et l'intervalle au démontage
        return () => {
          clearInterval(intervalId);
          window.removeEventListener('workOrderCreated', handleWorkOrderChange);
          window.removeEventListener('workOrderUpdated', handleWorkOrderChange);
          window.removeEventListener('workOrderDeleted', handleWorkOrderChange);
          window.removeEventListener('improvementCreated', handleWorkOrderChange);
          window.removeEventListener('improvementUpdated', handleWorkOrderChange);
          window.removeEventListener('improvementDeleted', handleWorkOrderChange);
          window.removeEventListener('surveillanceItemCreated', handleSurveillanceChange);
          window.removeEventListener('surveillanceItemUpdated', handleSurveillanceChange);
          window.removeEventListener('surveillanceItemDeleted', handleSurveillanceChange);
        };
      } catch (error) {
        console.error('Erreur lors du parsing des infos utilisateur:', error);
      }
    }
  }, []);

  // Fermer le menu des échéances quand on clique en dehors
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (overdueMenuOpen && !event.target.closest('.relative')) {
        setOverdueMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [overdueMenuOpen]);

  const loadWorkOrdersCount = async (userId) => {
    try {
      const token = localStorage.getItem('token');
      const backend_url = getBackendURL();
      
      const response = await fetch(`${backend_url}/api/work-orders`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        // Compter les ordres de travail assignés à l'utilisateur avec statut OUVERT uniquement
        // Vérifier à la fois assigne_a_id (string) et assigneA.id (objet)
        const assignedOrders = data.filter(order => {
          const isAssigned = order.assigne_a_id === userId || 
                           (order.assigneA && order.assigneA.id === userId);
          const isOpen = order.statut === 'OUVERT';
          return isAssigned && isOpen;
        });
        setWorkOrdersCount(assignedOrders.length);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des ordres de travail:', error);
    }
  };

  const loadOverdueCount = async () => {
    try {
      const token = localStorage.getItem('token');
      const backend_url = getBackendURL();
      
      // Récupérer les permissions depuis localStorage
      const userInfo = localStorage.getItem('user');
      const permissions = userInfo ? JSON.parse(userInfo).permissions : {};
      
      const canViewModule = (module) => {
        return permissions[module]?.view === true;
      };
      
      const today = new Date();
      today.setHours(23, 59, 59, 999);
      
      let total = 0;
      let executionCount = 0; // Work orders + Improvements
      let requestsCount = 0; // Demandes d'inter. + Demandes d'amél.
      let maintenanceCount = 0; // Maintenances préventives
      const details = {};
      
      // 1. Ordres de travail en retard (ORANGE)
      if (canViewModule('workOrders')) {
        try {
          const woResponse = await fetch(`${backend_url}/api/work-orders`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          if (woResponse.ok) {
            const workOrders = await woResponse.json();
            const overdueWO = workOrders.filter(wo => {
              if (!wo.dateLimite || wo.statut === 'TERMINE' || wo.statut === 'ANNULE') return false;
              const dueDate = new Date(wo.dateLimite);
              return dueDate < today;
            });
            if (overdueWO.length > 0) {
              details.workOrders = {
                count: overdueWO.length,
                label: 'Ordres de travail',
                route: '/work-orders',
                category: 'execution'
              };
              executionCount += overdueWO.length;
              total += overdueWO.length;
            }
          }
        } catch (err) {
          console.error('Erreur work orders:', err);
        }
      }
      
      // 2. Améliorations en retard (ORANGE)
      if (canViewModule('improvements')) {
        try {
          const impResponse = await fetch(`${backend_url}/api/improvements`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          if (impResponse.ok) {
            const improvements = await impResponse.json();
            const overdueImp = improvements.filter(imp => {
              if (!imp.dateLimite || imp.statut === 'TERMINE' || imp.statut === 'ANNULE') return false;
              const dueDate = new Date(imp.dateLimite);
              return dueDate < today;
            });
            if (overdueImp.length > 0) {
              details.improvements = {
                count: overdueImp.length,
                label: 'Améliorations',
                route: '/improvements',
                category: 'execution'
              };
              executionCount += overdueImp.length;
              total += overdueImp.length;
            }
          }
        } catch (err) {
          console.error('Erreur improvements:', err);
        }
      }
      
      // 3. Demandes d'intervention en retard (JAUNE)
      if (canViewModule('interventionRequests')) {
        try {
          const irResponse = await fetch(`${backend_url}/api/intervention-requests`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          if (irResponse.ok) {
            const interventionRequests = await irResponse.json();
            const overdueIR = interventionRequests.filter(ir => {
              if (!ir.date_limite_desiree || ir.statut === 'TERMINE' || ir.statut === 'ANNULE') return false;
              const dueDate = new Date(ir.date_limite_desiree);
              return dueDate < today;
            });
            if (overdueIR.length > 0) {
              details.interventionRequests = {
                count: overdueIR.length,
                label: "Demandes d'intervention",
                route: '/intervention-requests',
                category: 'requests'
              };
              requestsCount += overdueIR.length;
              total += overdueIR.length;
            }
          }
        } catch (err) {
          console.error('Erreur intervention requests:', err);
        }
      }
      
      // 4. Demandes d'amélioration en retard (JAUNE)
      if (canViewModule('improvementRequests')) {
        try {
          const imprResponse = await fetch(`${backend_url}/api/improvement-requests`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          if (imprResponse.ok) {
            const improvementRequests = await imprResponse.json();
            const overdueIMPR = improvementRequests.filter(impr => {
              if (!impr.date_limite_desiree || impr.statut === 'TERMINE' || impr.statut === 'ANNULE') return false;
              const dueDate = new Date(impr.date_limite_desiree);
              return dueDate < today;
            });
            if (overdueIMPR.length > 0) {
              details.improvementRequests = {
                count: overdueIMPR.length,
                label: "Demandes d'amélioration",
                route: '/improvement-requests',
                category: 'requests'
              };
              requestsCount += overdueIMPR.length;
              total += overdueIMPR.length;
            }
          }
        } catch (err) {
          console.error('Erreur improvement requests:', err);
        }
      }
      
      // 5. Maintenances préventives (BLEU)
      if (canViewModule('preventiveMaintenance')) {
        try {
          const pmResponse = await fetch(`${backend_url}/api/preventive-maintenance`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          if (pmResponse.ok) {
            const pms = await pmResponse.json();
            const overduePM = pms.filter(pm => {
              if (!pm.prochaineMaintenance || pm.statut !== 'ACTIF') return false;
              const nextDate = new Date(pm.prochaineMaintenance);
              return nextDate < today;
            });
            if (overduePM.length > 0) {
              details.preventiveMaintenance = {
                count: overduePM.length,
                label: 'Maintenances préventives',
                route: '/preventive-maintenance',
                category: 'maintenance'
              };
              maintenanceCount += overduePM.length;
              total += overduePM.length;
            }
          }
        } catch (err) {
          console.error('Erreur preventive maintenance:', err);
        }
      }
      
      setOverdueCount(total);
      setOverdueExecutionCount(executionCount);
      setOverdueRequestsCount(requestsCount);
      setOverdueMaintenanceCount(maintenanceCount);
      setOverdueDetails(details);
    } catch (error) {
      console.error('Erreur lors du chargement des échéances:', error);
    }
  };

  const loadSurveillanceBadgeStats = async () => {
    try {
      const token = localStorage.getItem('token');
      const backend_url = getBackendURL();
      
      const response = await fetch(`${backend_url}/api/surveillance/badge-stats`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setSurveillanceBadge(data);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des stats de surveillance:', error);
    }
  };

  const loadInventoryStats = async () => {
    try {
      const token = localStorage.getItem('token');
      const backend_url = getBackendURL();
      
      const response = await fetch(`${backend_url}/api/inventory/stats`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setInventoryStats(data);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des stats inventaire:', error);
    }
  };



  const menuItems = [
    { icon: LayoutDashboard, label: 'Tableau de bord', path: '/dashboard', module: 'dashboard' },
    { icon: MessageSquare, label: 'Demandes d\'inter.', path: '/intervention-requests', module: 'interventionRequests' },
    { icon: ClipboardList, label: 'Ordres de travail', path: '/work-orders', module: 'workOrders' },
    { icon: Lightbulb, label: 'Demandes d\'amél.', path: '/improvement-requests', module: 'improvementRequests' },
    { icon: Sparkles, label: 'Améliorations', path: '/improvements', module: 'improvements' },
    { icon: Calendar, label: 'Maintenance prev.', path: '/preventive-maintenance', module: 'preventiveMaintenance' },
    { icon: Calendar, label: 'Planning M.Prev.', path: '/planning-mprev', module: 'preventiveMaintenance' },
    { icon: Wrench, label: 'Équipements', path: '/assets', module: 'assets' },
    { icon: Package, label: 'Inventaire', path: '/inventory', module: 'inventory' },
    { icon: MapPin, label: 'Zones', path: '/locations', module: 'locations' },
    { icon: Gauge, label: 'Compteurs', path: '/meters', module: 'meters' },
    { icon: Eye, label: 'Plan de Surveillance', path: '/surveillance-plan', module: 'surveillance' },
    { icon: FileText, label: 'Rapport Surveillance', path: '/surveillance-rapport', module: 'surveillance' },
    { icon: AlertTriangle, label: 'Presqu\'accident', path: '/presqu-accident', module: 'presquaccident' },
    { icon: FileText, label: 'Rapport P.accident', path: '/presqu-accident-rapport', module: 'presquaccident' },
    { icon: FolderOpen, label: 'Documentations', path: '/documentations', module: 'documentations' },
    { icon: BarChart3, label: 'Rapports', path: '/reports', module: 'reports' },
    { icon: Users, label: 'Équipes', path: '/people', module: 'people' },
    { icon: Calendar, label: 'Planning', path: '/planning', module: 'planning' },
    { icon: ShoppingCart, label: 'Fournisseurs', path: '/vendors', module: 'vendors' },
    { icon: ShoppingBag, label: 'Historique Achat', path: '/purchase-history', module: 'purchaseHistory' },
    { icon: Database, label: 'Import / Export', path: '/import-export', module: 'importExport' }
  ].filter(item => {
    // Si le menu item a un module défini, vérifier la permission view
    if (item.module) {
      return canView(item.module);
    }
    // Si pas de module (ancien système), afficher par défaut
    return true;
  });

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  const handleFirstLoginSuccess = () => {
    // Mettre à jour le user dans localStorage pour marquer firstLogin comme false
    const userInfo = localStorage.getItem('user');
    if (userInfo) {
      try {
        const parsedUser = JSON.parse(userInfo);
        parsedUser.firstLogin = false;
        localStorage.setItem('user', JSON.stringify(parsedUser));
        setUser(prev => ({ ...prev, firstLogin: false }));
      } catch (error) {
        console.error('Erreur lors de la mise à jour:', error);
      }
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top Navigation */}
      <div className="fixed top-0 left-0 right-0 h-16 bg-white border-b border-gray-200 z-30 flex items-center justify-between px-4">
        <div className="flex items-center gap-4">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            title={sidebarOpen ? "Minimiser le menu" : "Agrandir le menu"}
          >
            {sidebarOpen ? <ChevronLeft size={20} /> : <ChevronRight size={20} />}
          </button>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">G</span>
            </div>
            <span className="font-semibold text-gray-800 text-lg">GMAO Iris</span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* Icône rappel échéances avec 3 badges */}
          <div className="relative">
            <button 
              onClick={() => setOverdueMenuOpen(!overdueMenuOpen)}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors relative"
              title="Échéances dépassées"
            >
              <img src="/rappel-calendrier.jpg" alt="Rappel" className="w-6 h-6 object-contain" />
              
              {/* Badge ORANGE - Coin supérieur droit - Work Orders + Improvements */}
              {overdueExecutionCount > 0 && (
                <span className="absolute -top-1 -right-1 w-5 h-5 bg-orange-500 rounded-full flex items-center justify-center text-white text-xs font-bold shadow-md">
                  {overdueExecutionCount > 9 ? '9+' : overdueExecutionCount}
                </span>
              )}
              
              {/* Badge JAUNE - Coin supérieur gauche - Demandes d'inter. + Demandes d'amél. */}
              {overdueRequestsCount > 0 && (
                <span className="absolute -top-1 -left-1 w-5 h-5 bg-yellow-500 rounded-full flex items-center justify-center text-white text-xs font-bold shadow-md">
                  {overdueRequestsCount > 9 ? '9+' : overdueRequestsCount}
                </span>
              )}
              
              {/* Badge BLEU - Coin inférieur gauche - Maintenances préventives */}
              {overdueMaintenanceCount > 0 && (
                <span className="absolute -bottom-1 -left-1 w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center text-white text-xs font-bold shadow-md">
                  {overdueMaintenanceCount > 9 ? '9+' : overdueMaintenanceCount}
                </span>
              )}
            </button>

            {/* Menu déroulant des échéances */}
            {overdueMenuOpen && overdueCount > 0 && (
              <div className="absolute right-0 mt-2 w-72 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
                <div className="p-3 border-b border-gray-200">
                  <h3 className="font-semibold text-gray-800">Échéances dépassées</h3>
                  <p className="text-xs text-gray-500 mt-1">{overdueCount} élément{overdueCount > 1 ? 's' : ''} en retard</p>
                </div>
                <div className="py-2 max-h-80 overflow-y-auto">
                  {Object.entries(overdueDetails).map(([key, detail]) => {
                    // Couleur selon la catégorie
                    const categoryColors = {
                      execution: { dot: 'bg-orange-500', text: 'text-orange-500', hover: 'group-hover:text-orange-600' },
                      requests: { dot: 'bg-yellow-500', text: 'text-yellow-600', hover: 'group-hover:text-yellow-700' },
                      maintenance: { dot: 'bg-blue-500', text: 'text-blue-500', hover: 'group-hover:text-blue-600' }
                    };
                    const colors = categoryColors[detail.category] || categoryColors.execution;
                    
                    return (
                      <button
                        key={key}
                        onClick={() => {
                          navigate(detail.route);
                          setOverdueMenuOpen(false);
                        }}
                        className="w-full px-4 py-3 hover:bg-gray-50 transition-colors flex items-center justify-between group"
                      >
                        <div className="flex items-center gap-3">
                          <div className={`w-2 h-2 ${colors.dot} rounded-full`}></div>
                          <span className={`text-sm text-gray-700 ${colors.hover} font-medium`}>
                            {detail.label}
                          </span>
                        </div>
                        <span className={`text-sm font-semibold ${colors.text}`}>
                          {detail.count}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
            
            {/* Message si aucune échéance */}
            {overdueMenuOpen && overdueCount === 0 && (
              <div className="absolute right-0 mt-2 w-72 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
                <div className="p-4 text-center">
                  <p className="text-sm text-gray-500">Aucune échéance dépassée</p>
                </div>
              </div>
            )}
          </div>
          
          {/* Badge de mise à jour (Admin uniquement) */}
          {isAdmin() && <UpdateNotificationBadge />}
          
          {/* Badge Plan de Surveillance */}
          <button 
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors relative group"
            onClick={() => navigate('/surveillance-plan', { state: { showOverdueOnly: true } })}
            title="Plan de Surveillance - Voir les contrôles en retard"
          >
            <Eye size={20} className="text-gray-600" />
            {surveillanceBadge.echeances_proches > 0 && (
              <span className="absolute -top-1 -right-1 w-5 h-5 bg-orange-500 rounded-full flex items-center justify-center text-white text-xs font-bold">
                {surveillanceBadge.echeances_proches > 9 ? '9+' : surveillanceBadge.echeances_proches}
              </span>
            )}
            {/* Tooltip avec détails */}
            <div className="absolute hidden group-hover:block right-0 mt-2 w-64 bg-white rounded-lg shadow-lg border border-gray-200 z-50 p-3">
              <div className="text-sm font-semibold text-gray-800 mb-2">Plan de Surveillance</div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Échéances proches:</span>
                  <span className="font-bold text-orange-600">{surveillanceBadge.echeances_proches}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Taux de réalisation:</span>
                  <span className={`font-bold ${surveillanceBadge.pourcentage_realisation >= 75 ? 'text-green-600' : surveillanceBadge.pourcentage_realisation >= 50 ? 'text-orange-600' : 'text-red-600'}`}>
                    {surveillanceBadge.pourcentage_realisation}%
                  </span>
                </div>
              </div>
              <div className="mt-3 pt-3 border-t border-gray-200 text-xs text-gray-500">
                💡 Cliquez pour voir uniquement les contrôles en retard
              </div>
            </div>
          </button>
          
          {/* Cloche notifications */}
          <button 
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors relative"
            onClick={() => navigate('/work-orders')}
          >
            <Bell size={20} className="text-gray-600" />
            {workOrdersCount > 0 && (
              <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 rounded-full flex items-center justify-center text-white text-xs font-bold">
                {workOrdersCount > 9 ? '9+' : workOrdersCount}
              </span>
            )}
          </button>
          <button 
            onClick={() => navigate('/settings')}
            className="flex items-center gap-3 hover:bg-gray-100 rounded-lg px-3 py-2 transition-colors cursor-pointer"
          >
            <div className="text-right">
              <div className="text-sm font-medium text-gray-800">{user.nom}</div>
              <div className="text-xs text-gray-500">{user.role}</div>
            </div>
            <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center">
              <span className="text-white font-medium text-sm">
                {user.nom.split(' ').map(n => n[0]).join('')}
              </span>
            </div>
          </button>
        </div>
      </div>

      {/* Sidebar */}
      <div
        className={`fixed top-16 left-0 bottom-0 bg-gray-900 text-white transition-all duration-300 z-20 ${
          sidebarOpen ? 'w-64' : 'w-20'
        }`}
      >
        <div className="p-4 space-y-2 h-full overflow-y-auto">
          {menuItems
            .filter(item => !item.adminOnly || user.role === 'ADMIN')
            .map((item, index) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <button
                  key={index}
                  onClick={() => navigate(item.path)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                    isActive
                      ? 'bg-blue-600 text-white'
                      : 'hover:bg-gray-800 text-gray-300'
                  } ${!sidebarOpen ? 'justify-center px-2' : ''}`}
                  title={!sidebarOpen ? item.label : ''}
                >
                  <Icon size={20} className="flex-shrink-0" />
                  {sidebarOpen && <span className="text-sm font-medium">{item.label}</span>}
                </button>
              );
            })}
          
          <div className="pt-4 mt-4 border-t border-gray-700">
            <button
              onClick={() => navigate('/settings')}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-gray-800 text-gray-300 transition-all ${!sidebarOpen ? 'justify-center px-2' : ''}`}
              title={!sidebarOpen ? 'Paramètres' : ''}
            >
              <Settings size={20} className="flex-shrink-0" />
              {sidebarOpen && <span className="text-sm font-medium">Paramètres</span>}
            </button>
            {user.role === 'ADMIN' && (
              <>
                <button
                  onClick={() => navigate('/special-settings')}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-gray-800 text-gray-300 transition-all ${!sidebarOpen ? 'justify-center px-2' : ''}`}
                  title={!sidebarOpen ? 'Paramètres Spéciaux' : ''}
                >
                  <Shield size={20} className="flex-shrink-0" />
                  {sidebarOpen && <span className="text-sm font-medium">Paramètres Spéciaux</span>}
                </button>
                <button
                  onClick={() => navigate('/updates')}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-gray-800 text-gray-300 transition-all ${!sidebarOpen ? 'justify-center px-2' : ''}`}
                  title={!sidebarOpen ? 'Mise à jour' : ''}
                >
                  <RefreshCw size={20} className="flex-shrink-0" />
                  {sidebarOpen && <span className="text-sm font-medium">Mise à jour</span>}
                </button>
                <button
                  onClick={() => navigate('/journal')}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-gray-800 text-gray-300 transition-all ${!sidebarOpen ? 'justify-center px-2' : ''}`}
                  title={!sidebarOpen ? 'Journal' : ''}
                >
                  <FileText size={20} className="flex-shrink-0" />
                  {sidebarOpen && <span className="text-sm font-medium">Journal</span>}
                </button>
                <button
                  onClick={() => navigate('/ssh')}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-gray-800 text-gray-300 transition-all ${!sidebarOpen ? 'justify-center px-2' : ''}`}
                  title={!sidebarOpen ? 'SSH' : ''}
                >
                  <Terminal size={20} className="flex-shrink-0" />
                  {sidebarOpen && <span className="text-sm font-medium">SSH</span>}
                </button>
              </>
            )}
            <button
              onClick={handleLogout}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-red-600 text-gray-300 transition-all ${!sidebarOpen ? 'justify-center px-2' : ''}`}
              title={!sidebarOpen ? 'Déconnexion' : ''}
            >
              <LogOut size={20} className="flex-shrink-0" />
              {sidebarOpen && <span className="text-sm font-medium">Déconnexion</span>}
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div
        className={`transition-all duration-300 ${
          sidebarOpen ? 'ml-64' : 'ml-20'
        }`}
      >
        <div className="p-6 pt-20">
          <Outlet />
        </div>
      </div>
      
      {/* Popups */}
      <FirstLoginPasswordDialog 
        open={firstLoginDialogOpen}
        onOpenChange={setFirstLoginDialogOpen}
        userId={user.id}
        onSuccess={() => {
          // Mettre à jour l'état local du user
          setUser(prev => ({ ...prev, firstLogin: false }));
          setFirstLoginDialogOpen(false);
        }}
      />
      
      {/* Popup de mise à jour récente (tous les utilisateurs) */}
      <RecentUpdatePopup />
      
      {/* Validation du token au démarrage */}
      <TokenValidator />
      
      {/* Gestion de l'inactivité */}
      <InactivityHandler />
    </div>
  );
};

export default MainLayout;