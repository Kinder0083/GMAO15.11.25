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
  const [selectedMonth, setSelectedMonth] = useState(null); // Pour vue mensuelle détaillée

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
      const startDate = new Date(year, 0, 1).toISOString().split('T')[0];
      const endDate = new Date(year, 11, 31).toISOString().split('T')[0];
      
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

  // Obtenir tous les jours d'un mois spécifique
  const getDaysInMonth = (year, month) => {
    const days = [];
    const lastDay = new Date(year, month + 1, 0).getDate();
    for (let d = 1; d <= lastDay; d++) {
      days.push(new Date(year, month, d));
    }
    return days;
  };

  // Obtenir le statut de l'équipement pour une demi-journée spécifique
  const getEquipmentStatusForHalfDay = (equipmentId, date, isAM) => {
    const dateStr = date.toISOString().split('T')[0];
    
    const entry = planningEntries.find(e => {
      if (e.equipement_id !== equipmentId) return false;
      
      const entryStart = new Date(e.date_debut);
      const entryEnd = new Date(e.date_fin);
      const currentDate = new Date(dateStr);
      
      if (currentDate < entryStart || currentDate > entryEnd) return false;
      
      // Vérifier la demi-journée pour le premier jour
      if (currentDate.toISOString().split('T')[0] === e.date_debut) {
        if (e.periode_debut === 'APRES_MIDI' && isAM) return false;
      }
      
      // Vérifier la demi-journée pour le dernier jour
      if (currentDate.toISOString().split('T')[0] === e.date_fin) {
        if (e.periode_fin === 'MATIN' && !isAM) return false;
      }
      
      return true;
    });

    if (entry) {
      return entry.statut || 'EN_MAINTENANCE';
    }

    const equipment = equipments.find(e => e.id === equipmentId);
    return equipment?.status || equipment?.statut || 'OPERATIONNEL';
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'OPERATIONNEL':
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

  const goToPreviousYear = () => {
    setCurrentDate(new Date(currentDate.getFullYear() - 1, 0, 1));
  };

  const goToNextYear = () => {
    setCurrentDate(new Date(currentDate.getFullYear() + 1, 0, 1));
  };

  const goToCurrentYear = () => {
    setCurrentDate(new Date());
  };

  const monthNames = [
    'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
    'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
  ];

  const today = new Date().toISOString().split('T')[0];
  const year = currentDate.getFullYear();

  // Calculer les statistiques annuelles
  const calculateAnnualStats = () => {
    let totalOperational = 0;
    let totalMaintenance = 0;
    let totalOutOfService = 0;
    
    // Pour chaque équipement
    equipments.forEach(equipment => {
      // Pour chaque jour de l'année
      for (let month = 0; month < 12; month++) {
        const daysInMonth = new Date(year, month + 1, 0).getDate();
        for (let day = 1; day <= daysInMonth; day++) {
          const date = new Date(year, month, day);
          
          // Vérifier les deux demi-journées
          const statusAM = getEquipmentStatusForHalfDay(equipment.id, date, true);
          const statusPM = getEquipmentStatusForHalfDay(equipment.id, date, false);
          
          // Compter les demi-journées
          [statusAM, statusPM].forEach(status => {
            if (status === 'OPERATIONNEL' || status === 'OPERATIONAL') {
              totalOperational += 0.5;
            } else if (status === 'EN_MAINTENANCE') {
              totalMaintenance += 0.5;
            } else if (status === 'HORS_SERVICE') {
              totalOutOfService += 0.5;
            }
          });
        }
      }
    });
    
    return {
      operational: Math.round(totalOperational),
      maintenance: Math.round(totalMaintenance),
      outOfService: Math.round(totalOutOfService),
      total: Math.round(totalOperational + totalMaintenance + totalOutOfService)
    };
  };

  const annualStats = calculateAnnualStats();

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
          {/* Navigation année */}
          <div className="flex items-center justify-between mb-6">
            <Button variant="outline" onClick={goToPreviousYear}>
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <div className="flex items-center gap-4">
              <h2 className="text-2xl font-bold">
                Année {year}
              </h2>
              <Button variant="ghost" size="sm" onClick={goToCurrentYear}>
                Année actuelle
              </Button>
            </div>
            <Button variant="outline" onClick={goToNextYear}>
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

          {/* Vue annuelle - Affichage par mois */}
          <div className="space-y-8">
            {monthNames.map((monthName, monthIndex) => {
              const days = getDaysInMonth(year, monthIndex);
              const currentMonth = new Date().getMonth();
              const currentYear = new Date().getFullYear();
              const isCurrentMonth = monthIndex === currentMonth && year === currentYear;

              return (
                <div key={monthIndex} className="border rounded-lg p-4">
                  <h3 className={`text-lg font-semibold mb-3 ${isCurrentMonth ? 'text-blue-600' : ''}`}>
                    {monthName} {year}
                  </h3>
                  
                  <div className="overflow-x-auto">
                    <table className="w-full border-collapse">
                      <thead>
                        <tr>
                          <th className="border p-2 bg-gray-100 sticky left-0 z-10 min-w-[150px]">
                            <div className="flex items-center gap-2">
                              <Wrench className="h-4 w-4" />
                              Équipement
                            </div>
                          </th>
                          {days.map((day, dayIndex) => {
                            const isToday = day.toISOString().split('T')[0] === today;
                            const isWeekend = day.getDay() === 0 || day.getDay() === 6;
                            return (
                              <th
                                key={dayIndex}
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
                                    {['D', 'L', 'M', 'M', 'J', 'V', 'S'][day.getDay()]}
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
                            <td colSpan={days.length + 1} className="text-center p-4 text-gray-500 text-sm">
                              Aucun équipement
                            </td>
                          </tr>
                        ) : (
                          equipments.map(equipment => (
                            <tr key={equipment.id}>
                              <td className="border p-2 text-sm font-medium sticky left-0 bg-white z-10">
                                <div className="font-semibold">{equipment.name || equipment.nom}</div>
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
                                    style={{ height: '40px', width: '35px' }}
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
                </div>
              );
            })}
          </div>

          {/* Statistiques */}
          <div className="grid grid-cols-3 gap-4 mt-6">
            <Card>
              <CardContent className="pt-6">
                <div className="text-2xl font-bold">
                  {equipments.filter(e => (e.status || e.statut) === 'OPERATIONNEL' || (e.status || e.statut) === 'OPERATIONAL').length}
                </div>
                <div className="text-sm text-gray-600">Équipements opérationnels</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-2xl font-bold">
                  {equipments.filter(e => (e.status || e.statut) === 'EN_MAINTENANCE').length}
                </div>
                <div className="text-sm text-gray-600">En maintenance</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-2xl font-bold">
                  {equipments.filter(e => (e.status || e.statut) === 'HORS_SERVICE').length}
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
