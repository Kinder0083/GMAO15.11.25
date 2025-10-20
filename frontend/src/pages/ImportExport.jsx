import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Download, Upload, Database, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import { useToast } from '../hooks/use-toast';
import axios from 'axios';

const ImportExport = () => {
  const { toast } = useToast();
  const [selectedModule, setSelectedModule] = useState('all');
  const [exportFormat, setExportFormat] = useState('xlsx');
  const [importMode, setImportMode] = useState('add');
  const [importing, setImporting] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [importResult, setImportResult] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);

  const modules = [
    { value: 'all', label: 'Toutes les données' },
    { value: 'work-orders', label: 'Ordres de travail' },
    { value: 'equipments', label: 'Équipements' },
    { value: 'users', label: 'Utilisateurs (Équipes)' },
    { value: 'inventory', label: 'Inventaire' },
    { value: 'locations', label: 'Zones' },
    { value: 'vendors', label: 'Fournisseurs' },
    { value: 'purchase-history', label: 'Historique Achat' }
  ];

  const handleExport = async () => {
    try {
      setExporting(true);
      const backend_url = process.env.REACT_APP_BACKEND_URL;
      const token = localStorage.getItem('token');

      const response = await axios.get(
        `${backend_url}/api/export/${selectedModule}`,
        {
          params: { format: exportFormat },
          headers: { Authorization: `Bearer ${token}` },
          responseType: 'blob'
        }
      );

      // Créer un lien de téléchargement
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      const filename = selectedModule === 'all' 
        ? `export_all.${exportFormat}` 
        : `${selectedModule}.${exportFormat}`;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      toast({
        title: 'Succès',
        description: 'Export réussi'
      });
    } catch (error) {
      toast({
        title: 'Erreur',
        description: error.response?.data?.detail || 'Impossible d\'exporter les données',
        variant: 'destructive'
      });
    } finally {
      setExporting(false);
    }
  };

  const handleFileSelect = (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (selectedModule === 'all') {
      toast({
        title: 'Erreur',
        description: 'Veuillez sélectionner un module spécifique pour l\'import',
        variant: 'destructive'
      });
      event.target.value = '';
      return;
    }

    setSelectedFile(file);
    setImportResult(null); // Réinitialiser le résultat précédent
  };

  const handleImport = async () => {
    if (!selectedFile) return;

    try {
      setImporting(true);
      const backend_url = process.env.REACT_APP_BACKEND_URL;
      const token = localStorage.getItem('token');

      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await axios.post(
        `${backend_url}/api/import/${selectedModule}`,
        formData,
        {
          params: { mode: importMode },
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          }
        }
      );

      setImportResult(response.data);
      setSelectedFile(null); // Réinitialiser le fichier sélectionné

      toast({
        title: 'Import terminé',
        description: `${response.data.inserted} ajouté(s), ${response.data.updated} mis à jour, ${response.data.skipped} ignoré(s)`
      });
    } catch (error) {
      toast({
        title: 'Erreur',
        description: error.response?.data?.detail || 'Impossible d\'importer les données',
        variant: 'destructive'
      });
    } finally {
      setImporting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Import / Export</h1>
        <p className="text-gray-600 mt-1">Sauvegardez et restaurez vos données</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Export */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Download size={24} className="text-blue-600" />
              Exporter les données
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Module à exporter</Label>
              <Select value={selectedModule} onValueChange={setSelectedModule}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {modules.map(mod => (
                    <SelectItem key={mod.value} value={mod.value}>
                      {mod.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Format</Label>
              <Select value={exportFormat} onValueChange={setExportFormat}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="csv">CSV (un module seulement)</SelectItem>
                  <SelectItem value="xlsx">Excel (XLSX)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Button
              onClick={handleExport}
              disabled={exporting || (exportFormat === 'csv' && selectedModule === 'all')}
              className="w-full bg-blue-600 hover:bg-blue-700"
            >
              <Download size={20} className="mr-2" />
              {exporting ? 'Export en cours...' : 'Exporter'}
            </Button>

            {exportFormat === 'csv' && selectedModule === 'all' && (
              <p className="text-sm text-orange-600">
                Pour exporter toutes les données, utilisez le format Excel (XLSX)
              </p>
            )}
          </CardContent>
        </Card>

        {/* Import */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Upload size={24} className="text-green-600" />
              Importer les données
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Module à importer</Label>
              <Select value={selectedModule} onValueChange={setSelectedModule}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {modules.filter(m => m.value !== 'all').map(mod => (
                    <SelectItem key={mod.value} value={mod.value}>
                      {mod.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Mode d'import</Label>
              <Select value={importMode} onValueChange={setImportMode}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="add">Ajouter aux données existantes</SelectItem>
                  <SelectItem value="replace">Écraser les données existantes (par ID)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="import-file">Fichier CSV ou Excel</Label>
              <input
                id="import-file"
                type="file"
                accept=".csv,.xlsx,.xls"
                onChange={handleFileSelect}
                disabled={importing || selectedModule === 'all'}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-green-50 file:text-green-700 hover:file:bg-green-100 cursor-pointer"
              />
              {selectedFile && (
                <p className="text-sm text-green-600">
                  Fichier sélectionné : {selectedFile.name}
                </p>
              )}
            </div>

            <Button
              onClick={handleImport}
              disabled={importing || !selectedFile || selectedModule === 'all'}
              className="w-full bg-green-600 hover:bg-green-700"
            >
              <Upload size={20} className="mr-2" />
              {importing ? 'Import en cours...' : 'Importer'}
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Résultat d'import */}
      {importResult && (
        <Card>
          <CardHeader>
            <CardTitle>Résultat de l'import</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="flex items-center gap-3 p-4 bg-blue-50 rounded-lg">
                <Database size={24} className="text-blue-600" />
                <div>
                  <p className="text-sm text-gray-600">Total</p>
                  <p className="text-2xl font-bold text-blue-600">{importResult.total}</p>
                </div>
              </div>

              <div className="flex items-center gap-3 p-4 bg-green-50 rounded-lg">
                <CheckCircle size={24} className="text-green-600" />
                <div>
                  <p className="text-sm text-gray-600">Ajoutés</p>
                  <p className="text-2xl font-bold text-green-600">{importResult.inserted}</p>
                </div>
              </div>

              <div className="flex items-center gap-3 p-4 bg-orange-50 rounded-lg">
                <AlertCircle size={24} className="text-orange-600" />
                <div>
                  <p className="text-sm text-gray-600">Mis à jour</p>
                  <p className="text-2xl font-bold text-orange-600">{importResult.updated}</p>
                </div>
              </div>

              <div className="flex items-center gap-3 p-4 bg-red-50 rounded-lg">
                <XCircle size={24} className="text-red-600" />
                <div>
                  <p className="text-sm text-gray-600">Ignorés</p>
                  <p className="text-2xl font-bold text-red-600">{importResult.skipped}</p>
                </div>
              </div>
            </div>

            {importResult.errors && importResult.errors.length > 0 && (
              <div className="mt-4">
                <h4 className="font-semibold text-red-600 mb-2">Erreurs :</h4>
                <ul className="list-disc list-inside space-y-1 text-sm text-gray-600">
                  {importResult.errors.slice(0, 10).map((error, index) => (
                    <li key={index}>{error}</li>
                  ))}
                  {importResult.errors.length > 10 && (
                    <li className="text-gray-500">... et {importResult.errors.length - 10} autres erreurs</li>
                  )}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Guide */}
      <Card>
        <CardHeader>
          <CardTitle>Guide d'utilisation</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm text-gray-600">
          <div>
            <h4 className="font-semibold text-gray-900 mb-1">Export :</h4>
            <ul className="list-disc list-inside space-y-1">
              <li>Sélectionnez un module ou "Toutes les données"</li>
              <li>Choisissez le format (CSV pour un module, XLSX pour plusieurs)</li>
              <li>Cliquez sur "Exporter" pour télécharger le fichier</li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold text-gray-900 mb-1">Import :</h4>
            <ul className="list-disc list-inside space-y-1">
              <li>Sélectionnez le module à importer</li>
              <li>Choisissez le mode : "Ajouter" (nouvelles entrées) ou "Écraser" (mise à jour par ID)</li>
              <li>Sélectionnez votre fichier CSV ou Excel</li>
              <li>L'import démarre automatiquement</li>
            </ul>
          </div>
          <div className="bg-yellow-50 p-3 rounded-lg">
            <p className="font-semibold text-yellow-800">⚠️ Important :</p>
            <p className="text-yellow-700">
              Le mode "Écraser" remplace les données existantes. Faites toujours un export avant un import en mode "Écraser".
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ImportExport;
