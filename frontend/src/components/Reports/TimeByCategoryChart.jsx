import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { BarChart3 } from 'lucide-react';
import { reportsAPI } from '../../services/api';
import { useToast } from '../../hooks/use-toast';

const TimeByCategoryChart = () => {
  const { toast } = useToast();
  const [selectedMonth, setSelectedMonth] = useState('');
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(false);

  // Générer les options de mois (24 mois en arrière et 12 mois en avant)
  const generateMonthOptions = () => {
    const months = [];
    const now = new Date();
    
    // 24 mois en arrière
    for (let i = 24; i >= 0; i--) {
      const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
      months.push({
        value: `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`,
        label: date.toLocaleDateString('fr-FR', { year: 'numeric', month: 'long' })
      });
    }
    
    // 12 mois en avant
    for (let i = 1; i <= 12; i++) {
      const date = new Date(now.getFullYear(), now.getMonth() + i, 1);
      months.push({
        value: `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`,
        label: date.toLocaleDateString('fr-FR', { year: 'numeric', month: 'long' })
      });
    }
    
    return months;
  };

  const monthOptions = generateMonthOptions();

  // Initialiser avec le mois actuel
  useEffect(() => {
    const now = new Date();
    const currentMonth = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
    setSelectedMonth(currentMonth);
  }, []);

  // Charger les données quand le mois change
  useEffect(() => {
    if (selectedMonth) {
      loadChartData();
    }
  }, [selectedMonth]);

  const loadChartData = async () => {
    try {
      setLoading(true);
      const response = await reportsAPI.getTimeByCategory(selectedMonth);
      setChartData(response.data);
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

  const categoryColors = {
    CHANGEMENT_FORMAT: '#3b82f6',
    TRAVAUX_PREVENTIFS: '#10b981',
    TRAVAUX_CURATIF: '#ef4444',
    TRAVAUX_DIVERS: '#f59e0b',
    FORMATION: '#8b5cf6',
    REGLAGE: '#06b6d4'
  };

  const categoryLabels = {
    CHANGEMENT_FORMAT: 'Changement de Format',
    TRAVAUX_PREVENTIFS: 'Travaux Préventifs',
    TRAVAUX_CURATIF: 'Travaux Curatif',
    TRAVAUX_DIVERS: 'Travaux Divers',
    FORMATION: 'Formation',
    REGLAGE: 'Réglage'
  };

  const formatMonthLabel = (monthStr) => {
    const [year, month] = monthStr.split('-');
    const date = new Date(parseInt(year), parseInt(month) - 1, 1);
    return date.toLocaleDateString('fr-FR', { month: 'short', year: '2-digit' });
  };

  const formatTime = (hours) => {
    if (!hours || hours === 0) return '0h';
    const h = Math.floor(hours);
    const m = Math.round((hours - h) * 60);
    return m > 0 ? `${h}h${m}m` : `${h}h`;
  };

  // Calculer la hauteur maximale pour l'échelle
  const getMaxValue = () => {
    if (!chartData || !chartData.months) return 100;
    let max = 0;
    chartData.months.forEach(month => {
      const total = Object.values(month.categories).reduce((sum, val) => sum + val, 0);
      if (total > max) max = total;
    });
    return Math.ceil(max * 1.1); // 10% de marge
  };

  const maxValue = getMaxValue();

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Evolution horaire des maintenances
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-64">
            <p className="text-gray-500">Chargement...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Evolution horaire des maintenances
          </CardTitle>
          <div className="w-64">
            <Select value={selectedMonth} onValueChange={setSelectedMonth}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {monthOptions.map(option => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
        <p className="text-sm text-gray-500 mt-2">
          Temps total passé par catégorie sur 12 mois glissants
        </p>
      </CardHeader>
      <CardContent>
        {/* Légende */}
        <div className="flex flex-wrap gap-4 mb-6 justify-center">
          {Object.entries(categoryLabels).map(([key, label]) => (
            <div key={key} className="flex items-center gap-2">
              <div 
                className="w-4 h-4 rounded" 
                style={{ backgroundColor: categoryColors[key] }}
              />
              <span className="text-sm text-gray-700">{label}</span>
            </div>
          ))}
        </div>

        {/* Graphique */}
        <div className="relative h-80 bg-gray-50 rounded-lg p-4">
          {chartData && chartData.months && (
            <div className="flex items-end justify-around h-full gap-2">
              {chartData.months.map((monthData, index) => {
                const totalTime = Object.values(monthData.categories).reduce((sum, val) => sum + val, 0);
                
                return (
                  <div key={index} className="flex flex-col items-center flex-1 h-full">
                    {/* Barres empilées */}
                    <div className="flex flex-col-reverse items-center justify-end flex-1 w-full mb-2">
                      {Object.entries(monthData.categories).map(([category, time]) => {
                        if (time === 0) return null;
                        const heightPercent = maxValue > 0 ? (time / maxValue) * 100 : 0;
                        
                        return (
                          <div
                            key={category}
                            className="w-full relative group cursor-pointer hover:opacity-80 transition-opacity"
                            style={{
                              height: `${heightPercent}%`,
                              backgroundColor: categoryColors[category]
                            }}
                          >
                            {/* Tooltip */}
                            <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 hidden group-hover:block z-10">
                              <div className="bg-gray-900 text-white text-xs rounded py-1 px-2 whitespace-nowrap">
                                {categoryLabels[category]}: {formatTime(time)}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                    
                    {/* Label du mois */}
                    <div className="text-xs text-gray-600 text-center mt-1 transform -rotate-45 origin-top-left">
                      {formatMonthLabel(monthData.month)}
                    </div>
                    
                    {/* Total */}
                    {totalTime > 0 && (
                      <div className="text-xs font-semibold text-gray-700 mt-6">
                        {formatTime(totalTime)}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {/* Échelle Y */}
          <div className="absolute left-0 top-0 h-full flex flex-col justify-between py-4 pr-2 text-xs text-gray-500">
            <span>{formatTime(maxValue)}</span>
            <span>{formatTime(maxValue * 0.75)}</span>
            <span>{formatTime(maxValue * 0.5)}</span>
            <span>{formatTime(maxValue * 0.25)}</span>
            <span>0h</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default TimeByCategoryChart;