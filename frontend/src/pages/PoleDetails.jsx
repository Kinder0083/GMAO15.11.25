import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Badge } from '../components/ui/badge';
import {
  ArrowLeft, Plus, Upload, FileText, Download, Trash2, Edit, File,
  FileSpreadsheet, FileImage, FileVideo, Mail, Printer, Eye, Shield
} from 'lucide-react';
import { documentationsAPI, autorisationsAPI } from '../services/api';
import { useToast } from '../hooks/use-toast';
import { useConfirmDialog } from '../components/ui/confirm-dialog';
import { formatErrorMessage } from '../utils/errorFormatter';

const FILE_ICONS = {
  'application/pdf': FileText,
  'application/msword': FileText,
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': FileText,
  'application/vnd.ms-excel': FileSpreadsheet,
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': FileSpreadsheet,
  'image/': FileImage,
  'video/': FileVideo
};

function PoleDetails() {
  const { poleId } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const { confirm, ConfirmDialog } = useConfirmDialog();
  const fileInputRef = useRef(null);

  const [pole, setPole] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [bonsTravail, setBonsTravail] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentUser, setCurrentUser] = useState(null);
  
  // Charger l'utilisateur actuel
  useEffect(() => {
    const userData = localStorage.getItem('user');
    if (userData) {
      setCurrentUser(JSON.parse(userData));
    }
  }, []);
  const [openDocForm, setOpenDocForm] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [uploading, setUploading] = useState(false);

  const [docFormData, setDocFormData] = useState({
    titre: '',
    description: '',
    type_document: 'PIECE_JOINTE',
    tags: []
  });

  useEffect(() => {
    loadData();
  }, [poleId]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [poleData, documentsData, bonsTravailData] = await Promise.all([
        documentationsAPI.getPole(poleId),
        documentationsAPI.getDocuments({ pole_id: poleId }),
        documentationsAPI.getBonsTravail({ pole_id: poleId })
      ]);
      setPole(poleData);
      setDocuments(documentsData);
      setBonsTravail(bonsTravailData);
    } catch (error) {
      console.error('Erreur chargement:', error);
      toast({
        title: 'Erreur',
        description: formatErrorMessage(error, 'Erreur lors du chargement'),
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCreateDocument = () => {
    setSelectedDocument(null);
    setDocFormData({
      titre: '',
      description: '',
      type_document: 'PIECE_JOINTE',
      tags: []
    });
    setOpenDocForm(true);
  };

  const handleCreateBonTravail = () => {
    navigate(`/documentations/${poleId}/bon-de-travail`);
  };
  
  const canEditBonTravail = (bon) => {
    if (!currentUser) return false;
    // Admin peut tout modifier
    if (currentUser.role === 'ADMIN') return true;
    // Créateur peut modifier son propre bon
    return bon.created_by === currentUser.id;
  };
  
  const isAdmin = () => {
    return currentUser && currentUser.role === 'ADMIN';
  };
  
  const handleDeleteBonTravail = (bonId) => {
    confirm({
      title: 'Supprimer le bon de travail',
      description: 'Êtes-vous sûr de vouloir supprimer ce bon de travail ? Cette action est irréversible.',
      confirmText: 'Supprimer',
      cancelText: 'Annuler',
      variant: 'destructive',
      onConfirm: async () => {
        try {
          await documentationsAPI.deleteBonTravail(bonId);
          toast({ title: 'Succès', description: 'Bon de travail supprimé' });
          loadData(); // Recharger la liste
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

  const handleSubmitDocument = async (e) => {
    e.preventDefault();
    try {
      const data = {
        ...docFormData,
        pole_id: poleId
      };

      if (selectedDocument) {
        await documentationsAPI.updateDocument(selectedDocument.id, data);
        toast({ title: 'Succès', description: 'Document mis à jour' });
      } else {
        await documentationsAPI.createDocument(data);
        toast({ title: 'Succès', description: 'Document créé' });
      }
      setOpenDocForm(false);
      loadData();
    } catch (error) {
      toast({
        title: 'Erreur',
        description: formatErrorMessage(error, 'Erreur lors de l\'enregistrement'),
        variant: 'destructive'
      });
    }
  };

  const handleUploadFile = async (docId, file) => {
    try {
      setUploading(true);
      await documentationsAPI.uploadFile(docId, file);
      toast({ title: 'Succès', description: 'Fichier uploadé' });
      loadData();
    } catch (error) {
      toast({
        title: 'Erreur',
        description: formatErrorMessage(error, 'Erreur lors de l\'upload'),
        variant: 'destructive'
      });
    } finally {
      setUploading(false);
    }
  };

  const handleFileSelect = async (e, docId) => {
    const file = e.target.files[0];
    if (file) {
      await handleUploadFile(docId, file);
    }
  };

  const handleDownload = async (docId, fileName) => {
    try {
      const blob = await documentationsAPI.downloadFile(docId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = fileName;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      toast({
        title: 'Erreur',
        description: formatErrorMessage(error, 'Erreur lors du téléchargement'),
        variant: 'destructive'
      });
    }
  };

  const handleDelete = (docId) => {
    confirm({
      title: 'Supprimer le document',
      description: 'Êtes-vous sûr de vouloir supprimer ce document ? Cette action est irréversible.',
      confirmText: 'Supprimer',
      cancelText: 'Annuler',
      variant: 'destructive',
      onConfirm: async () => {
        try {
          await documentationsAPI.deleteDocument(docId);
          toast({ title: 'Succès', description: 'Document supprimé' });
          loadData();
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

  const getFileIcon = (fileType) => {
    if (!fileType) return File;
    for (const [type, Icon] of Object.entries(FILE_ICONS)) {
      if (fileType.startsWith(type)) return Icon;
    }
    return File;
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p>Chargement...</p>
      </div>
    );
  }

  if (!pole) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p>Pôle non trouvé</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div>
        <Button variant="ghost" onClick={() => navigate('/documentations')} className="mb-4">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Retour aux pôles
        </Button>
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold">{pole.nom}</h1>
            <p className="text-gray-500">{pole.description || 'Pôle de service'}</p>
            {pole.responsable && (
              <p className="text-sm text-gray-600 mt-1">
                Responsable : <span className="font-medium">{pole.responsable}</span>
              </p>
            )}
          </div>
          <div className="flex gap-2">
            <Button onClick={handleCreateBonTravail} variant="outline">
              <FileText className="mr-2 h-4 w-4" />
              Nouveau Bon de Travail
            </Button>
            <Button onClick={() => navigate('/autorisations-particulieres/new')} variant="outline">
              <Shield className="mr-2 h-4 w-4" />
              Autorisation Particulière
            </Button>
            <Button onClick={handleCreateDocument}>
              <Plus className="mr-2 h-4 w-4" />
              Ajouter Document
            </Button>
          </div>
        </div>
      </div>

      {/* Bons de Travail List */}
      {bonsTravail.length > 0 && (
        <div className="space-y-6">
          <h2 className="text-xl font-semibold">Bons de Travail ({bonsTravail.length})</h2>
          
          {/* Grouper par entreprise */}
          {Object.entries(
            bonsTravail.reduce((acc, bon) => {
              const entreprise = bon.entreprise || 'Non assignée';
              if (!acc[entreprise]) acc[entreprise] = [];
              acc[entreprise].push(bon);
              return acc;
            }, {})
          ).map(([entreprise, bons]) => (
            <div key={entreprise} className="space-y-3">
              <div className="flex items-center gap-3">
                <div className="flex-1 h-px bg-gray-300"></div>
                <h3 className="text-lg font-semibold text-gray-700 px-4 bg-gray-50 rounded-full">
                  📁 {entreprise} ({bons.length})
                </h3>
                <div className="flex-1 h-px bg-gray-300"></div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {bons.map((bon) => (
              <Card key={bon.id} className="hover:shadow-lg transition-shadow cursor-pointer">
                <CardHeader className="pb-3">
                  <CardTitle className="text-base">{bon.titre || "Sans titre"}</CardTitle>
                  <p className="text-sm text-gray-500">
                    {bon.created_at ? new Date(bon.created_at).toLocaleDateString('fr-FR') : 'Date inconnue'}
                  </p>
                  {bon.entreprise && (
                    <p className="text-xs text-gray-400">Entreprise: {bon.entreprise}</p>
                  )}
                </CardHeader>
                <CardContent>
                  {bon.description && (
                    <p className="text-sm text-gray-600 mb-3 line-clamp-2">{bon.description}</p>
                  )}
                  <div className="flex gap-2 mt-3">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/documentations/${poleId}/bon-de-travail/${bon.id}/view`);
                      }}
                    >
                      <Eye className="h-4 w-4 mr-1" />
                      Voir
                    </Button>
                    {canEditBonTravail(bon) && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/documentations/${poleId}/bon-de-travail/${bon.id}/edit`);
                        }}
                      >
                        <Edit className="h-4 w-4 mr-1" />
                        Modifier
                      </Button>
                    )}
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={(e) => {
                        e.stopPropagation();
                        const token = localStorage.getItem('token');
                        const printUrl = `${process.env.REACT_APP_BACKEND_URL || window.location.origin}/api/documentations/bons-travail/${bon.id}/pdf?token=${token}`;
                        const printWindow = window.open(printUrl, '_blank');
                        if (printWindow) {
                          printWindow.onload = () => printWindow.print();
                        }
                      }}
                    >
                      <Printer className="h-4 w-4 mr-1" />
                      Imprimer
                    </Button>
                    {isAdmin() && (
                      <Button
                        size="sm"
                        variant="outline"
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteBonTravail(bon.id);
                        }}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Séparateur Documents Utilisateur */}
      {documents.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <div className="flex-1 h-px bg-gray-300"></div>
            <h3 className="text-lg font-semibold text-gray-700 px-4 bg-gray-50 rounded-full">
              📄 Documents Utilisateur ({documents.length})
            </h3>
            <div className="flex-1 h-px bg-gray-300"></div>
          </div>
        </div>
      )}

      {/* Documents List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {documents.length === 0 ? (
          <div className="col-span-full text-center py-12">
            <FileText className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <p className="text-gray-500 mb-4">Aucun document dans ce pôle</p>
            <Button onClick={handleCreateDocument}>Ajouter le premier document</Button>
          </div>
        ) : (
          documents.map((doc) => {
            const FileIcon = getFileIcon(doc.fichier_type);
            return (
              <Card key={doc.id} className="hover:shadow-lg transition-shadow">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3 flex-1">
                      <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                        <FileIcon className="h-5 w-5 text-blue-600" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <CardTitle className="text-base truncate">{doc.titre}</CardTitle>
                        <p className="text-xs text-gray-500">{doc.type_document}</p>
                      </div>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  {doc.description && (
                    <p className="text-sm text-gray-600 mb-3 line-clamp-2">{doc.description}</p>
                  )}

                  {doc.fichier_nom && (
                    <div className="bg-gray-50 rounded p-2 mb-3">
                      <p className="text-xs font-medium truncate">{doc.fichier_nom}</p>
                      <p className="text-xs text-gray-500">{formatFileSize(doc.fichier_taille)}</p>
                    </div>
                  )}

                  {doc.tags && doc.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-3">
                      {doc.tags.map((tag, idx) => (
                        <Badge key={idx} variant="outline" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  )}

                  <div className="flex gap-2">
                    {!doc.fichier_url ? (
                      <>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => fileInputRef.current?.click()}
                          disabled={uploading}
                        >
                          <Upload className="h-4 w-4 mr-1" />
                          Upload
                        </Button>
                        <input
                          ref={fileInputRef}
                          type="file"
                          style={{ display: 'none' }}
                          onChange={(e) => handleFileSelect(e, doc.id)}
                        />
                      </>
                    ) : (
                      <>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            const token = localStorage.getItem('token');
                            window.open(`${process.env.REACT_APP_BACKEND_URL || window.location.origin}/api/documentations/documents/${doc.id}/view?token=${token}`, '_blank');
                          }}
                          title="Ouvrir dans un nouvel onglet"
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleDownload(doc.id, doc.fichier_nom)}
                          title="Télécharger"
                        >
                          <Download className="h-4 w-4" />
                        </Button>
                      </>
                    )}
                    <Button size="sm" variant="outline" onClick={() => handleDelete(doc.id)}>
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })
        )}
      </div>

      {/* Document Form Dialog */}
      <Dialog open={openDocForm} onOpenChange={setOpenDocForm}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{selectedDocument ? 'Modifier' : 'Nouveau'} Document</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmitDocument} className="space-y-4">
            <div className="space-y-4">
              <div>
                <Label>Titre *</Label>
                <Input
                  value={docFormData.titre}
                  onChange={(e) => setDocFormData({ ...docFormData, titre: e.target.value })}
                  required
                />
              </div>

              <div>
                <Label>Type de document *</Label>
                <Select
                  value={docFormData.type_document}
                  onValueChange={(value) =>
                    setDocFormData({ ...docFormData, type_document: value })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="PIECE_JOINTE">Pièce jointe</SelectItem>
                    <SelectItem value="FORMULAIRE">Formulaire en ligne</SelectItem>
                    <SelectItem value="TEMPLATE">Template</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label>Description</Label>
                <Textarea
                  value={docFormData.description}
                  onChange={(e) => setDocFormData({ ...docFormData, description: e.target.value })}
                  rows={3}
                />
              </div>

              <div>
                <Label>Tags (séparés par virgule)</Label>
                <Input
                  value={docFormData.tags.join(', ')}
                  onChange={(e) =>
                    setDocFormData({
                      ...docFormData,
                      tags: e.target.value.split(',').map((t) => t.trim()).filter(Boolean)
                    })
                  }
                  placeholder="maintenance, urgent, formation"
                />
              </div>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setOpenDocForm(false)}>
                Annuler
              </Button>
              <Button type="submit">
                {selectedDocument ? 'Mettre à jour' : 'Créer'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Confirm Dialog */}
      <ConfirmDialog />
    </div>
  );
}

export default PoleDetails;
