import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { workOrdersAPI, equipmentsAPI, reportsAPI } from '../services/api';
import {
  ClipboardList,
  Wrench,
  TrendingUp,
  Clock,
  AlertCircle,
  CheckCircle2,
  Activity
} from 'lucide-react';
import { useAutoRefresh } from '../hooks/useAutoRefresh';
import { usePermissions } from '../hooks/usePermissions';

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [initialLoad, setInitialLoad] = useState(true);
  const [workOrders, setWorkOrders] = useState([]);
  const [equipments, setEquipments] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const { canView } = usePermissions();

  const loadData = async () => {
    try {
      // Ne montrer le loading que lors du premier chargement
      if (initialLoad) {
        setLoading(true);
      }
      
      // Charger uniquement les données auxquelles l'utilisateur a accès
      const promises = [];
      
      // Work Orders - si permission view
      if (canView('workOrders')) {
        promises.push(
          workOrdersAPI.getAll()
            .then(res => ({ type: 'workOrders', data: res.data }))
            .catch(err => {
              console.error('Erreur work orders:', err);
              return { type: 'workOrders', data: [] };
            })
        );
      }
      
      // Equipments - si permission view
      if (canView('assets')) {
        promises.push(
          equipmentsAPI.getAll()
            .then(res => ({ type: 'equipments', data: res.data }))
            .catch(err => {
              console.error('Erreur equipments:', err);
              return { type: 'equipments', data: [] };
            })
        );
      }
      
      // Analytics/Reports - si permission view
      if (canView('reports')) {
        promises.push(
          reportsAPI.getAnalytics()
            .then(res => ({ type: 'analytics', data: res.data }))
            .catch(err => {
              console.error('Erreur analytics:', err);
              return { type: 'analytics', data: null };
            })
        );
      }
      
      // Si aucune permission, afficher un dashboard vide
      if (promises.length === 0) {
        setWorkOrders([]);
        setEquipments([]);
        setAnalytics(null);
        setLoading(false);
        setInitialLoad(false);
        return;
      }
      
      const results = await Promise.all(promises);
      
      // Mettre à jour les données selon les résultats
      results.forEach(result => {
        if (result.type === 'workOrders') {
          if (initialLoad || JSON.stringify(result.data) !== JSON.stringify(workOrders)) {
            setWorkOrders(result.data);
          }
        } else if (result.type === 'equipments') {
          if (initialLoad || JSON.stringify(result.data) !== JSON.stringify(equipments)) {
            setEquipments(result.data);
          }
        } else if (result.type === 'analytics') {
          if (initialLoad || JSON.stringify(result.data) !== JSON.stringify(analytics)) {
            setAnalytics(result.data);
          }
        }
      });
      
    } catch (error) {
      console.error('Erreur générale de chargement:', error);
      // En cas d'erreur, initialiser avec des données vides
      setWorkOrders([]);
      setEquipments([]);
      setAnalytics(null);
    } finally {
      if (initialLoad) {
        setLoading(false);
        setInitialLoad(false);
      }
    }
  };

  // Rafraîchissement automatique toutes les 5 secondes (invisible)
  useAutoRefresh(loadData, []);

  // Calculer les stats dynamiquement
  const stats = React.useMemo(() => {
    const baseStats = [];
    
    // Toujours afficher les stats basées sur les données disponibles
    if (workOrders) {
      baseStats.push({
        title: 'Ordres de travail actifs',
        value: workOrders.filter(wo => wo.statut !== 'TERMINE').length,
        icon: ClipboardList,
        color: 'bg-blue-500',
        change: '+12%'
      });
    }
    
    if (equipments) {
      baseStats.push({
        title: 'Équipements en maintenance',
        value: equipments.filter(e => e.statut === 'EN_MAINTENANCE').length,
        icon: Wrench,
        color: 'bg-orange-500',
        change: '+5%'
      });
    }
    
    // Ajouter les stats analytics seulement si disponibles
    if (analytics) {
      baseStats.push(
        {
          title: 'Taux de réalisation',
          value: `${analytics.tauxRealisation}%`,
          icon: TrendingUp,
          color: 'bg-green-500',
          change: '+8%'
        },
        {
          title: 'Temps de réponse moyen',
          value: `${analytics.tempsReponse.moyen}h`,
          icon: Clock,
          color: 'bg-purple-500',
          change: '-15%'
        }
      );
    }
    
    return baseStats;
  }, [analytics, workOrders, equipments]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-gray-500">Chargement...</p>
      </div>
    );
  }

  const recentWorkOrders = workOrders.slice(0, 5);

  const getStatusBadge = (statut) => {
    const badges = {
      'OUVERT': { bg: 'bg-gray-100', text: 'text-gray-700', label: 'Ouvert' },
      'EN_COURS': { bg: 'bg-blue-100', text: 'text-blue-700', label: 'En cours' },
      'EN_ATTENTE': { bg: 'bg-yellow-100', text: 'text-yellow-700', label: 'En attente' },
      'TERMINE': { bg: 'bg-green-100', text: 'text-green-700', label: 'Terminé' }
    };
    const badge = badges[statut] || badges['OUVERT'];
    return (
      <span className={`px-3 py-1 rounded-full text-xs font-medium ${badge.bg} ${badge.text}`}>
        {badge.label}
      </span>
    );
  };

  const getPriorityBadge = (priorite) => {
    const badges = {
      'HAUTE': { bg: 'bg-red-100', text: 'text-red-700', label: 'Haute' },
      'MOYENNE': { bg: 'bg-orange-100', text: 'text-orange-700', label: 'Moyenne' },
      'BASSE': { bg: 'bg-yellow-100', text: 'text-yellow-700', label: 'Basse' },
      'AUCUNE': { bg: 'bg-gray-100', text: 'text-gray-600', label: 'Normale' }
    };
    const badge = badges[priorite] || badges['AUCUNE'];
    return (
      <span className={`px-2 py-1 rounded text-xs font-medium ${badge.bg} ${badge.text}`}>
        {badge.label}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Tableau de bord</h1>
        <p className="text-gray-600 mt-1">Vue d'ensemble de votre système de maintenance</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <Card key={index} className="hover:shadow-lg transition-shadow">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">{stat.title}</p>
                    <p className="text-3xl font-bold text-gray-900 mt-2">{stat.value}</p>
                    <p className="text-xs text-green-600 mt-2 font-medium">{stat.change} ce mois</p>
                  </div>
                  <div className={`${stat.color} p-3 rounded-xl`}>
                    <Icon size={24} className="text-white" />
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Work Orders by Status */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="text-blue-600" size={20} />
              Ordres de travail par statut
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(analytics.workOrdersParStatut).map(([statut, count]) => {
                const total = Object.values(analytics.workOrdersParStatut).reduce((a, b) => a + b, 0);
                const percentage = total > 0 ? ((count / total) * 100).toFixed(0) : 0;
                const labels = {
                  'OUVERT': 'Ouvert',
                  'EN_COURS': 'En cours',
                  'EN_ATTENTE': 'En attente',
                  'TERMINE': 'Terminé'
                };
                const colors = {
                  'OUVERT': 'bg-gray-500',
                  'EN_COURS': 'bg-blue-500',
                  'EN_ATTENTE': 'bg-yellow-500',
                  'TERMINE': 'bg-green-500'
                };
                return (
                  <div key={statut}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="font-medium text-gray-700">{labels[statut]}</span>
                      <span className="text-gray-600">{count} ({percentage}%)</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2.5">
                      <div
                        className={`${colors[statut]} h-2.5 rounded-full transition-all`}
                        style={{ width: `${percentage}%` }}
                      ></div>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Equipment Status */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Wrench className="text-orange-600" size={20} />
              État des équipements
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                    <CheckCircle2 className="text-green-600" size={24} />
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Opérationnel</p>
                    <p className="text-2xl font-bold text-gray-900">{analytics.equipementsParStatut.OPERATIONNEL || 0}</p>
                  </div>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
                    <Clock className="text-orange-600" size={24} />
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">En maintenance</p>
                    <p className="text-2xl font-bold text-gray-900">{analytics.equipementsParStatut.EN_MAINTENANCE || 0}</p>
                  </div>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
                    <AlertCircle className="text-red-600" size={24} />
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Hors service</p>
                    <p className="text-2xl font-bold text-gray-900">{analytics.equipementsParStatut.HORS_SERVICE || 0}</p>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Work Orders */}
      <Card>
        <CardHeader>
          <CardTitle>Ordres de travail récents</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">ID</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Titre</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Statut</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Priorité</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Assigné à</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Emplacement</th>
                </tr>
              </thead>
              <tbody>
                {recentWorkOrders.map((wo) => (
                  <tr key={wo.id} className="border-b hover:bg-gray-50 transition-colors">
                    <td className="py-3 px-4 text-sm text-gray-900 font-medium">#{wo.numero}</td>
                    <td className="py-3 px-4 text-sm text-gray-900">{wo.titre}</td>
                    <td className="py-3 px-4">{getStatusBadge(wo.statut)}</td>
                    <td className="py-3 px-4">{getPriorityBadge(wo.priorite)}</td>
                    <td className="py-3 px-4 text-sm text-gray-700">
                      {wo.assigneA ? `${wo.assigneA.prenom} ${wo.assigneA.nom}` : '-'}
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-700">
                      {wo.emplacement ? wo.emplacement.nom : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Dashboard;