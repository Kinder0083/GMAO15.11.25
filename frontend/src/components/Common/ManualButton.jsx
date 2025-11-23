import React, { useState, useEffect } from 'react';
import { Button } from '../ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui/dialog';
import { Input } from '../ui/input';
import { useToast } from '../../hooks/use-toast';
import { 
  BookOpen, 
  Search, 
  Download, 
  ChevronRight, 
  ChevronDown,
  Home,
  Filter,
  X
} from 'lucide-react';
import axios from 'axios';
import { getBackendURL } from '../../utils/config';
import './ManualButton.css';

const ManualButton = () => {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [manualData, setManualData] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedChapter, setSelectedChapter] = useState(null);
  const [selectedSection, setSelectedSection] = useState(null);
  const [expandedChapters, setExpandedChapters] = useState(new Set());
  const [levelFilter, setLevelFilter] = useState('both'); // 'beginner', 'advanced', 'both'
  const [moduleFilter, setModuleFilter] = useState('all');
  const [adminMode, setAdminMode] = useState(false);
  const [editingSection, setEditingSection] = useState(null);
  const [editTitle, setEditTitle] = useState('');
  const [editContent, setEditContent] = useState('');
  const [editLevel, setEditLevel] = useState('beginner');
  const { toast } = useToast();
  
  // Vérifier si l'utilisateur est ADMIN
  const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
  const isAdmin = currentUser.role === 'ADMIN';

  // Charger le manuel quand la modale s'ouvre ou quand les filtres changent
  useEffect(() => {
    if (open) {
      loadManual();
    }
  }, [open, levelFilter, moduleFilter]);

  const loadManual = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const backend_url = getBackendURL();
      
      const params = new URLSearchParams();
      if (levelFilter !== 'both') params.append('level_filter', levelFilter);
      if (moduleFilter !== 'all') params.append('module_filter', moduleFilter);
      
      console.log('📚 Chargement du manuel depuis:', `${backend_url}/api/manual/content`);
      
      const response = await axios.get(
        `${backend_url}/api/manual/content?${params.toString()}`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      
      console.log('📚 Manuel chargé:', response.data);
      console.log('📚 Chapitres:', response.data.chapters);
      console.log('📚 Sections:', response.data.sections);
      setManualData(response.data);
      
      // Sélectionner le premier chapitre par défaut
      if (response.data.chapters && response.data.chapters.length > 0) {
        const firstChapter = response.data.chapters[0];
        setSelectedChapter(firstChapter);
        
        console.log('📚 Premier chapitre:', firstChapter);
        console.log('📚 Sections du chapitre:', firstChapter.sections);
        
        // Ouvrir automatiquement le premier chapitre
        setExpandedChapters(new Set([firstChapter.id]));
        
        // Sélectionner la première section du premier chapitre
        const firstSection = response.data.sections.find(
          s => firstChapter.sections && firstChapter.sections.includes(s.id)
        );
        console.log('📚 Première section trouvée:', firstSection);
        
        if (firstSection) {
          setSelectedSection(firstSection);
        }
      }
    } catch (error) {
      console.error('❌ Erreur chargement manuel:', error);
      console.error('❌ Détails:', error.response?.data || error.message);
      toast({
        title: 'Erreur',
        description: error.response?.data?.detail || 'Impossible de charger le manuel',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const toggleChapter = (chapterId) => {
    const newExpanded = new Set(expandedChapters);
    if (newExpanded.has(chapterId)) {
      newExpanded.delete(chapterId);
    } else {
      newExpanded.add(chapterId);
      
      // Auto-sélectionner la première section du chapitre si aucune section n'est sélectionnée
      if (!selectedSection) {
        const chapter = manualData.chapters.find(c => c.id === chapterId);
        if (chapter && chapter.sections && chapter.sections.length > 0) {
          const firstSection = manualData.sections.find(s => chapter.sections.includes(s.id));
          if (firstSection) {
            selectSection(firstSection, chapter);
          }
        }
      }
    }
    setExpandedChapters(newExpanded);
  };

  const selectSection = (section, chapter) => {
    setSelectedSection(section);
    setSelectedChapter(chapter);
  };

  const exportPDF = async () => {
    try {
      setLoading(true);
      toast({
        title: 'Génération en cours...',
        description: 'Veuillez patienter pendant la génération du PDF'
      });
      
      const token = localStorage.getItem('token');
      const backend_url = getBackendURL();
      
      // Construire l'URL avec le filtre de niveau actuel
      const params = new URLSearchParams();
      if (levelFilter !== 'both') {
        params.append('level_filter', levelFilter);
      }
      
      // Télécharger le PDF
      const response = await fetch(
        `${backend_url}/api/manual/export-pdf?${params.toString()}`,
        {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      
      if (!response.ok) {
        throw new Error('Erreur lors de la génération du PDF');
      }
      
      // Créer un blob à partir de la réponse
      const blob = await response.blob();
      
      // Créer un lien de téléchargement temporaire
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `manuel_gmao_iris_${new Date().toISOString().split('T')[0]}.pdf`;
      document.body.appendChild(a);
      a.click();
      
      // Nettoyer
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      toast({
        title: 'Succès',
        description: 'Le PDF a été téléchargé avec succès',
        variant: 'default'
      });
      
    } catch (error) {
      console.error('Erreur export PDF:', error);
      toast({
        title: 'Erreur',
        description: 'Impossible de générer le PDF. Veuillez réessayer.',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };



  // Fonctions d'édition Admin
  const startEditSection = (section) => {
    setEditingSection(section.id);
    setEditTitle(section.title);
    setEditContent(section.content);
    setEditLevel(section.level);
  };

  const cancelEdit = () => {
    setEditingSection(null);
    setEditTitle('');
    setEditContent('');
    setEditLevel('beginner');
  };

  const saveSection = async () => {
    try {
      const token = localStorage.getItem('token');
      const backend_url = getBackendURL();
      
      const response = await axios.put(
        `${backend_url}/api/manual/sections/${editingSection}`,
        {
          title: editTitle,
          content: editContent,
          level: editLevel
        },
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      
      toast({
        title: 'Succès',
        description: 'Section mise à jour avec succès'
      });
      
      // Recharger le manuel
      await loadManual();
      cancelEdit();
      
    } catch (error) {
      console.error('Erreur sauvegarde:', error);
      toast({
        title: 'Erreur',
        description: 'Impossible de sauvegarder la section',
        variant: 'destructive'
      });
    }
  };

  const deleteSection = async (sectionId) => {
    if (!confirm('Êtes-vous sûr de vouloir supprimer cette section ?')) {
      return;
    }
    
    try {
      const token = localStorage.getItem('token');
      const backend_url = getBackendURL();
      
      await axios.delete(
        `${backend_url}/api/manual/sections/${sectionId}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      
      toast({
        title: 'Succès',
        description: 'Section supprimée avec succès'
      });
      
      // Recharger le manuel
      await loadManual();
      setSelectedSection(null);
      
    } catch (error) {
      console.error('Erreur suppression:', error);
      toast({
        title: 'Erreur',
        description: 'Impossible de supprimer la section',
        variant: 'destructive'
      });
    }
  };

  const searchManual = async () => {
    if (!searchQuery.trim()) return;
    
    try {
      const token = localStorage.getItem('token');
      const backend_url = getBackendURL();
      
      const response = await axios.post(
        `${backend_url}/api/manual/search`,
        {
          query: searchQuery,
          level_filter: levelFilter !== 'both' ? levelFilter : null,
          module_filter: moduleFilter !== 'all' ? moduleFilter : null
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      
      // Afficher les résultats dans la zone de contenu
      if (response.data.results && response.data.results.length > 0) {
        // Sélectionner le premier résultat
        const firstResult = response.data.results[0];
        const section = manualData.sections.find(s => s.id === firstResult.section_id);
        const chapter = manualData.chapters.find(c => c.id === firstResult.chapter_id);
        
        if (section && chapter) {
          selectSection(section, chapter);
          setExpandedChapters(new Set([chapter.id]));
        }
      } else {
        toast({
          title: 'Aucun résultat',
          description: 'Aucun résultat trouvé pour votre recherche'
        });
      }
    } catch (error) {
      console.error('Erreur recherche:', error);
    }
  };

  const renderTableOfContents = () => {
    if (!manualData || !manualData.chapters) return null;

    return (
      <div className="space-y-1">
        {manualData.chapters.map(chapter => {
          const chapterSections = manualData.sections.filter(
            s => chapter.sections.includes(s.id)
          );
          const isExpanded = expandedChapters.has(chapter.id);

          return (
            <div key={chapter.id} className="mb-2">
              <div
                className="flex items-center justify-between p-3 hover:bg-white rounded-lg cursor-pointer transition-colors border border-transparent hover:border-gray-200"
                onClick={() => toggleChapter(chapter.id)}
              >
                <div className="flex items-center gap-2 flex-1">
                  {isExpanded ? <ChevronDown size={18} className="text-gray-600" /> : <ChevronRight size={18} className="text-gray-600" />}
                  <span className="font-semibold text-sm text-gray-800">{chapter.title}</span>
                </div>
              </div>
              
              {isExpanded && chapterSections.length > 0 && (
                <div className="ml-8 mt-1 space-y-0.5">
                  {chapterSections.map(section => (
                    <div
                      key={section.id}
                      className={`p-2.5 text-sm rounded-lg cursor-pointer transition-all ${
                        selectedSection?.id === section.id 
                          ? 'bg-blue-100 text-blue-800 font-medium border-l-4 border-blue-600 pl-3' 
                          : 'hover:bg-gray-100 text-gray-700 hover:text-gray-900 border-l-4 border-transparent hover:border-gray-300 pl-3'
                      }`}
                      onClick={() => selectSection(section, chapter)}
                    >
                      <div className="flex items-center justify-between">
                        <span>{section.title}</span>
                        {section.level !== 'both' && (
                          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                            section.level === 'beginner' 
                              ? 'bg-green-100 text-green-700' 
                              : 'bg-orange-100 text-orange-700'
                          }`}>
                            {section.level === 'beginner' ? '🎓 Débutant' : '⚡ Avancé'}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    );
  };

  const renderContent = () => {
    if (loading) {
      return (
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Chargement du manuel...</p>
          </div>
        </div>
      );
    }

    if (!selectedSection) {
      return (
        <div className="flex items-center justify-center h-full">
          <div className="text-center text-gray-500">
            <BookOpen size={48} className="mx-auto mb-4 opacity-50" />
            <p>Sélectionnez une section dans la table des matières</p>
          </div>
        </div>
      );
    }

    return (
      <div className="max-w-5xl">
        {/* Breadcrumb */}
        <div className="manual-breadcrumb">
          <Home size={16} />
          <ChevronRight size={14} />
          <span>{selectedChapter?.title}</span>
          <ChevronRight size={14} />
          <span>{selectedSection.title}</span>
        </div>
        
        {/* Titre de la section */}
        <h1>{selectedSection.title}</h1>
        
        {/* Contenu avec formatage préservé */}
        <div className="whitespace-pre-wrap">{selectedSection.content}</div>
        
        {/* Images si présentes */}
        {selectedSection.images && selectedSection.images.length > 0 && (
          <div className="mt-8 space-y-6">
            {selectedSection.images.map((img, idx) => (
              <div key={idx} className="border rounded-lg p-4 bg-white shadow-sm">
                <img 
                  src={img} 
                  alt={`Illustration ${idx + 1}`} 
                  className="w-full rounded-lg"
                />
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setOpen(true)}
        className="flex items-center gap-2"
      >
        <BookOpen size={18} />
        <span>Manuel</span>
      </Button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-[95vw] w-[95vw] h-[92vh] p-0 flex flex-col">
          {/* Header */}
          <DialogHeader className="px-6 py-4 border-b shrink-0">
            <div className="flex items-center justify-between">
              <DialogTitle className="flex items-center gap-3 text-xl">
                <BookOpen size={28} className="text-blue-600" />
                <span>Manuel Utilisateur - GMAO Iris</span>
              </DialogTitle>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={exportPDF}
                  className="flex items-center gap-2"
                >
                  <Download size={16} />
                  Export PDF
                </Button>
              </div>
            </div>
          </DialogHeader>

          {/* Search Bar */}
          <div className="px-6 py-3 border-b bg-gray-50 shrink-0">
            <div className="flex gap-2 items-center">
              <div className="flex-1 relative">
                <Search size={18} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                <Input
                  placeholder="Rechercher dans le manuel..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && searchManual()}
                  className="pl-10"
                />
              </div>
              <Button onClick={searchManual} size="sm">
                Rechercher
              </Button>
              
              {/* Filtres */}
              <select
                value={levelFilter}
                onChange={(e) => setLevelFilter(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded text-sm bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="both">Tous niveaux</option>
                <option value="beginner">Débutant</option>
                <option value="advanced">Avancé</option>
              </select>
            </div>
          </div>

          {/* Content Area - with explicit height */}
          <div className="flex-1 flex overflow-hidden min-h-0">
            {/* Table of Contents - Sidebar with scrollbar */}
            <div className="w-80 border-r bg-gray-50 flex flex-col shrink-0">
              <div className="px-4 py-3 border-b bg-white">
                <h3 className="font-semibold flex items-center gap-2 text-base">
                  <Filter size={18} />
                  Table des Matières
                </h3>
              </div>
              <div className="flex-1 overflow-y-auto p-4 manual-scrollbar manual-toc">
                {renderTableOfContents()}
              </div>
            </div>

            {/* Main Content with scrollbar */}
            <div className="flex-1 flex flex-col overflow-hidden min-w-0">
              <div className="flex-1 overflow-y-auto p-8 manual-scrollbar manual-content">
                {renderContent()}
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default ManualButton;
