import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Plus, Search, Eye, Pencil, Trash2, TrendingUp, Activity } from 'lucide-react';
import MeterDialog from '../components/Meters/MeterDialog';
import MeterFormDialog from '../components/Meters/MeterFormDialog';
import DeleteConfirmDialog from '../components/Common/DeleteConfirmDialog';
import { metersAPI } from '../services/api';
import { useToast } from '../hooks/use-toast';

const Meters = () => {
  const { toast } = useToast();
  const [meters, setMeters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('ALL');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formDialogOpen, setFormDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedMeter, setSelectedMeter] = useState(null);
  const [itemToDelete, setItemToDelete] = useState(null);

  useEffect(() => {
    loadMeters();
  }, []);

  const loadMeters = async () => {
    try {
      setLoading(true);
      const response = await metersAPI.getAll();
      setMeters(response.data);
    } catch (error) {
      toast({
        title: 'Erreur',
        description: 'Impossible de charger les compteurs',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    setItemToDelete(id);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = async () => {
    if (!itemToDelete) return;
    
    try {
      await metersAPI.delete(itemToDelete);
      toast({
        title: 'Succès',
        description: 'Compteur supprimé'
      });
      loadMeters();
    } catch (error) {
      toast({
        title: 'Erreur',
        description: 'Impossible de supprimer le compteur',
        variant: 'destructive'
      });
    } finally {
      setDeleteDialogOpen(false);
      setItemToDelete(null);
    }
  };

  const filteredMeters = meters.filter(meter => {
    const matchesSearch = meter.nom.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         (meter.numero_serie && meter.numero_serie.includes(searchTerm));
    const matchesType = filterType === 'ALL' || meter.type === filterType;
    return matchesSearch && matchesType;
  });

  const getTypeBadge = (type) => {
    const badges = {
      'EAU': { bg: 'bg-blue-100', text: 'text-blue-700', label: 'Eau' },
      'GAZ': { bg: 'bg-orange-100', text: 'text-orange-700', label: 'Gaz' },
      'ELECTRICITE': { bg: 'bg-yellow-100', text: 'text-yellow-700', label: 'Électricité' },
      'AIR_COMPRIME': { bg: 'bg-gray-100', text: 'text-gray-700', label: 'Air comprimé' },
      'VAPEUR': { bg: 'bg-purple-100', text: 'text-purple-700', label: 'Vapeur' },
      'FUEL': { bg: 'bg-red-100', text: 'text-red-700', label: 'Fuel' },
      'SOLAIRE': { bg: 'bg-green-100', text: 'text-green-700', label: 'Solaire' },
      'AUTRE': { bg: 'bg-gray-100', text: 'text-gray-600', label: 'Autre' }
    };
    const badge = badges[type] || badges['AUTRE'];
    return (
      <span className={`px-3 py-1 rounded-full text-xs font-medium ${badge.bg} ${badge.text}`}>
        {badge.label}
      </span>
    );
  };

  const types = [
    { value: 'ALL', label: 'Tous' },
    { value: 'EAU', label: 'Eau' },
    { value: 'GAZ', label: 'Gaz' },
    { value: 'ELECTRICITE', label: 'Électricité' },
    { value: 'AIR_COMPRIME', label: 'Air comprimé' },
    { value: 'VAPEUR', label: 'Vapeur' },
    { value: 'FUEL', label: 'Fuel' },
    { value: 'SOLAIRE', label: 'Solaire' },
    { value: 'AUTRE', label: 'Autre' }
  ];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Compteurs</h1>
          <p className="text-gray-600 mt-1">Gérez vos compteurs et relevés de consommation</p>
        </div>
        <Button className="bg-blue-600 hover:bg-blue-700 text-white" onClick={() => {
          setSelectedMeter(null);
          setFormDialogOpen(true);
        }}>
          <Plus size={20} className="mr-2" />
          Nouveau compteur
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
                <Input
                  placeholder="Rechercher par nom ou numéro de série..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <div className="flex gap-2 flex-wrap">
              {types.map(type => (
                <Button
                  key={type.value}
                  variant={filterType === type.value ? 'default' : 'outline'}
                  onClick={() => setFilterType(type.value)}
                  size="sm"
                  className={filterType === type.value ? 'bg-blue-600 hover:bg-blue-700' : ''}
                >
                  {type.label}
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Meters Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {loading ? (
          <div className="col-span-full text-center py-8">
            <p className="text-gray-500">Chargement...</p>
          </div>
        ) : filteredMeters.length === 0 ? (
          <div className="col-span-full text-center py-8">
            <p className="text-gray-500">Aucun compteur trouvé</p>
          </div>
        ) : (
          filteredMeters.map((meter) => (
            <Card key={meter.id} className="hover:shadow-lg transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <CardTitle className="text-lg">{meter.nom}</CardTitle>
                    {meter.numero_serie && (
                      <p className="text-sm text-gray-500 mt-1">N° {meter.numero_serie}</p>
                    )}
                  </div>
                  {getTypeBadge(meter.type)}
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {meter.emplacement && (
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <Activity size={16} />
                      <span>{meter.emplacement.nom}</span>
                    </div>
                  )}
                  
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-gray-600">Unité:</span>
                    <span className="font-medium text-gray-900">{meter.unite}</span>
                  </div>
                  
                  {meter.prix_unitaire && (
                    <div className="flex items-center gap-2 text-sm">
                      <span className="text-gray-600">Prix:</span>
                      <span className="font-medium text-gray-900">{meter.prix_unitaire} €/{meter.unite}</span>
                    </div>
                  )}
                  
                  <div className="flex gap-2 mt-4 pt-4 border-t">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setSelectedMeter(meter);
                        setDialogOpen(true);
                      }}
                      className="flex-1 hover:bg-blue-50 hover:text-blue-600"
                    >
                      <Eye size={16} className="mr-1" />
                      Voir
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setSelectedMeter(meter);
                        setFormDialogOpen(true);
                      }}
                      className="flex-1 hover:bg-green-50 hover:text-green-600"
                    >
                      <Pencil size={16} className="mr-1" />
                      Modifier
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(meter.id)}
                      className="hover:bg-red-50 hover:text-red-600"
                    >
                      <Trash2 size={16} />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      <MeterDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        meter={selectedMeter}
        onSuccess={loadMeters}
      />

      <MeterFormDialog
        open={formDialogOpen}
        onOpenChange={setFormDialogOpen}
        meter={selectedMeter}
        onSuccess={loadMeters}
      />

      <DeleteConfirmDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        onConfirm={confirmDelete}
        title="Supprimer le compteur"
        description="Êtes-vous sûr de vouloir supprimer ce compteur ? Tous les relevés associés seront conservés mais le compteur ne sera plus accessible."
      />
    </div>
  );
};

export default Meters;