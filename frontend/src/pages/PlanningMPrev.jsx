import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Calendar, ChevronLeft, ChevronRight, Wrench, Plus } from 'lucide-react';
import { equipmentsAPI, demandesArretAPI } from '../services/api';
import { useToast } from '../hooks/use-toast';
import { useAutoRefresh } from '../hooks/useAutoRefresh';
import DemandeArretDialog from '../components/PlanningMPrev/DemandeArretDialog';

const PlanningMPrev = () => {
  const { toast } = useToast();
  const [equipments, setEquipments] = useState([]);
  const [currentDate, setCurrentDate] = useState(new Date());
  const [planningEntries, setPlanningEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);

  const loadEquipments = async () => {
    try {
      const response = await equipmentsAPI.getAll();
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
      const year = currentDate.getFullYear();
      const month = currentDate.getMonth();
      const startDate = new Date(year, month, 1).toISOString().split('T')[0];
      const endDate = new Date(year, month + 1, 0).toISOString().split('T')[0];
      
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
  }, [currentDate]);

  // Rafraîchissement automatique toutes les 30 secondes
  useAutoRefresh(() => {
    loadEquipments();
    loadPlanningEntries();
  }, [currentDate]);

  const getDaysInMonth = () => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const days = [];

    for (let d = 1; d <= lastDay.getDate(); d++) {
      days.push(new Date(year, month, d));
    }

    return days;
  };

  // Obtenir le statut de l'équipement pour une demi-journée spécifique
  const getEquipmentStatusForHalfDay = (equipmentId, date, isAM) => {
    const dateStr = date.toISOString().split('T')[0];
    
    // Chercher une entrée de planning pour cette date et cet équipement
    const entry = planningEntries.find(e => {
      if (e.equipement_id !== equipmentId) return false;
      
      const entryStart = new Date(e.date_debut);
      const entryEnd = new Date(e.date_fin);
      const currentDate = new Date(dateStr);
      
      // Vérifier si la date est dans la plage
      if (currentDate < entryStart || currentDate > entryEnd) return false;
      
      // Vérifier la demi-journée
      if (currentDate.toISOString().split('T')[0] === e.date_debut) {
        // Premier jour
        if (e.periode_debut === 'APRES_MIDI' && isAM) return false;
      }
      
      if (currentDate.toISOString().split('T')[0] === e.date_fin) {
        // Dernier jour
        if (e.periode_fin === 'MATIN' && !isAM) return false;
      }
      
      return true;
    });

    if (entry) {
      return entry.statut || 'EN_MAINTENANCE';
    }

    // Utiliser le statut de l'équipement
    const equipment = equipments.find(e => e.id === equipmentId);
    return equipment?.status || 'OPERATIONAL';
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'OPERATIONAL':
        return '#10b981'; // Vert
      case 'EN_MAINTENANCE':
        return '#f59e0b'; // Orange
      case 'HORS_SERVICE':
        return '#ef4444'; // Rouge
      default:
        return '#9ca3af'; // Gris
    }
  };

  const goToPreviousMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1));
  };

  const goToNextMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1));
  };

  const goToToday = () => {
    setCurrentDate(new Date());
  };

  const monthNames = [
    'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
    'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
  ];

  const days = getDaysInMonth();
  const today = new Date().toISOString().split('T')[0];

  if (loading && equipments.length === 0) {
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
              Planning Maintenance Préventive
            </CardTitle>
            <Button onClick={() => setDialogOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Demande d'Arrêt
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {/* Navigation mois */}
          <div className="flex items-center justify-between mb-6">
            <Button variant="outline" onClick={goToPreviousMonth}>
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <div className="flex items-center gap-4">
              <h2 className="text-2xl font-bold">
                {monthNames[currentDate.getMonth()]} {currentDate.getFullYear()}
              </h2>
              <Button variant="ghost" size="sm" onClick={goToToday}>
                Aujourd'hui
              </Button>
            </div>
            <Button variant="outline" onClick={goToNextMonth}>
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>

          {/* Légende */}
          <div className="flex items-center gap-6 mb-4 p-3 bg-gray-50 rounded">
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
            <span className="text-xs text-gray-500 ml-4">• Triangle gauche = Matin (8h-12h) • Triangle droit = Après-midi (13h-17h)</span>
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
                  {days.map((day, index) => {
                    const isToday = day.toISOString().split('T')[0] === today;
                    const isWeekend = day.getDay() === 0 || day.getDay() === 6;
                    return (
                      <th
                        key={index}
                        className={`border p-1 text-xs ${
                          isToday
                            ? 'bg-blue-100 font-bold'
                            : isWeekend
                            ? 'bg-gray-200'
                            : 'bg-gray-100'
                        }`}
                      >
                        <div className="text-center">
                          <div>{day.getDate()}</div>
                          <div className="text-[10px] text-gray-600">
                            {['Dim', 'Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam'][day.getDay()]}
                          </div>
                        </div>
                      </th>
                    );
                  })}
                </tr>
              </thead>
              <tbody>
                {equipments.length === 0 ? (
                  <tr>
                    <td colSpan={days.length + 1} className="text-center p-8 text-gray-500">
                      Aucun équipement enregistré
                    </td>
                  </tr>
                ) : (
                  equipments.map(equipment => (
                    <tr key={equipment.id}>
                      <td className="border p-2 font-medium sticky left-0 bg-white z-10">
                        <div>
                          <div className="font-semibold text-sm">{equipment.name || equipment.nom}</div>
                          {(equipment.category || equipment.categorie) && (
                            <div className="text-xs text-gray-500">{equipment.category || equipment.categorie}</div>
                          )}
                        </div>
                      </td>
                      {days.map((day, dayIndex) => {
                        const statusAM = getEquipmentStatusForHalfDay(equipment.id, day, true);
                        const statusPM = getEquipmentStatusForHalfDay(equipment.id, day, false);
                        const isToday = day.toISOString().split('T')[0] === today;
                        
                        return (
                          <td
                            key={dayIndex}
                            className={`border p-0 relative ${
                              isToday ? 'bg-blue-50' : ''
                            }`}
                            style={{ height: '50px', width: '40px' }}
                          >
                            <div className="relative w-full h-full">
                              {/* Triangle gauche (Matin) */}
                              <svg
                                className="absolute inset-0 w-full h-full"
                                viewBox="0 0 100 100"
                                preserveAspectRatio="none"
                              >
                                <polygon
                                  points="0,0 0,100 100,100"
                                  fill={getStatusColor(statusAM)}
                                  opacity="0.9"
                                />
                              </svg>
                              {/* Triangle droit (Après-midi) */}
                              <svg
                                className="absolute inset-0 w-full h-full"
                                viewBox="0 0 100 100"
                                preserveAspectRatio="none"
                              >
                                <polygon
                                  points="0,0 100,0 100,100"
                                  fill={getStatusColor(statusPM)}
                                  opacity="0.9"
                                />
                              </svg>
                            </div>
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
