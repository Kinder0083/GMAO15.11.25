import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Plus, Search, Wrench, AlertCircle, CheckCircle2, Clock, Pencil, Trash2 } from 'lucide-react';
import EquipmentFormDialog from '../components/Equipment/EquipmentFormDialog';
import DeleteConfirmDialog from '../components/Common/DeleteConfirmDialog';
import { equipmentsAPI } from '../services/api';
import { useToast } from '../hooks/use-toast';

const Assets = () => {
  const { toast } = useToast();
  const [equipments, setEquipments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('ALL');
  const [formDialogOpen, setFormDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedEquipment, setSelectedEquipment] = useState(null);
  const [itemToDelete, setItemToDelete] = useState(null);

  useEffect(() => {
    loadEquipments();
  }, []);

  const loadEquipments = async () => {
    try {
      setLoading(true);
      const response = await equipmentsAPI.getAll();
      setEquipments(response.data);
    } catch (error) {
      toast({
        title: 'Erreur',
        description: 'Impossible de charger les équipements',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Êtes-vous sûr de vouloir supprimer cet équipement ?')) {
      try {
        await equipmentsAPI.delete(id);
        toast({
          title: 'Succès',
          description: 'Équipement supprimé'
        });
        loadEquipments();
      } catch (error) {
        toast({
          title: 'Erreur',
          description: 'Impossible de supprimer l\'équipement',
          variant: 'destructive'
        });
      }
    }
  };

  const filteredEquipments = equipments.filter(eq => {
    const matchesSearch = eq.nom.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         eq.numeroSerie.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = filterStatus === 'ALL' || eq.statut === filterStatus;
    return matchesSearch && matchesStatus;
  });

  const getStatusBadge = (statut) => {
    const badges = {
      'OPERATIONNEL': { 
        bg: 'bg-green-100', 
        text: 'text-green-700', 
        label: 'Opérationnel',
        icon: CheckCircle2,
        iconColor: 'text-green-600'
      },
      'EN_MAINTENANCE': { 
        bg: 'bg-orange-100', 
        text: 'text-orange-700', 
        label: 'En maintenance',
        icon: Clock,
        iconColor: 'text-orange-600'
      },
      'HORS_SERVICE': { 
        bg: 'bg-red-100', 
        text: 'text-red-700', 
        label: 'Hors service',
        icon: AlertCircle,
        iconColor: 'text-red-600'
      }
    };
    const badge = badges[statut] || badges['OPERATIONNEL'];
    const Icon = badge.icon;
    return (
      <span className={`px-3 py-1 rounded-full text-xs font-medium ${badge.bg} ${badge.text} flex items-center gap-1 w-fit`}>
        <Icon size={14} className={badge.iconColor} />
        {badge.label}
      </span>
    );
  };

  const statuses = [
    { value: 'ALL', label: 'Tous', count: equipments.length },
    { value: 'OPERATIONNEL', label: 'Opérationnel', count: equipments.filter(e => e.statut === 'OPERATIONNEL').length },
    { value: 'EN_MAINTENANCE', label: 'En maintenance', count: equipments.filter(e => e.statut === 'EN_MAINTENANCE').length },
    { value: 'HORS_SERVICE', label: 'Hors service', count: equipments.filter(e => e.statut === 'HORS_SERVICE').length }
  ];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Équipements</h1>
          <p className="text-gray-600 mt-1">Gérez votre parc d'équipements</p>
        </div>
        <Button className="bg-blue-600 hover:bg-blue-700 text-white" onClick={() => {
          setSelectedEquipment(null);
          setFormDialogOpen(true);
        }}>
          <Plus size={20} className="mr-2" />
          Nouvel équipement
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="hover:shadow-lg transition-shadow">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Opérationnel</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">
                  {equipments.filter(e => e.statut === 'OPERATIONNEL').length}
                </p>
              </div>
              <div className="bg-green-100 p-3 rounded-xl">
                <CheckCircle2 size={24} className="text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-shadow">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">En maintenance</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">
                  {equipments.filter(e => e.statut === 'EN_MAINTENANCE').length}
                </p>
              </div>
              <div className="bg-orange-100 p-3 rounded-xl">
                <Clock size={24} className="text-orange-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-shadow">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Hors service</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">
                  {equipments.filter(e => e.statut === 'HORS_SERVICE').length}
                </p>
              </div>
              <div className="bg-red-100 p-3 rounded-xl">
                <AlertCircle size={24} className="text-red-600" />
              </div>
            </div>
          </CardContent>
        </Card>
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
              {statuses.map(status => (
                <Button
                  key={status.value}
                  variant={filterStatus === status.value ? 'default' : 'outline'}
                  onClick={() => setFilterStatus(status.value)}
                  size="sm"
                  className={filterStatus === status.value ? 'bg-blue-600 hover:bg-blue-700' : ''}
                >
                  {status.label} ({status.count})
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Equipment Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {loading ? (
          <div className="col-span-full text-center py-8">
            <p className="text-gray-500">Chargement...</p>
          </div>
        ) : filteredEquipments.length === 0 ? (
          <div className="col-span-full text-center py-8">
            <p className="text-gray-500">Aucun équipement trouvé</p>
          </div>
        ) : (
          filteredEquipments.map((equipment) => (
            <Card key={equipment.id} className="hover:shadow-xl transition-all duration-300 cursor-pointer group">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center group-hover:bg-blue-200 transition-colors">
                      <Wrench size={24} className="text-blue-600" />
                    </div>
                    <div>
                      <CardTitle className="text-lg">{equipment.nom}</CardTitle>
                      <p className="text-sm text-gray-500 mt-1">{equipment.categorie}</p>
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {getStatusBadge(equipment.statut)}
                  
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">N° Série:</span>
                      <span className="font-medium text-gray-900">{equipment.numeroSerie}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Emplacement:</span>
                      <span className="font-medium text-gray-900">{equipment.emplacement?.nom || '-'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Date d'achat:</span>
                      <span className="font-medium text-gray-900">
                        {equipment.dateAchat ? new Date(equipment.dateAchat).toLocaleDateString('fr-FR') : '-'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Coût d'achat:</span>
                      <span className="font-medium text-gray-900">{equipment.coutAchat?.toLocaleString('fr-FR')} €</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Garantie:</span>
                      <span className="font-medium text-gray-900">{equipment.garantie}</span>
                    </div>
                    {equipment.derniereMaintenance && (
                      <div className="flex justify-between">
                        <span className="text-gray-600">Dernière maintenance:</span>
                        <span className="font-medium text-gray-900">
                          {new Date(equipment.derniereMaintenance).toLocaleDateString('fr-FR')}
                        </span>
                      </div>
                    )}
                  </div>

                  <div className="flex gap-2 pt-2">
                    <Button 
                      variant="outline" 
                      className="flex-1 hover:bg-green-50 hover:text-green-600"
                      onClick={() => {
                        setSelectedEquipment(equipment);
                        setFormDialogOpen(true);
                      }}
                    >
                      <Pencil size={16} className="mr-1" />
                      Modifier
                    </Button>
                    <Button 
                      variant="outline" 
                      className="hover:bg-red-50 hover:text-red-600"
                      onClick={() => handleDelete(equipment.id)}
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

      <EquipmentFormDialog
        open={formDialogOpen}
        onOpenChange={setFormDialogOpen}
        equipment={selectedEquipment}
        onSuccess={loadEquipments}
      />
    </div>
  );
};

export default Assets;