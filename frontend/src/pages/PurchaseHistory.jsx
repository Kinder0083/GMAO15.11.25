import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Plus, Search, ShoppingCart, TrendingUp, Calendar, Pencil, Trash2, Download, Upload, ChevronDown, ChevronRight } from 'lucide-react';
import { purchaseHistoryAPI } from '../services/api';
import { useToast } from '../hooks/use-toast';
import PurchaseFormDialog from '../components/PurchaseHistory/PurchaseFormDialog';
import { ResponsiveBar } from '@nivo/bar';

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
        console.log('Début suppression de tout l\'historique...');
        const result = await purchaseHistoryAPI.deleteAll();
        console.log('Résultat suppression:', result);
        toast({
          title: 'Succès',
          description: `${result.data.deleted_count} achats supprimés`
        });
        loadData();
      } catch (error) {
        console.error('Erreur lors de la suppression:', error);
        toast({
          title: 'Erreur',
          description: error.response?.data?.detail || 'Impossible de supprimer l\'historique',
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

  // Filtrer les commandes groupées
  const filteredGroupedPurchases = groupedPurchases.filter(order => {
    const searchLower = searchTerm.toLowerCase();
    const matchesSearch = 
      order.fournisseur.toLowerCase().includes(searchLower) ||
      order.numeroCommande.toLowerCase().includes(searchLower);
    
    const orderMonth = new Date(order.dateCreation).toISOString().substring(0, 7);
    const matchesMonth = !filterMonth || orderMonth === filterMonth;
    const matchesSupplier = !filterSupplier || order.fournisseur === filterSupplier;
    
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
  const uniqueSuppliers = [...new Set(groupedPurchases.map(p => p.fournisseur))].sort();

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
          {currentUser?.role === 'ADMIN' && (
            <Button
              variant="outline"
              className="bg-red-50 text-red-600 hover:bg-red-100 border-red-300"
              onClick={handleDeleteAll}
            >
              <Trash2 size={20} className="mr-2" />
              Supprimer tout
            </Button>
          )}
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
                <p className="text-sm font-medium text-gray-600">Commandes Totales</p>
                <p className="text-3xl font-bold text-orange-600 mt-2">
                  {stats?.commandesTotales || 0}
                </p>
                <p className="text-xs text-gray-500 mt-1">N° uniques</p>
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
        {/* Statistiques par Utilisateur - NOUVELLE SECTION */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>📊 Statistiques par Utilisateur (Créateurs de Commandes)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Utilisateur</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Nb Commandes</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Montant Total</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">% du Budget</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {stats?.par_utilisateur?.map((user, index) => (
                    <tr key={index} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm font-medium text-gray-900">{user.utilisateur}</td>
                      <td className="px-4 py-3 text-sm text-right text-blue-600 font-semibold">{user.nb_commandes}</td>
                      <td className="px-4 py-3 text-sm text-right text-green-600 font-semibold">{formatCurrency(user.montant_total)}</td>
                      <td className="px-4 py-3 text-sm text-right">
                        <div className="flex items-center justify-end gap-2">
                          <div className="w-24 bg-gray-200 rounded-full h-2">
                            <div 
                              className="bg-blue-600 h-2 rounded-full" 
                              style={{width: `${Math.min(user.pourcentage, 100)}%`}}
                            ></div>
                          </div>
                          <span className="font-medium text-gray-700">{user.pourcentage}%</span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        {/* Évolution Mensuelle des Achats - HISTOGRAMME À COLONNES */}
        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle>📈 Évolution Mensuelle des Achats</CardTitle>
          </CardHeader>
          <CardContent>
            {stats?.par_mois && stats.par_mois.length > 0 ? (
              <>
                {/* Histogramme personnalisé HTML/CSS */}
                <div className="w-full">
                  {(() => {
                    const data = stats.par_mois.slice(-12);
                    const maxValue = Math.max(...data.map(d => d.montant_total));
                    const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];
                    
                    return (
                      <div className="space-y-4">
                        {/* Graphique en barres */}
                        <div className="bg-white rounded-lg border border-gray-200 p-6">
                          {/* Axe Y avec échelle */}
                          <div className="flex gap-4">
                            {/* Labels Y */}
                            <div className="flex flex-col justify-between text-xs text-gray-500 py-2" style={{ minWidth: '60px' }}>
                              <div className="text-right">{(maxValue).toLocaleString('fr-FR')} €</div>
                              <div className="text-right">{(maxValue * 0.75).toLocaleString('fr-FR', { maximumFractionDigits: 0 })} €</div>
                              <div className="text-right">{(maxValue * 0.5).toLocaleString('fr-FR', { maximumFractionDigits: 0 })} €</div>
                              <div className="text-right">{(maxValue * 0.25).toLocaleString('fr-FR', { maximumFractionDigits: 0 })} €</div>
                              <div className="text-right">0 €</div>
                            </div>
                            
                            {/* Zone du graphique */}
                            <div className="flex-1">
                              {/* Lignes de grille horizontales */}
                              <div className="relative" style={{ height: '320px' }}>
                                {[0, 25, 50, 75, 100].map((percent) => (
                                  <div 
                                    key={percent}
                                    className="absolute w-full border-t border-gray-200"
                                    style={{ bottom: `${percent}%` }}
                                  ></div>
                                ))}
                                
                                {/* Barres */}
                                <div className="absolute inset-0 flex items-end justify-between gap-1">
                                  {data.map((item, index) => {
                                    const heightPercent = ((item.montant_total / maxValue) * 100) || 0;
                                    const color = colors[index % colors.length];
                                    
                                    return (
                                      <div key={index} className="flex-1 flex flex-col items-center justify-end group relative">
                                        {/* Valeur au-dessus de la barre */}
                                        <div className="absolute bottom-full mb-1 text-xs font-semibold opacity-0 group-hover:opacity-100 transition-opacity" style={{ color: color }}>
                                          {(item.montant_total / 1000).toFixed(0)}k
                                        </div>
                                        
                                        {/* Barre */}
                                        <div 
                                          className="w-full rounded-t-lg transition-all duration-300 hover:opacity-80 relative cursor-pointer shadow-sm hover:shadow-md"
                                          style={{ 
                                            height: `${heightPercent}%`,
                                            backgroundColor: color,
                                            minHeight: heightPercent > 0 ? '8px' : '0px'
                                          }}
                                        >
                                          {/* Tooltip au survol */}
                                          <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-10 shadow-xl">
                                            <div className="font-bold text-center">{item.mois}</div>
                                            <div className="text-center mt-1">{item.montant_total.toLocaleString('fr-FR')} €</div>
                                            <div className="text-gray-300 text-xs text-center mt-1">{item.nb_commandes} commande{item.nb_commandes > 1 ? 's' : ''}</div>
                                            <div className="text-gray-400 text-xs text-center">{item.nb_lignes} ligne{item.nb_lignes > 1 ? 's' : ''}</div>
                                          </div>
                                        </div>
                                      </div>
                                    );
                                  })}
                                </div>
                              </div>
                              
                              {/* Labels X (mois) */}
                              <div className="flex justify-between gap-1 mt-3 pt-2 border-t border-gray-300">
                                {data.map((item, index) => (
                                  <div key={index} className="flex-1 text-center">
                                    <div className="text-xs text-gray-600 font-medium transform -rotate-45 origin-center whitespace-nowrap">
                                      {item.mois}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          </div>
                        </div>
                        
                        {/* Légende */}
                        <div className="flex items-center justify-center gap-6 text-sm flex-wrap">
                          {colors.map((color, idx) => (
                            <div key={idx} className="flex items-center gap-2">
                              <div className="w-4 h-4 rounded shadow-sm" style={{ backgroundColor: color }}></div>
                              <span className="text-gray-600">
                                {['Bleu', 'Vert', 'Orange', 'Rouge', 'Violet', 'Rose'][idx]}
                              </span>
                            </div>
                          ))}
                        </div>
                        
                        {/* Info */}
                        <div className="text-center text-sm text-gray-500">
                          📊 {data.length} mois affichés • Maximum: {maxValue.toLocaleString('fr-FR')} €
                        </div>
                      </div>
                    );
                  })()}
                </div>
              </>
            ) : (
              <div className="text-center py-8 text-gray-500">
                Aucune donnée d'achat disponible pour le moment
              </div>
            )}
            
            {/* Tableau récapitulatif sous le graphique */}
            <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
              {stats?.par_mois?.slice(-3).reverse().map((month, index) => (
                <div key={index} className="border rounded-lg p-4 bg-gray-50">
                  <p className="text-sm font-semibold text-gray-700">{month.mois}</p>
                  <p className="text-2xl font-bold text-blue-600 mt-2">{formatCurrency(month.montant_total)}</p>
                  <p className="text-xs text-gray-600 mt-1">
                    {month.nb_commandes} commande{month.nb_commandes > 1 ? 's' : ''} • {month.nb_lignes} ligne{month.nb_lignes > 1 ? 's' : ''}
                  </p>
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

      {/* Purchase List Table - Grouped by Order */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase w-10"></th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fournisseur</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">N° Commande</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Montant Total HT</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nb Articles</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Site</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredGroupedPurchases.length === 0 ? (
                  <tr>
                    <td colSpan="7" className="px-6 py-8 text-center text-gray-500">
                      Aucune commande trouvée
                    </td>
                  </tr>
                ) : (
                  filteredGroupedPurchases.map((order) => {
                    const isExpanded = expandedOrders.has(order.numeroCommande);
                    return (
                      <React.Fragment key={order.numeroCommande}>
                        {/* Order Row */}
                        <tr className="hover:bg-gray-50 transition-colors cursor-pointer" onClick={() => toggleExpand(order.numeroCommande)}>
                          <td className="px-6 py-4">
                            {order.itemCount > 1 && (
                              <button className="text-gray-600 hover:text-blue-600">
                                {isExpanded ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
                              </button>
                            )}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                            {formatDate(order.dateCreation)}
                          </td>
                          <td className="px-6 py-4 text-sm font-medium text-gray-900">
                            {order.fournisseur}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                            {order.numeroCommande}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-green-600">
                            {formatCurrency(order.montantTotal)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                            <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs">
                              {order.itemCount} article{order.itemCount > 1 ? 's' : ''}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                            {order.site || '-'}
                          </td>
                        </tr>
                        
                        {/* Expanded Items - Detail Table with Different Columns */}
                        {isExpanded && (
                          <tr>
                            <td colSpan="7" className="px-0 py-0 bg-blue-50">
                              <div className="px-6 py-4">
                                <div className="bg-white rounded-lg shadow-sm overflow-hidden">
                                  <table className="w-full">
                                    <thead className="bg-gray-100">
                                      <tr>
                                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-600">Article</th>
                                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-600">Description</th>
                                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-600">N° Réception</th>
                                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-600">Quantité</th>
                                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-600">Montant HT</th>
                                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-600">Groupe Stat.</th>
                                      </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-200">
                                      {order.items.map((item, idx) => (
                                        <tr key={`${order.numeroCommande}-${idx}`} className="hover:bg-gray-50">
                                          <td className="px-4 py-3 text-sm text-gray-900 font-medium">
                                            {item.article || '-'}
                                          </td>
                                          <td className="px-4 py-3 text-sm text-gray-700">
                                            {item.description || '-'}
                                          </td>
                                          <td className="px-4 py-3 text-sm text-gray-700 whitespace-nowrap">
                                            {item.numeroReception || '-'}
                                          </td>
                                          <td className="px-4 py-3 text-sm text-gray-700">
                                            {item.quantite || 0}
                                          </td>
                                          <td className="px-4 py-3 text-sm font-medium text-green-600">
                                            {formatCurrency(item.montantLigneHT)}
                                          </td>
                                          <td className="px-4 py-3 text-sm text-gray-600">
                                            {item.groupeStatistique || '-'}
                                          </td>
                                        </tr>
                                      ))}
                                    </tbody>
                                  </table>
                                </div>
                              </div>
                            </td>
                          </tr>
                        )}
                      </React.Fragment>
                    );
                  })
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
