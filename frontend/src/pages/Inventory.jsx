import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Plus, Search, Package, AlertTriangle, TrendingDown, Pencil, Trash2 } from 'lucide-react';
import InventoryFormDialog from '../components/Inventory/InventoryFormDialog';
import { inventoryAPI } from '../services/api';
import { useToast } from '../hooks/use-toast';

const Inventory = () => {
  const { toast } = useToast();
  const [inventory, setInventory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [formDialogOpen, setFormDialogOpen] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);

  useEffect(() => {
    loadInventory();
  }, []);

  const loadInventory = async () => {
    try {
      setLoading(true);
      const response = await inventoryAPI.getAll();
      setInventory(response.data);
    } catch (error) {
      toast({
        title: 'Erreur',
        description: 'Impossible de charger l\'inventaire',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Êtes-vous sûr de vouloir supprimer cet article ?')) {
      try {
        await inventoryAPI.delete(id);
        toast({
          title: 'Succès',
          description: 'Article supprimé'
        });
        loadInventory();
      } catch (error) {
        toast({
          title: 'Erreur',
          description: 'Impossible de supprimer l\'article',
          variant: 'destructive'
        });
      }
    }
  };

  const filteredInventory = inventory.filter(item => {
    return item.nom.toLowerCase().includes(searchTerm.toLowerCase()) ||
           item.reference.toLowerCase().includes(searchTerm.toLowerCase()) ||
           item.categorie.toLowerCase().includes(searchTerm.toLowerCase());
  });

  const lowStockItems = inventory.filter(item => item.quantite <= item.quantiteMin);
  const totalValue = inventory.reduce((sum, item) => sum + (item.quantite * item.prixUnitaire), 0);

  const getStockStatus = (item) => {
    if (item.quantite === 0) {
      return { color: 'text-red-600', bg: 'bg-red-100', label: 'Rupture', icon: AlertTriangle };
    } else if (item.quantite <= item.quantiteMin) {
      return { color: 'text-orange-600', bg: 'bg-orange-100', label: 'Stock bas', icon: TrendingDown };
    }
    return { color: 'text-green-600', bg: 'bg-green-100', label: 'En stock', icon: Package };
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Inventaire</h1>
          <p className="text-gray-600 mt-1">Gérez vos pièces et fournitures</p>
        </div>
        <Button className="bg-blue-600 hover:bg-blue-700 text-white" onClick={() => {
          setSelectedItem(null);
          setFormDialogOpen(true);
        }}>
          <Plus size={20} className="mr-2" />
          Nouvel article
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="hover:shadow-lg transition-shadow">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Articles totaux</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{inventory.length}</p>
              </div>
              <div className="bg-blue-100 p-3 rounded-xl">
                <Package size={24} className="text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-shadow">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Valeur totale</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">
                  {totalValue.toLocaleString('fr-FR')} €
                </p>
              </div>
              <div className="bg-green-100 p-3 rounded-xl">
                <TrendingDown size={24} className="text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-shadow">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Alertes stock bas</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{lowStockItems.length}</p>
              </div>
              <div className="bg-orange-100 p-3 rounded-xl">
                <AlertTriangle size={24} className="text-orange-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Low Stock Alert */}
      {lowStockItems.length > 0 && (
        <Card className="border-orange-200 bg-orange-50">
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <AlertTriangle className="text-orange-600 mt-1" size={20} />
              <div>
                <h3 className="font-semibold text-orange-900">Alerte de stock bas</h3>
                <p className="text-sm text-orange-700 mt-1">
                  {lowStockItems.length} article(s) nécessite(nt) un réapprovisionnement :
                  <span className="font-medium"> {lowStockItems.map(item => item.nom).join(', ')}</span>
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Search */}
      <Card>
        <CardContent className="pt-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            <Input
              placeholder="Rechercher par nom, référence ou catégorie..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
        </CardContent>
      </Card>

      {/* Inventory Table */}
      <Card>
        <CardHeader>
          <CardTitle>Liste des articles ({filteredInventory.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Référence</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Nom</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Catégorie</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Quantité</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Min.</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Prix unitaire</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Valeur totale</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Fournisseur</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Emplacement</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Statut</th>
                </tr>
              </thead>
              <tbody>
                {filteredInventory.map((item) => {
                  const status = getStockStatus(item);
                  const StatusIcon = status.icon;
                  return (
                    <tr key={item.id} className="border-b hover:bg-gray-50 transition-colors">
                      <td className="py-3 px-4 text-sm text-gray-900 font-medium">{item.reference}</td>
                      <td className="py-3 px-4 text-sm text-gray-900 font-medium">{item.nom}</td>
                      <td className="py-3 px-4 text-sm text-gray-700">{item.categorie}</td>
                      <td className="py-3 px-4 text-sm text-gray-900 font-bold">{item.quantite}</td>
                      <td className="py-3 px-4 text-sm text-gray-600">{item.quantiteMin}</td>
                      <td className="py-3 px-4 text-sm text-gray-700">{item.prixUnitaire.toFixed(2)} €</td>
                      <td className="py-3 px-4 text-sm text-gray-900 font-medium">
                        {(item.quantite * item.prixUnitaire).toFixed(2)} €
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-700">{item.fournisseur}</td>
                      <td className="py-3 px-4 text-sm text-gray-600">{item.emplacement}</td>
                      <td className="py-3 px-4">
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${status.bg} ${status.color} flex items-center gap-1 w-fit`}>
                          <StatusIcon size={14} />
                          {status.label}
                        </span>
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

export default Inventory;