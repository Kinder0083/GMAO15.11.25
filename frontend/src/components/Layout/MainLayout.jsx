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
  LogOut,
  Bell,
  Database,
  RefreshCw,
  FileText,
  Gauge,
  MessageSquare,
  Lightbulb,
  Sparkles
} from 'lucide-react';
import FirstLoginPasswordDialog from '../Common/FirstLoginPasswordDialog';
import { usePermissions } from '../../hooks/usePermissions';

const MainLayout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [firstLoginDialogOpen, setFirstLoginDialogOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const [user, setUser] = useState({ nom: 'Utilisateur', role: 'VIEWER', firstLogin: false, id: '' });
  const [workOrdersCount, setWorkOrdersCount] = useState(0);
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
        
        // Rafraîchir les notifications toutes les 60 secondes
        const intervalId = setInterval(() => {
          loadWorkOrdersCount(parsedUser.id);
        }, 60000); // 60 secondes
        
        // Écouter les événements de création/modification d'ordres de travail
        const handleWorkOrderChange = () => {
          loadWorkOrdersCount(parsedUser.id);
        };
        
        window.addEventListener('workOrderCreated', handleWorkOrderChange);
        window.addEventListener('workOrderUpdated', handleWorkOrderChange);
        
        // Nettoyer les listeners et l'intervalle au démontage
        return () => {
          clearInterval(intervalId);
          window.removeEventListener('workOrderCreated', handleWorkOrderChange);
          window.removeEventListener('workOrderUpdated', handleWorkOrderChange);
        };
      } catch (error) {
        console.error('Erreur lors du parsing des infos utilisateur:', error);
      }
    }
  }, []);

  const loadWorkOrdersCount = async (userId) => {
    try {
      const token = localStorage.getItem('token');
      const backend_url = process.env.REACT_APP_BACKEND_URL;
      
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

  const menuItems = [
    { icon: LayoutDashboard, label: 'Tableau de bord', path: '/dashboard', module: 'dashboard' },
    { icon: MessageSquare, label: 'Demandes d\'inter.', path: '/intervention-requests', module: 'interventionRequests' },
    { icon: ClipboardList, label: 'Ordres de travail', path: '/work-orders', module: 'workOrders' },
    { icon: Lightbulb, label: 'Demandes d\'amél.', path: '/improvement-requests', module: 'improvementRequests' },
    { icon: Sparkles, label: 'Améliorations', path: '/improvements', module: 'improvements' },
    { icon: Calendar, label: 'Maintenance prev.', path: '/preventive-maintenance', module: 'preventiveMaintenance' },
    { icon: Wrench, label: 'Équipements', path: '/assets', module: 'assets' },
    { icon: Package, label: 'Inventaire', path: '/inventory', module: 'inventory' },
    { icon: MapPin, label: 'Zones', path: '/locations', module: 'locations' },
    { icon: Gauge, label: 'Compteurs', path: '/meters', module: 'meters' },
    { icon: BarChart3, label: 'Rapports', path: '/reports', module: 'reports' },
    { icon: Users, label: 'Équipes', path: '/people', module: 'people' },
    { icon: Calendar, label: 'Planning', path: '/planning', module: 'planning' },
    { icon: ShoppingCart, label: 'Fournisseurs', path: '/vendors', module: 'vendors' },
    { icon: ShoppingBag, label: 'Historique Achat', path: '/purchase-history', module: 'purchaseHistory' },
    { icon: Database, label: 'Import / Export', path: '/import-export', module: 'importExport' },
    { icon: FileText, label: 'Journal', path: '/journal', module: 'journal' }
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
      {/* First Login Password Dialog */}
      <FirstLoginPasswordDialog 
        open={firstLoginDialogOpen}
        onOpenChange={setFirstLoginDialogOpen}
        onSuccess={handleFirstLoginSuccess}
      />
      {/* Top Navigation */}
      <div className="fixed top-0 left-0 right-0 h-16 bg-white border-b border-gray-200 z-30 flex items-center justify-between px-4">
        <div className="flex items-center gap-4">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">G</span>
            </div>
            <span className="font-semibold text-gray-800 text-lg">GMAO Iris</span>
          </div>
        </div>

        <div className="flex items-center gap-4">
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
          sidebarOpen ? 'w-64' : 'w-0'
        } overflow-hidden`}
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
                  }`}
                >
                  <Icon size={20} />
                  <span className="text-sm font-medium">{item.label}</span>
                </button>
              );
            })}
          
          <div className="pt-4 mt-4 border-t border-gray-700">
            <button
              onClick={() => navigate('/settings')}
              className="w-full flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-gray-800 text-gray-300 transition-all"
            >
              <Settings size={20} />
              <span className="text-sm font-medium">Paramètres</span>
            </button>
            {user.role === 'ADMIN' && (
              <>
                <button
                  onClick={() => navigate('/updates')}
                  className="w-full flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-gray-800 text-gray-300 transition-all"
                >
                  <RefreshCw size={20} />
                  <span className="text-sm font-medium">Mise à jour</span>
                </button>
                <button
                  onClick={() => navigate('/journal')}
                  className="w-full flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-gray-800 text-gray-300 transition-all"
                >
                  <FileText size={20} />
                  <span className="text-sm font-medium">Journal</span>
                </button>
              </>
            )}
            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-red-600 text-gray-300 transition-all"
            >
              <LogOut size={20} />
              <span className="text-sm font-medium">Déconnexion</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div
        className={`pt-16 transition-all duration-300 ${
          sidebarOpen ? 'ml-64' : 'ml-0'
        }`}
      >
        <div className="p-6">
          <Outlet />
        </div>
      </div>
    </div>
  );
};

export default MainLayout;