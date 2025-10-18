import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Plus, Search, Filter, Eye, Pencil, Trash2 } from 'lucide-react';
import WorkOrderDialog from '../components/WorkOrders/WorkOrderDialog';
import WorkOrderFormDialog from '../components/WorkOrders/WorkOrderFormDialog';
import DeleteConfirmDialog from '../components/Common/DeleteConfirmDialog';
import { workOrdersAPI } from '../services/api';
import { useToast } from '../hooks/use-toast';

const WorkOrders = () => {
  const { toast } = useToast();
  const [workOrders, setWorkOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('ALL');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formDialogOpen, setFormDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedWorkOrder, setSelectedWorkOrder] = useState(null);
  const [itemToDelete, setItemToDelete] = useState(null);

  useEffect(() => {
    loadWorkOrders();
  }, []);

  const loadWorkOrders = async () => {
    try {
      setLoading(true);
      const response = await workOrdersAPI.getAll();
      setWorkOrders(response.data);
    } catch (error) {
      toast({
        title: 'Erreur',
        description: 'Impossible de charger les ordres de travail',
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
      await workOrdersAPI.delete(itemToDelete);
      toast({
        title: 'Succès',
        description: 'Ordre de travail supprimé'
      });
      loadWorkOrders();
    } catch (error) {
      toast({
        title: 'Erreur',
        description: 'Impossible de supprimer l\'ordre de travail',
        variant: 'destructive'
      });
    } finally {
      setDeleteDialogOpen(false);
      setItemToDelete(null);
    }
  };

  const filteredWorkOrders = workOrders.filter(wo => {
    const matchesSearch = wo.titre.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         wo.id.includes(searchTerm);
    const matchesStatus = filterStatus === 'ALL' || wo.statut === filterStatus;
    return matchesSearch && matchesStatus;
  });

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

  const handleViewWorkOrder = (wo) => {
    setSelectedWorkOrder(wo);
    setDialogOpen(true);
  };

  const statuses = [
    { value: 'ALL', label: 'Tous' },
    { value: 'OUVERT', label: 'Ouvert' },
    { value: 'EN_COURS', label: 'En cours' },
    { value: 'EN_ATTENTE', label: 'En attente' },
    { value: 'TERMINE', label: 'Terminé' }
  ];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Ordres de travail</h1>
          <p className="text-gray-600 mt-1">Gérez tous vos ordres de maintenance</p>
        </div>
        <Button
          onClick={() => {
            setSelectedWorkOrder(null);
            setFormDialogOpen(true);
          }}
          className="bg-blue-600 hover:bg-blue-700 text-white"
        >
          <Plus size={20} className="mr-2" />
          Nouvel ordre
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
                  placeholder="Rechercher par titre ou ID..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <div className="flex gap-2">
              <Filter size={20} className="text-gray-400 mt-2" />
              <div className="flex gap-2 flex-wrap">
                {statuses.map(status => (
                  <Button
                    key={status.value}
                    variant={filterStatus === status.value ? 'default' : 'outline'}
                    onClick={() => setFilterStatus(status.value)}
                    size="sm"
                    className={filterStatus === status.value ? 'bg-blue-600 hover:bg-blue-700' : ''}
                  >
                    {status.label}
                  </Button>
                ))}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Work Orders Table */}
      <Card>
        <CardHeader>
          <CardTitle>Liste des ordres ({filteredWorkOrders.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8">
              <p className="text-gray-500">Chargement...</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">ID</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Statut</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Titre</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Priorité</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Assigné à</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Emplacement</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Équipement</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Date limite</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredWorkOrders.map((wo) => (
                    <tr key={wo.id} className="border-b hover:bg-gray-50 transition-colors">
                      <td className="py-3 px-4 text-sm text-gray-900 font-medium">#{wo.numero}</td>
                      <td className="py-3 px-4">{getStatusBadge(wo.statut)}</td>
                      <td className="py-3 px-4 text-sm text-gray-900 font-medium">{wo.titre}</td>
                      <td className="py-3 px-4">{getPriorityBadge(wo.priorite)}</td>
                      <td className="py-3 px-4 text-sm text-gray-700">
                        {wo.assigneA ? (
                          <div className="flex items-center gap-2">
                            <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                              <span className="text-white text-xs font-medium">
                                {wo.assigneA.prenom[0]}{wo.assigneA.nom[0]}
                              </span>
                            </div>
                            <span>{wo.assigneA.prenom} {wo.assigneA.nom}</span>
                          </div>
                        ) : (
                          <span className="text-gray-400">Non assigné</span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-700">
                        {wo.emplacement ? wo.emplacement.nom : '-'}
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-700">
                        {wo.equipement ? wo.equipement.nom : '-'}
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-700">
                        {wo.dateLimite ? new Date(wo.dateLimite).toLocaleDateString('fr-FR') : '-'}
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setSelectedWorkOrder(wo);
                              setDialogOpen(true);
                            }}
                            className="hover:bg-blue-50 hover:text-blue-600"
                          >
                            <Eye size={16} />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setSelectedWorkOrder(wo);
                              setFormDialogOpen(true);
                            }}
                            className="hover:bg-green-50 hover:text-green-600"
                          >
                            <Pencil size={16} />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDelete(wo.id)}
                            className="hover:bg-red-50 hover:text-red-600"
                          >
                            <Trash2 size={16} />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <WorkOrderDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        workOrder={selectedWorkOrder}
      />

      <WorkOrderFormDialog
        open={formDialogOpen}
        onOpenChange={setFormDialogOpen}
        workOrder={selectedWorkOrder}
        onSuccess={loadWorkOrders}
      />

      <DeleteConfirmDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        onConfirm={confirmDelete}
        title="Supprimer l'ordre de travail"
        description="Êtes-vous sûr de vouloir supprimer cet ordre de travail ? Cette action est irréversible."
      />
    </div>
  );
};

export default WorkOrders;