import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Plus, FolderOpen, Edit, Trash2, FileText, Search, Grid3x3, List, ChevronDown, ChevronRight, Eye, Download, FileSpreadsheet, FileImage, FileVideo } from 'lucide-react';
import { documentationsAPI } from '../services/api';
import { useToast } from '../hooks/use-toast';
import { useConfirmDialog } from '../components/ui/confirm-dialog';
import { formatErrorMessage } from '../utils/errorFormatter';
import { getBackendURL } from '../utils/config';

const POLE_COLORS = {
  MAINTENANCE: '#f97316',
  PRODUCTION: '#3b82f6',
  QHSE: '#22c55e',
  LOGISTIQUE: '#a855f7',
  LABO: '#06b6d4',
  ADV: '#ec4899',
  INDUS: '#f59e0b',
  DIRECTION: '#ef4444',
  RH: '#8b5cf6',
  AUTRE: '#6b7280'
};

const POLE_ICONS = {
  MAINTENANCE: '🔧',
  PRODUCTION: '🏭',
  QHSE: '🛡️',
  LOGISTIQUE: '📦',
  LABO: '🧪',
  ADV: '💼',
  INDUS: '⚙️',
  DIRECTION: '👔',
  RH: '👥',
  AUTRE: '📁'
};

function Documentations() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { confirm, ConfirmDialog } = useConfirmDialog();
  const [poles, setPoles] = useState([]);
  const [filteredPoles, setFilteredPoles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [openForm, setOpenForm] = useState(false);
  const [selectedPole, setSelectedPole] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [viewMode, setViewMode] = useState('cards'); // 'cards' ou 'list'
  const [expandedPoles, setExpandedPoles] = useState(new Set());
  const [previewDocument, setPreviewDocument] = useState(null);
  const [openPreview, setOpenPreview] = useState(false);

  const [formData, setFormData] = useState({
    nom: '',
    pole: 'AUTRE',
    description: '',
    responsable: '',
    couleur: '#3b82f6',
    icon: 'Folder'
  });

  useEffect(() => {
    loadPoles();
  }, []);

  useEffect(() => {
    if (searchTerm) {
      const filtered = poles.filter(pole =>
        pole.nom.toLowerCase().includes(searchTerm.toLowerCase()) ||
        pole.description?.toLowerCase().includes(searchTerm.toLowerCase())
      );
      setFilteredPoles(filtered);
    } else {
      setFilteredPoles(poles);
    }
  }, [searchTerm, poles]);

  const loadPoles = async () => {
    try {
      setLoading(true);
      const data = await documentationsAPI.getPoles();
      setPoles(data);
      setFilteredPoles(data);
    } catch (error) {
      console.error('Erreur chargement pôles:', error);
      toast({
        title: 'Erreur',
        description: formatErrorMessage(error, 'Erreur lors du chargement'),
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setSelectedPole(null);
    setFormData({
      nom: '',
      pole: 'AUTRE',
      description: '',
      responsable: '',
      couleur: '#3b82f6',
      icon: 'Folder'
    });
    setOpenForm(true);
  };

  const handleEdit = (pole) => {
    setSelectedPole(pole);
    setFormData({
      nom: pole.nom || '',
      pole: pole.pole || 'AUTRE',
      description: pole.description || '',
      responsable: pole.responsable || '',
      couleur: pole.couleur || '#3b82f6',
      icon: pole.icon || 'Folder'
    });
    setOpenForm(true);
  };

  const handleDelete = (poleId) => {
    confirm({
      title: 'Supprimer le pôle',
      description: 'Êtes-vous sûr de vouloir supprimer ce pôle de service ? Cette action est irréversible.',
      confirmText: 'Supprimer',
      cancelText: 'Annuler',
      variant: 'destructive',
      onConfirm: async () => {
        try {
          await documentationsAPI.deletePole(poleId);
          toast({ title: 'Succès', description: 'Pôle supprimé' });
          loadPoles();
        } catch (error) {
          toast({
            title: 'Erreur',
            description: formatErrorMessage(error, 'Erreur lors de la suppression'),
            variant: 'destructive'
          });
        }
      }
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      // Mettre à jour la couleur selon le pôle sélectionné
      const poleData = {
        ...formData,
        couleur: POLE_COLORS[formData.pole] || formData.couleur
      };

      if (selectedPole) {
        await documentationsAPI.updatePole(selectedPole.id, poleData);
        toast({ title: 'Succès', description: 'Pôle mis à jour' });
      } else {
        await documentationsAPI.createPole(poleData);
        toast({ title: 'Succès', description: 'Pôle créé' });
      }
      setOpenForm(false);
      loadPoles();
    } catch (error) {
      toast({
        title: 'Erreur',
        description: formatErrorMessage(error, 'Erreur lors de l\'enregistrement'),
        variant: 'destructive'
      });
    }
  };

  const handlePoleClick = (poleId) => {
    navigate(`/documentations/${poleId}`);
  };

  const togglePoleExpansion = (poleId) => {
    const newExpanded = new Set(expandedPoles);
    if (newExpanded.has(poleId)) {
      newExpanded.delete(poleId);
    } else {
      newExpanded.add(poleId);
    }
    setExpandedPoles(newExpanded);
  };

  const handleDocumentPreview = async (document) => {
    setPreviewDocument(document);
    setOpenPreview(true);
  };

  const getFileIcon = (type) => {
    if (type?.includes('pdf') || type?.includes('word') || type?.includes('document')) return FileText;
    if (type?.includes('sheet') || type?.includes('excel')) return FileSpreadsheet;
    if (type?.includes('image')) return FileImage;
    if (type?.includes('video')) return FileVideo;
    return FileText;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p>Chargement...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Documentations</h1>
          <p className="text-gray-500">Gestion des pôles de service et documents</p>
        </div>
        <Button onClick={handleCreate}>
          <Plus className="mr-2 h-4 w-4" />
          Nouveau Pôle
        </Button>
      </div>

      {/* Search & View Toggle */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-4 items-center">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Rechercher un pôle..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="flex gap-2">
              <Button
                variant={viewMode === 'cards' ? 'default' : 'outline'}
                size="icon"
                onClick={() => setViewMode('cards')}
                title="Vue en cartes"
              >
                <Grid3x3 className="h-4 w-4" />
              </Button>
              <Button
                variant={viewMode === 'list' ? 'default' : 'outline'}
                size="icon"
                onClick={() => setViewMode('list')}
                title="Vue en liste"
              >
                <List className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Pôles Display */}
      {viewMode === 'cards' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredPoles.length === 0 ? (
          <div className="col-span-full text-center py-12">
            <FolderOpen className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <p className="text-gray-500">Aucun pôle de service trouvé</p>
            <Button onClick={handleCreate} className="mt-4">
              Créer le premier pôle
            </Button>
          </div>
        ) : (
          filteredPoles.map((pole) => (
            <Card
              key={pole.id}
              className="hover:shadow-lg transition-shadow cursor-pointer group"
              style={{ borderLeftWidth: '4px', borderLeftColor: pole.couleur || POLE_COLORS[pole.pole] }}
            >
              <CardHeader
                className="pb-3"
                onClick={() => handlePoleClick(pole.id)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div
                      className="w-12 h-12 rounded-lg flex items-center justify-center text-2xl"
                      style={{ backgroundColor: `${pole.couleur || POLE_COLORS[pole.pole]}20` }}
                    >
                      {POLE_ICONS[pole.pole] || '📁'}
                    </div>
                    <div>
                      <CardTitle className="text-lg">{pole.nom}</CardTitle>
                      <p className="text-sm text-gray-500">{pole.pole}</p>
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent onClick={() => handlePoleClick(pole.id)}>
                {pole.description && (
                  <p className="text-sm text-gray-600 mb-3">{pole.description}</p>
                )}
                {pole.responsable && (
                  <p className="text-xs text-gray-500">
                    Responsable : <span className="font-medium">{pole.responsable}</span>
                  </p>
                )}
              </CardContent>
              <div className="px-6 pb-4 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleEdit(pole);
                  }}
                >
                  <Edit className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDelete(pole.id);
                  }}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </Card>
          ))
        )}
        </div>
      ) : (
        /* Vue en Liste avec Arborescence */
        <Card>
          <CardContent className="p-0">
            {filteredPoles.length === 0 ? (
              <div className="text-center py-12">
                <FolderOpen className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                <p className="text-gray-500">Aucun pôle de service trouvé</p>
                <Button onClick={handleCreate} className="mt-4">
                  Créer le premier pôle
                </Button>
              </div>
            ) : (
              <div className="divide-y">
                {filteredPoles.map((pole) => {
                  const isExpanded = expandedPoles.has(pole.id);
                  const Icon = getFileIcon();
                  
                  return (
                    <div key={pole.id}>
                      {/* Pôle Header */}
                      <div className="flex items-center gap-3 p-4 hover:bg-gray-50 transition-colors">
                        <button
                          onClick={() => togglePoleExpansion(pole.id)}
                          className="p-1 hover:bg-gray-200 rounded"
                        >
                          {isExpanded ? (
                            <ChevronDown className="h-5 w-5" />
                          ) : (
                            <ChevronRight className="h-5 w-5" />
                          )}
                        </button>
                        
                        <div
                          className="w-10 h-10 rounded-lg flex items-center justify-center text-xl flex-shrink-0"
                          style={{ backgroundColor: `${pole.couleur || POLE_COLORS[pole.pole]}20` }}
                        >
                          {POLE_ICONS[pole.pole] || '📁'}
                        </div>

                        <div 
                          className="flex-1 cursor-pointer"
                          onClick={() => handlePoleClick(pole.id)}
                        >
                          <div className="flex items-center gap-2">
                            <h3 className="font-semibold">{pole.nom}</h3>
                            <span className="text-xs px-2 py-0.5 bg-gray-100 rounded-full">
                              {pole.pole}
                            </span>
                          </div>
                          {pole.description && (
                            <p className="text-sm text-gray-500 mt-1">{pole.description}</p>
                          )}
                          {pole.responsable && (
                            <p className="text-xs text-gray-400 mt-1">
                              Responsable : {pole.responsable}
                            </p>
                          )}
                        </div>

                        <div className="flex gap-2">
                          <span className="text-sm text-gray-500">
                            {pole.documents?.length || 0} doc(s)
                          </span>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleEdit(pole);
                            }}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDelete(pole.id);
                            }}
                          >
                            <Trash2 className="h-4 w-4 text-red-500" />
                          </Button>
                        </div>
                      </div>

                      {/* Documents List (expanded) */}
                      {isExpanded && (
                        <div className="bg-gray-50 border-t">
                          {pole.documents && pole.documents.length > 0 ? (
                            <div className="divide-y divide-gray-200">
                              {pole.documents.map((doc) => {
                                const DocIcon = getFileIcon(doc.type_fichier);
                                return (
                                  <div
                                    key={doc.id}
                                    className="flex items-center gap-3 p-3 pl-16 hover:bg-gray-100 transition-colors"
                                  >
                                    <DocIcon className="h-5 w-5 text-blue-500 flex-shrink-0" />
                                    <div className="flex-1 min-w-0">
                                      <p className="font-medium text-sm truncate">{doc.nom_fichier}</p>
                                      <p className="text-xs text-gray-500">
                                        {(doc.taille / 1024).toFixed(2)} KB
                                      </p>
                                    </div>
                                    <div className="flex gap-2">
                                      <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => {
                                          window.open(`${getBackendURL()}/api/documentations/documents/${doc.id}/view`, '_blank');
                                        }}
                                        title="Ouvrir dans un nouvel onglet"
                                      >
                                        <Eye className="h-4 w-4" />
                                      </Button>
                                      <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => {
                                          window.open(`${getBackendURL()}/api/documentations/documents/${doc.id}/download`, '_blank');
                                        }}
                                        title="Télécharger"
                                      >
                                        <Download className="h-4 w-4" />
                                      </Button>
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          ) : (
                            <div className="p-6 text-center text-gray-500 text-sm">
                              <FileText className="h-8 w-8 mx-auto mb-2 text-gray-300" />
                              Aucun document dans ce pôle
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Form Dialog */}
      <Dialog open={openForm} onOpenChange={setOpenForm}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{selectedPole ? 'Modifier' : 'Nouveau'} Pôle de Service</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Nom du pôle *</Label>
                <Input
                  value={formData.nom}
                  onChange={(e) => setFormData({ ...formData, nom: e.target.value })}
                  placeholder="ex: Service Maintenance"
                  required
                />
              </div>

              <div>
                <Label>Type de pôle *</Label>
                <Select
                  value={formData.pole}
                  onValueChange={(value) => setFormData({ ...formData, pole: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="MAINTENANCE">Maintenance</SelectItem>
                    <SelectItem value="PRODUCTION">Production</SelectItem>
                    <SelectItem value="QHSE">QHSE</SelectItem>
                    <SelectItem value="LOGISTIQUE">Logistique</SelectItem>
                    <SelectItem value="LABO">Laboratoire</SelectItem>
                    <SelectItem value="ADV">ADV</SelectItem>
                    <SelectItem value="INDUS">Industrialisation</SelectItem>
                    <SelectItem value="DIRECTION">Direction</SelectItem>
                    <SelectItem value="RH">Ressources Humaines</SelectItem>
                    <SelectItem value="AUTRE">Autre</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="col-span-2">
                <Label>Description</Label>
                <Textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
                  placeholder="Description du pôle..."
                />
              </div>

              <div className="col-span-2">
                <Label>Responsable</Label>
                <Input
                  value={formData.responsable}
                  onChange={(e) => setFormData({ ...formData, responsable: e.target.value })}
                  placeholder="Nom du responsable"
                />
              </div>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setOpenForm(false)}>
                Annuler
              </Button>
              <Button type="submit">
                {selectedPole ? 'Mettre à jour' : 'Créer'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Confirm Dialog */}
      <ConfirmDialog />

      {/* Document Preview Dialog */}
      <Dialog open={openPreview} onOpenChange={setOpenPreview}>
        <DialogContent className="max-w-4xl h-[80vh]">
          <DialogHeader>
            <DialogTitle>Prévisualisation : {previewDocument?.nom_fichier}</DialogTitle>
          </DialogHeader>
          <div className="flex-1 overflow-auto">
            {previewDocument && (
              <>
                {previewDocument.type_fichier?.includes('pdf') ? (
                  <iframe
                    src={`${getBackendURL()}/api/documentations/documents/${previewDocument.id}/view`}
                    className="w-full h-full border-0"
                    title="PDF Preview"
                  />
                ) : previewDocument.type_fichier?.includes('image') ? (
                  <img
                    src={`${getBackendURL()}/api/documentations/documents/${previewDocument.id}/view`}
                    alt={previewDocument.nom_fichier}
                    className="max-w-full h-auto mx-auto"
                  />
                ) : (
                  <div className="text-center py-12">
                    <FileText className="h-16 w-16 mx-auto text-gray-300 mb-4" />
                    <p className="text-gray-600 mb-4">
                      Prévisualisation non disponible pour ce type de fichier
                    </p>
                    <Button
                      onClick={() => {
                        window.open(`${getBackendURL()}/api/documentations/documents/${previewDocument.id}/view`, '_blank');
                      }}
                    >
                      <Eye className="mr-2 h-4 w-4" />
                      Ouvrir dans un nouvel onglet
                    </Button>
                  </div>
                )}
              </>
            )}
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                window.open(`${getBackendURL()}/api/documentations/documents/${previewDocument?.id}/download`, '_blank');
              }}
            >
              <Download className="mr-2 h-4 w-4" />
              Télécharger
            </Button>
            <Button onClick={() => setOpenPreview(false)}>
              Fermer
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default Documentations;
