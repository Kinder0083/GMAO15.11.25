import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Plus, Search, ShoppingCart, TrendingUp, Calendar, Pencil, Trash2, Download, Upload, ChevronDown, ChevronRight } from 'lucide-react';
import { purchaseHistoryAPI } from '../services/api';
import { useToast } from '../hooks/use-toast';
import PurchaseFormDialog from '../components/PurchaseHistory/PurchaseFormDialog';

const PurchaseHistory = () => {
  const { toast } = useToast();
  const [purchases, setPurchases] = useState([]);
  const [groupedPurchases, setGroupedPurchases] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [formDialogOpen, setFormDialogOpen] = useState(false);
  const [selectedPurchase, setSelectedPurchase] = useState(null);
  const [filterMonth, setFilterMonth] = useState('');
  const [filterSupplier, setFilterSupplier] = useState('');
  const [expandedOrders, setExpandedOrders] = useState(new Set());
  const [currentUser, setCurrentUser] = useState(null);

  useEffect(() => {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    setCurrentUser(user);
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [groupedRes, statsRes] = await Promise.all([
        purchaseHistoryAPI.getGrouped(),
        purchaseHistoryAPI.getStats()
      ]);
      setGroupedPurchases(groupedRes.data);
      setStats(statsRes.data);
    } catch (error) {
      toast({
        title: 'Erreur',
        description: 'Impossible de charger les données',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAll = async () => {
    if (window.confirm('⚠️ ATTENTION ! Êtes-vous sûr de vouloir supprimer TOUT l\'historique d\'achat ? Cette action est irréversible !')) {
      try {
        const result = await purchaseHistoryAPI.deleteAll();
        toast({
          title: 'Succès',
          description: `${result.data.deleted_count} achats supprimés`
        });
        loadData();
      } catch (error) {
        toast({
          title: 'Erreur',
          description: 'Impossible de supprimer l\'historique',
          variant: 'destructive'
        });
      }
    }
  };

  const toggleExpand = (numeroCommande) => {
    const newExpanded = new Set(expandedOrders);
    if (newExpanded.has(numeroCommande)) {
      newExpanded.delete(numeroCommande);
    } else {
      newExpanded.add(numeroCommande);
    }
    setExpandedOrders(newExpanded);
  };

  const handleDelete = async (id) => {
    if (window.confirm('Êtes-vous sûr de vouloir supprimer cet achat ?')) {
      try {
        await purchaseHistoryAPI.delete(id);
        toast({
          title: 'Succès',
          description: 'Achat supprimé'
        });
        loadData();
      } catch (error) {
        toast({
          title: 'Erreur',
          description: 'Impossible de supprimer l\'achat',
          variant: 'destructive'
        });
      }
    }
  };

  const handleDownloadTemplate = async () => {
    try {
      const response = await purchaseHistoryAPI.downloadTemplate('csv');
      
      const blob = new Blob([response.data], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = 'template_historique_achat.csv';
      document.body.appendChild(a);
      a.click();
      
      // Cleanup
      setTimeout(() => {
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }, 100);
      
      toast({
        title: 'Succès',
        description: 'Template téléchargé avec succès'
      });
    } catch (error) {
      console.error('Erreur téléchargement template:', error);
      toast({
        title: 'Erreur',
        description: error.response?.data?.detail || 'Impossible de télécharger le template',
        variant: 'destructive'
      });
    }
  };

  const canEdit = () => {
    return currentUser?.role === 'ADMIN' || currentUser?.role === 'TECHNICIEN';
  };

  const canDelete = () => {
    return currentUser?.role === 'ADMIN';
  };

  // Filtrer les achats
  const filteredPurchases = purchases.filter(purchase => {
    const matchesSearch = 
      purchase.article.toLowerCase().includes(searchTerm.toLowerCase()) ||
      purchase.fournisseur.toLowerCase().includes(searchTerm.toLowerCase()) ||
      purchase.numeroCommande.toLowerCase().includes(searchTerm.toLowerCase());
    
    const purchaseMonth = new Date(purchase.dateCreation).toISOString().substring(0, 7);
    const matchesMonth = !filterMonth || purchaseMonth === filterMonth;
    const matchesSupplier = !filterSupplier || purchase.fournisseur === filterSupplier;
    
    return matchesSearch && matchesMonth && matchesSupplier;
  });

  // Format currency
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR'
    }).format(amount);
  };

  // Format date
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('fr-FR');
  };

  // Get unique suppliers for filter
  const uniqueSuppliers = [...new Set(purchases.map(p => p.fournisseur))].sort();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Chargement...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Historique Achat</h1>
          <p className="text-gray-600 mt-1">Gérez et analysez vos achats</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            className="bg-white"
            onClick={handleDownloadTemplate}
          >
            <Download size={20} className="mr-2" />
            Template CSV
          </Button>
          {canEdit() && (
            <Button
              className="bg-blue-600 hover:bg-blue-700 text-white"
              onClick={() => {
                setSelectedPurchase(null);
                setFormDialogOpen(true);
              }}
            >
              <Plus size={20} className="mr-2" />
              Nouvel achat
            </Button>
          )}
        </div>
      </div>

      {/* Info Import */}
      <Card className="bg-blue-50 border-blue-200">
        <CardContent className="pt-4">
          <div className="flex items-start gap-3">
            <div className="bg-blue-100 p-2 rounded-lg">
              <Upload size={20} className="text-blue-600" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-blue-900 mb-1">💡 Import de fichier Excel</h3>
              <p className="text-sm text-blue-700">
                <strong>Problème avec votre fichier Excel ?</strong> Si vous rencontrez une erreur "stylesheet", 
                voici les solutions :
              </p>
              <ol className="text-sm text-blue-700 mt-2 space-y-1 ml-4 list-decimal">
                <li>Ouvrez votre fichier Excel et <strong>Enregistrer sous → CSV</strong></li>
                <li>Ou téléchargez notre <strong>Template CSV</strong> ci-dessus et copiez vos données</li>
                <li>Utilisez la page <strong>Import/Export</strong> avec le fichier CSV</li>
              </ol>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="hover:shadow-lg transition-shadow">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Achats</p>
                <p className="text-3xl font-bold text-blue-600 mt-2">{stats?.totalAchats || 0}</p>
              </div>
              <div className="bg-blue-100 p-3 rounded-xl">
                <ShoppingCart size={24} className="text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-shadow">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Montant Total</p>
                <p className="text-3xl font-bold text-green-600 mt-2">
                  {formatCurrency(stats?.montantTotal || 0)}
                </p>
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
                <p className="text-sm font-medium text-gray-600">Quantité Totale</p>
                <p className="text-3xl font-bold text-orange-600 mt-2">
                  {Math.round(stats?.quantiteTotale || 0)}
                </p>
              </div>
              <div className="bg-orange-100 p-3 rounded-xl">
                <Calendar size={24} className="text-orange-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Statistics Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Fournisseurs */}
        <Card>
          <CardHeader>
            <CardTitle>Top Fournisseurs</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {stats?.parFournisseur?.slice(0, 5).map((item, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{item.fournisseur}</p>
                    <p className="text-sm text-gray-600">{item.count} achats</p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-blue-600">{formatCurrency(item.montant)}</p>
                    <p className="text-xs text-gray-500">{item.pourcentage}%</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Par Mois */}
        <Card>
          <CardHeader>
            <CardTitle>Achats par Mois</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 max-h-80 overflow-y-auto">
              {stats?.parMois?.slice(-6).reverse().map((item, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{item.mois}</p>
                    <p className="text-sm text-gray-600">{item.count} achats</p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-green-600">{formatCurrency(item.montant)}</p>
                    <p className="text-xs text-gray-500">{Math.round(item.quantite)} unités</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Par Site */}
        {stats?.parSite && stats.parSite.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Achats par Site</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {stats.parSite.slice(0, 5).map((item, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex-1">
                      <p className="font-medium text-gray-900">{item.site}</p>
                      <p className="text-sm text-gray-600">{item.count} achats</p>
                    </div>
                    <div className="text-right">
                      <p className="font-bold text-purple-600">{formatCurrency(item.montant)}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Top Articles */}
        <Card>
          <CardHeader>
            <CardTitle>Top Articles</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 max-h-80 overflow-y-auto">
              {stats?.articlesTop?.slice(0, 10).map((item, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{item.article}</p>
                    {item.description && (
                      <p className="text-xs text-gray-600 truncate">{item.description}</p>
                    )}
                  </div>
                  <div className="text-right ml-2">
                    <p className="font-bold text-indigo-600">{formatCurrency(item.montant)}</p>
                    <p className="text-xs text-gray-500">{Math.round(item.quantite)} unités</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters and Search */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
              <Input
                placeholder="Rechercher..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <select
              value={filterMonth}
              onChange={(e) => setFilterMonth(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2"
            >
              <option value="">Tous les mois</option>
              {stats?.parMois?.map((item) => (
                <option key={item.mois} value={item.mois}>
                  {item.mois}
                </option>
              ))}
            </select>
            <select
              value={filterSupplier}
              onChange={(e) => setFilterSupplier(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2"
            >
              <option value="">Tous les fournisseurs</option>
              {uniqueSuppliers.map((supplier) => (
                <option key={supplier} value={supplier}>
                  {supplier}
                </option>
              ))}
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Purchase List Table */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fournisseur</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">N° Commande</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Article</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Quantité</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Montant HT</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Site</th>
                  {(canEdit() || canDelete()) && (
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                  )}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredPurchases.length === 0 ? (
                  <tr>
                    <td colSpan="8" className="px-6 py-8 text-center text-gray-500">
                      Aucun achat trouvé
                    </td>
                  </tr>
                ) : (
                  filteredPurchases.map((purchase) => (
                    <tr key={purchase.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                        {formatDate(purchase.dateCreation)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {purchase.fournisseur}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                        {purchase.numeroCommande}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-700">
                        <div>
                          <p className="font-medium">{purchase.article}</p>
                          {purchase.description && (
                            <p className="text-xs text-gray-500 truncate max-w-xs">{purchase.description}</p>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                        {purchase.quantite}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-green-600">
                        {formatCurrency(purchase.montantLigneHT)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                        {purchase.site || '-'}
                      </td>
                      {(canEdit() || canDelete()) && (
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                          <div className="flex justify-end gap-2">
                            {canEdit() && (
                              <Button
                                variant="outline"
                                size="sm"
                                className="hover:bg-green-50 hover:text-green-600"
                                onClick={() => {
                                  setSelectedPurchase(purchase);
                                  setFormDialogOpen(true);
                                }}
                              >
                                <Pencil size={14} />
                              </Button>
                            )}
                            {canDelete() && (
                              <Button
                                variant="outline"
                                size="sm"
                                className="hover:bg-red-50 hover:text-red-600"
                                onClick={() => handleDelete(purchase.id)}
                              >
                                <Trash2 size={14} />
                              </Button>
                            )}
                          </div>
                        </td>
                      )}
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      <PurchaseFormDialog
        open={formDialogOpen}
        onOpenChange={setFormDialogOpen}
        purchase={selectedPurchase}
        onSuccess={loadData}
      />
    </div>
  );
};

export default PurchaseHistory;
