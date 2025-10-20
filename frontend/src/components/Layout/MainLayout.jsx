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
  RefreshCw
} from 'lucide-react';
import FirstLoginPasswordDialog from '../Common/FirstLoginPasswordDialog';

const MainLayout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [firstLoginDialogOpen, setFirstLoginDialogOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const [user, setUser] = useState({ nom: 'Utilisateur', role: 'VIEWER', firstLogin: false, id: '' });
  const [workOrdersCount, setWorkOrdersCount] = useState(0);

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
        // Compter les ordres de travail assignés à l'utilisateur
        const assignedOrders = data.filter(order => 
          order.assignedTo === userId && 
          order.status !== 'TERMINE'
        );
        setWorkOrdersCount(assignedOrders.length);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des ordres de travail:', error);
    }
  };

  const menuItems = [
    { icon: LayoutDashboard, label: 'Tableau de bord', path: '/dashboard' },
    { icon: ClipboardList, label: 'Ordres de travail', path: '/work-orders' },
    { icon: Calendar, label: 'Maintenance prev.', path: '/preventive-maintenance' },
    { icon: Wrench, label: 'Équipements', path: '/assets' },
    { icon: Package, label: 'Inventaire', path: '/inventory' },
    { icon: MapPin, label: 'Zones', path: '/locations' },
    { icon: BarChart3, label: 'Rapports', path: '/reports' },
    { icon: Users, label: 'Équipes', path: '/people' },
    { icon: Calendar, label: 'Planning', path: '/planning' },
    { icon: ShoppingCart, label: 'Fournisseurs', path: '/vendors' },
    { icon: ShoppingBag, label: 'Historique Achat', path: '/purchase-history' },
    { icon: Database, label: 'Import / Export', path: '/import-export', adminOnly: true }
  ];

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
              <button
                onClick={() => navigate('/updates')}
                className="w-full flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-gray-800 text-gray-300 transition-all"
              >
                <RefreshCw size={20} />
                <span className="text-sm font-medium">Mise à jour</span>
              </button>
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