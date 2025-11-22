import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Calendar, ChevronLeft, ChevronRight, Wrench, Plus } from 'lucide-react';
import { assetsAPI, demandesArretAPI } from '../services/api';
import { useToast } from '../hooks/use-toast';
import { useAutoRefresh } from '../hooks/useAutoRefresh';
import DemandeArretDialog from '../components/PlanningMPrev/DemandeArretDialog';

const PlanningMPrev = () => {
  const { toast } = useToast();
  const [equipments, setEquipments] = useState([]);
  const [currentYear, setCurrentYear] = useState(new Date().getFullYear());
  const [planningEntries, setPlanningEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);

  const loadEquipments = async () => {
    try {
      const response = await assetsAPI.getAll();
      setEquipments(response.data || []);
    } catch (error) {
      console.error('Erreur chargement équipements:', error);
      toast({
        title: 'Erreur',
        description: 'Impossible de charger les équipements',
        variant: 'destructive'
      });
    }
  };

  const loadPlanningEntries = async () => {
    try {
      setLoading(true);
      const startDate = new Date(currentYear, 0, 1).toISOString().split('T')[0];
      const endDate = new Date(currentYear, 11, 31).toISOString().split('T')[0];
      
      const entries = await demandesArretAPI.getPlanningEquipements({
        date_debut: startDate,
        date_fin: endDate
      });
      
      setPlanningEntries(entries);
    } catch (error) {
      console.error('Erreur chargement planning:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEquipments();
    loadPlanningEntries();
  }, [currentYear]);

  // Rafraîchissement automatique toutes les 30 secondes
  useAutoRefresh(() => {
    loadEquipments();
    loadPlanningEntries();
  }, [currentYear]);

  const getMonths = () => {
    return [
      'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
      'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
    ];
  };

  const getEquipmentStatusForMonth = (equipmentId, monthIndex) => {
    // Vérifier s'il y a des entrées de planning pour cet équipement ce mois-ci
    const monthStart = new Date(currentYear, monthIndex, 1);
    const monthEnd = new Date(currentYear, monthIndex + 1, 0);

    const entriesInMonth = planningEntries.filter(entry => {
      if (entry.equipement_id !== equipmentId) return false;
      
      const entryStart = new Date(entry.date_debut);
      const entryEnd = new Date(entry.date_fin);
      
      // Vérifier si l'entrée chevauche ce mois
      return entryStart <= monthEnd && entryEnd >= monthStart;
    });

    if (entriesInMonth.length === 0) {
      // Utiliser le statut de l'équipement
      const equipment = equipments.find(e => e.id === equipmentId);
      return equipment?.status || 'OPERATIONAL';
    }

    // S'il y a une entrée de maintenance, retourner EN_MAINTENANCE
    return 'EN_MAINTENANCE';
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'OPERATIONAL':
        return 'bg-green-500';
      case 'EN_MAINTENANCE':
        return 'bg-orange-500';
      case 'HORS_SERVICE':
        return 'bg-red-500';
      default:
        return 'bg-gray-300';
    }
  };

  const getStatusLabel = (status) => {
    switch (status) {
      case 'OPERATIONAL':
        return 'Opérationnel';
      case 'EN_MAINTENANCE':
        return 'En Maintenance';
      case 'HORS_SERVICE':
        return 'Hors Service';
      default:
        return 'Inconnu';
    }
  };

  const goToPreviousYear = () => {
    setCurrentYear(prev => prev - 1);
  };

  const goToNextYear = () => {
    setCurrentYear(prev => prev + 1);
  };

  const goToCurrentYear = () => {
    setCurrentYear(new Date().getFullYear());
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-lg">Chargement du planning...</div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Planning Maintenance Préventive Annuel
            </CardTitle>
            <Button onClick={() => setDialogOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Demande d'Arrêt
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {/* Navigation année */}
          <div className="flex items-center justify-between mb-6">
            <Button variant="outline" onClick={goToPreviousYear}>
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <div className="flex items-center gap-4">
              <h2 className="text-2xl font-bold">{currentYear}</h2>
              <Button variant="ghost" size="sm" onClick={goToCurrentYear}>
                Aujourd'hui
              </Button>
            </div>
            <Button variant="outline" onClick={goToNextYear}>
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>

          {/* Légende */}
          <div className="flex items-center gap-4 mb-4 p-3 bg-gray-50 rounded">
            <span className="text-sm font-semibold">Légende :</span>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-green-500 rounded"></div>
              <span className="text-sm">Opérationnel</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-orange-500 rounded"></div>
              <span className="text-sm">En Maintenance</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-red-500 rounded"></div>
              <span className="text-sm">Hors Service</span>
            </div>
          </div>

          {/* Table planning */}
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <th className="border p-2 bg-gray-100 sticky left-0 z-10 min-w-[200px]">
                    <div className="flex items-center gap-2">
                      <Wrench className="h-4 w-4" />
                      Équipement
                    </div>
                  </th>
                  {getMonths().map((month, index) => (
                    <th key={index} className="border p-2 bg-gray-100 text-sm">
                      {month.substring(0, 3)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {equipments.length === 0 ? (
                  <tr>
                    <td colSpan={13} className="text-center p-8 text-gray-500">
                      Aucun équipement enregistré
                    </td>
                  </tr>
                ) : (
                  equipments.map(equipment => (
                    <tr key={equipment.id}>
                      <td className="border p-2 font-medium sticky left-0 bg-white z-10">
                        <div>
                          <div className="font-semibold">{equipment.name}</div>
                          <div className="text-xs text-gray-500">{equipment.category}</div>
                        </div>
                      </td>
                      {getMonths().map((_, monthIndex) => {
                        const status = getEquipmentStatusForMonth(equipment.id, monthIndex);
                        return (
                          <td key={monthIndex} className="border p-1">
                            <div
                              className={`h-8 rounded ${getStatusColor(status)} transition-colors cursor-pointer hover:opacity-80`}
                              title={`${equipment.name} - ${getStatusLabel(status)}`}
                            />
                          </td>
                        );
                      })}
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Statistiques */}
          <div className="grid grid-cols-3 gap-4 mt-6">
            <Card>
              <CardContent className="pt-6">
                <div className="text-2xl font-bold">
                  {equipments.filter(e => e.status === 'OPERATIONAL').length}
                </div>
                <div className="text-sm text-gray-600">Équipements opérationnels</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-2xl font-bold">
                  {equipments.filter(e => e.status === 'EN_MAINTENANCE').length}
                </div>
                <div className="text-sm text-gray-600">En maintenance</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-2xl font-bold">
                  {equipments.filter(e => e.status === 'HORS_SERVICE').length}
                </div>
                <div className="text-sm text-gray-600">Hors service</div>
              </CardContent>
            </Card>
          </div>
        </CardContent>
      </Card>

      {/* Dialog Demande d'Arrêt */}
      <DemandeArretDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        onSuccess={() => {
          loadPlanningEntries();
          toast({
            title: 'Succès',
            description: 'Demande d\'arrêt envoyée avec succès'
          });
        }}
      />
    </div>
  );
};

export default PlanningMPrev;
