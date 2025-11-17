import React, { useState, useMemo } from 'react';
import {
  Box,
  Paper,
  Typography,
  IconButton,
  Chip,
  Tooltip,
  CircularProgress,
  Card,
  CardContent
} from '@mui/material';
import { ChevronLeft, ChevronRight, CheckCircle } from '@mui/icons-material';
import CompleteSurveillanceDialog from './CompleteSurveillanceDialog';

const MONTHS = [
  'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
  'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
];

const getStatusColor = (status) => {
  switch (status) {
    case 'REALISE': return '#4caf50';
    case 'PLANIFIE': return '#2196f3';
    case 'PLANIFIER': return '#ff9800';
    default: return '#9e9e9e';
  }
};

function CalendarView({ items, loading, onEdit, onRefresh }) {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [completeDialog, setCompleteDialog] = useState({ open: false, item: null });

  const currentMonth = currentDate.getMonth();
  const currentYear = currentDate.getFullYear();

  const handlePreviousMonth = () => {
    setCurrentDate(new Date(currentYear, currentMonth - 1, 1));
  };

  const handleNextMonth = () => {
    setCurrentDate(new Date(currentYear, currentMonth + 1, 1));
  };

  const handleComplete = (item) => {
    setCompleteDialog({ open: true, item });
  };

  const handleCompleteClose = (shouldRefresh) => {
    setCompleteDialog({ open: false, item: null });
    if (shouldRefresh && onRefresh) {
      onRefresh();
    }
  };

  // Grouper les items par date de prochain contrôle
  const itemsByDate = useMemo(() => {
    const grouped = {};
    items.forEach((item) => {
      if (item.prochain_controle) {
        const date = new Date(item.prochain_controle);
        if (date.getMonth() === currentMonth && date.getFullYear() === currentYear) {
          const dateKey = date.toISOString().split('T')[0];
          if (!grouped[dateKey]) {
            grouped[dateKey] = [];
          }
          grouped[dateKey].push(item);
        }
      }
    });
    return grouped;
  }, [items, currentMonth, currentYear]);

  // Calculer le calendrier du mois
  const getDaysInMonth = () => {
    const firstDay = new Date(currentYear, currentMonth, 1);
    const lastDay = new Date(currentYear, currentMonth + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startDay = firstDay.getDay();

    const days = [];
    // Ajouter les jours vides avant le 1er du mois
    for (let i = 0; i < (startDay === 0 ? 6 : startDay - 1); i++) {
      days.push(null);
    }
    // Ajouter les jours du mois
    for (let day = 1; day <= daysInMonth; day++) {
      days.push(day);
    }
    return days;
  };

  const days = getDaysInMonth();

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <>
      <Paper sx={{ p: 2 }}>
        {/* En-tête du calendrier */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <IconButton onClick={handlePreviousMonth}>
            <ChevronLeft />
          </IconButton>
          <Typography variant="h5" fontWeight="bold">
            {MONTHS[currentMonth]} {currentYear}
          </Typography>
          <IconButton onClick={handleNextMonth}>
            <ChevronRight />
          </IconButton>
        </Box>

        {/* Jours de la semaine */}
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 1, mb: 1 }}>
          {['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'].map((day) => (
            <Box key={day} sx={{ textAlign: 'center', fontWeight: 'bold', py: 1 }}>
              {day}
            </Box>
          ))}
        </Box>

        {/* Grille des jours */}
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 1 }}>
          {days.map((day, index) => {
            if (!day) {
              return <Box key={`empty-${index}`} sx={{ minHeight: 100 }} />;
            }

            const dateKey = `${currentYear}-${String(currentMonth + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
            const dayItems = itemsByDate[dateKey] || [];
            const isToday = 
              day === new Date().getDate() &&
              currentMonth === new Date().getMonth() &&
              currentYear === new Date().getFullYear();

            return (
              <Card
                key={day}
                sx={{
                  minHeight: 100,
                  backgroundColor: isToday ? '#e3f2fd' : 'white',
                  border: isToday ? '2px solid #2196f3' : '1px solid #e0e0e0'
                }}
              >
                <CardContent sx={{ p: 1, '&:last-child': { pb: 1 } }}>
                  <Typography variant="body2" fontWeight="bold" gutterBottom>
                    {day}
                  </Typography>
                  {dayItems.map((item) => (
                    <Tooltip
                      key={item.id}
                      title={
                        <Box>
                          <Typography variant="caption" display="block">
                            <strong>{item.classe_type}</strong>
                          </Typography>
                          <Typography variant="caption" display="block">
                            {item.batiment}
                          </Typography>
                          <Typography variant="caption" display="block">
                            {item.responsable} - {item.executant}
                          </Typography>
                        </Box>
                      }
                    >
                      <Box
                        sx={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          p: 0.5,
                          mb: 0.5,
                          backgroundColor: getStatusColor(item.status),
                          color: 'white',
                          borderRadius: 1,
                          cursor: 'pointer',
                          fontSize: '0.7rem',
                          '&:hover': {
                            opacity: 0.8
                          }
                        }}
                        onClick={() => onEdit(item)}
                      >
                        <Typography variant="caption" noWrap sx={{ flex: 1 }}>
                          {item.classe_type.substring(0, 15)}...
                        </Typography>
                        {item.status !== 'REALISE' && (
                          <IconButton
                            size="small"
                            sx={{ p: 0, color: 'white' }}
                            onClick={(e) => {
                              e.stopPropagation();
                              handleComplete(item);
                            }}
                          >
                            <CheckCircle sx={{ fontSize: 14 }} />
                          </IconButton>
                        )}
                      </Box>
                    </Tooltip>
                  ))}
                </CardContent>
              </Card>
            );
          })}
        </Box>

        {/* Légende */}
        <Box sx={{ display: 'flex', gap: 2, mt: 3, justifyContent: 'center' }}>
          <Chip label="À planifier" size="small" sx={{ backgroundColor: '#ff9800', color: 'white' }} />
          <Chip label="Planifié" size="small" sx={{ backgroundColor: '#2196f3', color: 'white' }} />
          <Chip label="Réalisé" size="small" sx={{ backgroundColor: '#4caf50', color: 'white' }} />
        </Box>
      </Paper>

      {completeDialog.open && (
        <CompleteSurveillanceDialog
          open={completeDialog.open}
          item={completeDialog.item}
          onClose={handleCompleteClose}
        />
      )}
    </>
  );
}

export default CalendarView;
