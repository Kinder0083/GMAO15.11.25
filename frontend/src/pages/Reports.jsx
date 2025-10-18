import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { BarChart3, TrendingUp, Download, Calendar } from 'lucide-react';
import { reportsAPI, equipmentsAPI } from '../services/api';

const Reports = () => {
  const [selectedPeriod, setSelectedPeriod] = useState('MOIS');
  const [loading, setLoading] = useState(true);
  const [analytics, setAnalytics] = useState(null);
  const [equipments, setEquipments] = useState([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [analyticsRes, equipRes] = await Promise.all([
        reportsAPI.getAnalytics(),
        equipmentsAPI.getAll()
      ]);
      setAnalytics(analyticsRes.data);
      setEquipments(equipRes.data);
    } catch (error) {
      console.error('Erreur de chargement:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !analytics) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-gray-500">Chargement...</p>
      </div>
    );
  }

  const periods = [
    { value: 'SEMAINE', label: 'Cette semaine' },
    { value: 'MOIS', label: 'Ce mois' },
    { value: 'TRIMESTRE', label: 'Ce trimestre' },
    { value: 'ANNEE', label: 'Cette année' }
  ];

  const coutsMaintenance = Object.entries(analytics.coutsMaintenance);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Rapports & Analytiques</h1>
          <p className="text-gray-600 mt-1">Analysez vos performances de maintenance</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" className="border-blue-600 text-blue-600 hover:bg-blue-50">
            <Calendar size={20} className="mr-2" />
            Période personnalisée
          </Button>
          <Button className="bg-blue-600 hover:bg-blue-700 text-white">
            <Download size={20} className="mr-2" />
            Exporter PDF
          </Button>
        </div>
      </div>

      {/* Period Filter */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-2 flex-wrap">
            {periods.map(period => (
              <Button
                key={period.value}
                variant={selectedPeriod === period.value ? 'default' : 'outline'}
                onClick={() => setSelectedPeriod(period.value)}
                size="sm"
                className={selectedPeriod === period.value ? 'bg-blue-600 hover:bg-blue-700' : ''}
              >
                {period.label}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="hover:shadow-lg transition-shadow">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Taux de réalisation</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{analytics.tauxRealisation}%</p>
                <p className="text-xs text-green-600 mt-1 font-medium">+8% vs mois précédent</p>
              </div>
              <div className="bg-green-100 p-3 rounded-xl">
                <TrendingUp size={24} className="text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-shadow">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Temps de réponse moyen</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{analytics.tempsReponse.moyen}h</p>
                <p className="text-xs text-green-600 mt-1 font-medium">-15% vs mois précédent</p>
              </div>
              <div className="bg-blue-100 p-3 rounded-xl">
                <BarChart3 size={24} className="text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-shadow">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Maintenances préventives</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{analytics.nombreMaintenancesPrev}</p>
                <p className="text-xs text-gray-500 mt-1">Ce mois</p>
              </div>
              <div className="bg-purple-100 p-3 rounded-xl">
                <Calendar size={24} className="text-purple-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-shadow">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Maintenances correctives</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{analytics.nombreMaintenancesCorrectives}</p>
                <p className="text-xs text-gray-500 mt-1">Ce mois</p>
              </div>
              <div className="bg-orange-100 p-3 rounded-xl">
                <BarChart3 size={24} className="text-orange-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Cost Trends */}
        <Card>
          <CardHeader>
            <CardTitle>Tendance des coûts de maintenance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {coutsMaintenance.map(([mois, cout], index) => {
                const maxCout = Math.max(...coutsMaintenance.map(c => c[1]));
                const percentage = (cout / maxCout) * 100;
                return (
                  <div key={mois}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="font-medium text-gray-700 capitalize">{mois}</span>
                      <span className="text-gray-900 font-bold">{cout.toLocaleString('fr-FR')} €</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div
                        className="bg-gradient-to-r from-blue-500 to-blue-600 h-3 rounded-full transition-all"
                        style={{ width: `${percentage}%` }}
                      ></div>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Work Order Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Répartition des ordres de travail</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <div>
                <h4 className="text-sm font-semibold text-gray-700 mb-3">Par statut</h4>
                <div className="space-y-3">
                  {Object.entries(analytics.workOrdersParStatut).map(([statut, count]) => {
                    const total = Object.values(analytics.workOrdersParStatut).reduce((a, b) => a + b, 0);
                    const percentage = total > 0 ? ((count / total) * 100).toFixed(0) : 0;
                    const labels = {
                      'OUVERT': { label: 'Ouvert', color: 'bg-gray-500' },
                      'EN_COURS': { label: 'En cours', color: 'bg-blue-500' },
                      'EN_ATTENTE': { label: 'En attente', color: 'bg-yellow-500' },
                      'TERMINE': { label: 'Terminé', color: 'bg-green-500' }
                    };
                    return (
                      <div key={statut} className="flex items-center justify-between">
                        <div className="flex items-center gap-2 flex-1">
                          <div className={`w-3 h-3 rounded-full ${labels[statut].color}`}></div>
                          <span className="text-sm text-gray-700">{labels[statut].label}</span>
                        </div>
                        <div className="flex items-center gap-4">
                          <div className="w-32 bg-gray-200 rounded-full h-2">
                            <div
                              className={`${labels[statut].color} h-2 rounded-full`}
                              style={{ width: `${percentage}%` }}
                            ></div>
                          </div>
                          <span className="text-sm font-medium text-gray-900 w-12 text-right">
                            {count} ({percentage}%)
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="pt-4 border-t">
                <h4 className="text-sm font-semibold text-gray-700 mb-3">Par priorité</h4>
                <div className="space-y-3">
                  {Object.entries(analytics.workOrdersParPriorite).filter(([_, count]) => count > 0).map(([priorite, count]) => {
                    const labels = {
                      'HAUTE': { label: 'Haute', color: 'bg-red-500' },
                      'MOYENNE': { label: 'Moyenne', color: 'bg-orange-500' },
                      'BASSE': { label: 'Basse', color: 'bg-yellow-500' },
                      'AUCUNE': { label: 'Normale', color: 'bg-gray-500' }
                    };
                    return (
                      <div key={priorite} className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div className={`w-3 h-3 rounded-full ${labels[priorite].color}`}></div>
                          <span className="text-sm text-gray-700">{labels[priorite].label}</span>
                        </div>
                        <span className="text-sm font-medium text-gray-900">{count}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Equipment Performance */}
      <Card>
        <CardHeader>
          <CardTitle>Performance des équipements</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Équipement</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Catégorie</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Statut</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Dernière maintenance</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Coût d'achat</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Disponibilité</th>
                </tr>
              </thead>
              <tbody>
                {mockEquipments.map((equipment) => {
                  const availability = equipment.statut === 'OPERATIONNEL' ? 95 : equipment.statut === 'EN_MAINTENANCE' ? 70 : 0;
                  return (
                    <tr key={equipment.id} className="border-b hover:bg-gray-50 transition-colors">
                      <td className="py-3 px-4 text-sm text-gray-900 font-medium">{equipment.nom}</td>
                      <td className="py-3 px-4 text-sm text-gray-700">{equipment.categorie}</td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          equipment.statut === 'OPERATIONNEL' ? 'bg-green-100 text-green-700' :
                          equipment.statut === 'EN_MAINTENANCE' ? 'bg-orange-100 text-orange-700' :
                          'bg-red-100 text-red-700'
                        }`}>
                          {equipment.statut === 'OPERATIONNEL' ? 'Opérationnel' :
                           equipment.statut === 'EN_MAINTENANCE' ? 'En maintenance' : 'Hors service'}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-700">{equipment.derniereMaintenance}</td>
                      <td className="py-3 px-4 text-sm text-gray-700">{equipment.coutAchat.toLocaleString('fr-FR')} €</td>
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          <div className="flex-1 bg-gray-200 rounded-full h-2 max-w-[100px]">
                            <div
                              className={`h-2 rounded-full ${
                                availability >= 90 ? 'bg-green-500' :
                                availability >= 70 ? 'bg-orange-500' : 'bg-red-500'
                              }`}
                              style={{ width: `${availability}%` }}
                            ></div>
                          </div>
                          <span className="text-sm font-medium text-gray-900">{availability}%</span>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Reports;