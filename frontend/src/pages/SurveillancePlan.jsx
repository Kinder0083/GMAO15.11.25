import React, { useState, useEffect } from 'react';
import { Box, Container, Typography, Tabs, Tab, Button, TextField, MenuItem, Chip, Alert } from '@mui/material';
import { Add as AddIcon, FileDownload, FileUpload, Notifications } from '@mui/icons-material';
import { surveillanceAPI } from '../services/api';
import ListView from '../components/Surveillance/ListView';
import GridView from '../components/Surveillance/GridView';
import CalendarView from '../components/Surveillance/CalendarView';
import SurveillanceItemForm from '../components/Surveillance/SurveillanceItemForm';
import { toast } from 'react-toastify';

function SurveillancePlan() {
  const [activeTab, setActiveTab] = useState(0);
  const [items, setItems] = useState([]);
  const [filteredItems, setFilteredItems] = useState([]);
  const [stats, setStats] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [openForm, setOpenForm] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  
  // Filtres
  const [filters, setFilters] = useState({
    category: '',
    responsable: '',
    batiment: '',
    status: ''
  });

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [items, filters]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [itemsData, statsData, alertsData] = await Promise.all([
        surveillanceAPI.getItems(),
        surveillanceAPI.getStats(),
        surveillanceAPI.getAlerts()
      ]);
      setItems(itemsData);
      setStats(statsData);
      setAlerts(alertsData.alerts || []);
    } catch (error) {
      console.error('Erreur chargement données:', error);
      toast.error('Erreur lors du chargement des données');
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...items];
    
    if (filters.category) {
      filtered = filtered.filter(item => item.category === filters.category);
    }
    if (filters.responsable) {
      filtered = filtered.filter(item => item.responsable === filters.responsable);
    }
    if (filters.batiment) {
      filtered = filtered.filter(item => item.batiment === filters.batiment);
    }
    if (filters.status) {
      filtered = filtered.filter(item => item.status === filters.status);
    }
    
    setFilteredItems(filtered);
  };

  const handleFilterChange = (field, value) => {
    setFilters(prev => ({ ...prev, [field]: value }));
  };

  const handleCreate = () => {
    setSelectedItem(null);
    setOpenForm(true);
  };

  const handleEdit = (item) => {
    setSelectedItem(item);
    setOpenForm(true);
  };

  const handleDelete = async (itemId) => {
    if (window.confirm('Êtes-vous sûr de vouloir supprimer cet item ?')) {
      try {
        await surveillanceAPI.deleteItem(itemId);
        toast.success('Item supprimé avec succès');
        loadData();
      } catch (error) {
        toast.error('Erreur lors de la suppression');
      }
    }
  };

  const handleFormClose = (shouldRefresh) => {
    setOpenForm(false);
    setSelectedItem(null);
    if (shouldRefresh) {
      loadData();
    }
  };

  const handleExportTemplate = async () => {
    try {
      const response = await fetch('/api/surveillance/export/template', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'template_plan_surveillance.csv';
      a.click();
      toast.success('Template téléchargé');
    } catch (error) {
      toast.error('Erreur lors du téléchargement');
    }
  };

  const handleImport = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const result = await surveillanceAPI.importData(formData);
      toast.success(`Import réussi: ${result.imported_count} items importés`);
      if (result.errors && result.errors.length > 0) {
        toast.warning(`${result.errors.length} erreurs d'import`);
      }
      loadData();
    } catch (error) {
      toast.error('Erreur lors de l\'import');
    }
  };

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      {/* En-tête */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" fontWeight="bold">
          Plan de Surveillance
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<FileDownload />}
            onClick={handleExportTemplate}
          >
            Template
          </Button>
          <Button
            variant="outlined"
            component="label"
            startIcon={<FileUpload />}
          >
            Importer
            <input type="file" hidden accept=".csv,.xlsx,.xls" onChange={handleImport} />
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreate}
          >
            Nouveau Contrôle
          </Button>
        </Box>
      </Box>

      {/* Alertes */}
      {alerts.length > 0 && (
        <Alert severity="warning" icon={<Notifications />} sx={{ mb: 2 }}>
          <strong>{alerts.length} contrôle(s) à échéance proche</strong>
          {alerts.slice(0, 3).map(alert => (
            <div key={alert.id}>
              • {alert.classe_type} - {alert.batiment} (J-{alert.days_until})
            </div>
          ))}
        </Alert>
      )}

      {/* Statistiques */}
      {stats && (
        <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
          <Chip label={`Total: ${stats.global.total}`} color="primary" />
          <Chip label={`Réalisés: ${stats.global.realises}`} color="success" />
          <Chip label={`Planifiés: ${stats.global.planifies}`} color="info" />
          <Chip label={`À planifier: ${stats.global.a_planifier}`} color="warning" />
          <Chip label={`Taux: ${stats.global.pourcentage_realisation}%`} color="secondary" />
        </Box>
      )}

      {/* Filtres */}
      <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
        <TextField
          select
          label="Catégorie"
          value={filters.category}
          onChange={(e) => handleFilterChange('category', e.target.value)}
          sx={{ minWidth: 200 }}
          size="small"
        >
          <MenuItem value="">Toutes</MenuItem>
          <MenuItem value="MMRI">MMRI</MenuItem>
          <MenuItem value="INCENDIE">Incendie</MenuItem>
          <MenuItem value="SECURITE_ENVIRONNEMENT">Sécurité/Environnement</MenuItem>
          <MenuItem value="ELECTRIQUE">Électrique</MenuItem>
          <MenuItem value="MANUTENTION">Manutention</MenuItem>
          <MenuItem value="EXTRACTION">Extraction</MenuItem>
          <MenuItem value="AUTRE">Autre</MenuItem>
        </TextField>

        <TextField
          select
          label="Responsable"
          value={filters.responsable}
          onChange={(e) => handleFilterChange('responsable', e.target.value)}
          sx={{ minWidth: 150 }}
          size="small"
        >
          <MenuItem value="">Tous</MenuItem>
          <MenuItem value="MAINT">MAINT</MenuItem>
          <MenuItem value="PROD">PROD</MenuItem>
          <MenuItem value="QHSE">QHSE</MenuItem>
          <MenuItem value="EXTERNE">EXTERNE</MenuItem>
        </TextField>

        <TextField
          select
          label="Statut"
          value={filters.status}
          onChange={(e) => handleFilterChange('status', e.target.value)}
          sx={{ minWidth: 150 }}
          size="small"
        >
          <MenuItem value="">Tous</MenuItem>
          <MenuItem value="PLANIFIER">À planifier</MenuItem>
          <MenuItem value="PLANIFIE">Planifié</MenuItem>
          <MenuItem value="REALISE">Réalisé</MenuItem>
        </TextField>
      </Box>

      {/* Onglets de vue */}
      <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)} sx={{ mb: 2 }}>
        <Tab label="Liste" />
        <Tab label="Grille par Catégorie" />
        <Tab label="Calendrier" />
      </Tabs>

      {/* Contenu des vues */}
      {activeTab === 0 && (
        <ListView
          items={filteredItems}
          loading={loading}
          onEdit={handleEdit}
          onDelete={handleDelete}
          onRefresh={loadData}
        />
      )}
      {activeTab === 1 && (
        <GridView
          items={filteredItems}
          loading={loading}
          onEdit={handleEdit}
          onDelete={handleDelete}
          onRefresh={loadData}
        />
      )}
      {activeTab === 2 && (
        <CalendarView
          items={filteredItems}
          loading={loading}
          onEdit={handleEdit}
          onRefresh={loadData}
        />
      )}

      {/* Formulaire de création/édition */}
      {openForm && (
        <SurveillanceItemForm
          open={openForm}
          item={selectedItem}
          onClose={handleFormClose}
        />
      )}
    </Container>
  );
}

export default SurveillancePlan;
