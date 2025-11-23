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
  const { toast } = useToast();

  // Charger le manuel quand la modale s'ouvre
  useEffect(() => {
    if (open && !manualData) {
      loadManual();
    }
  }, [open]);

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
    toast({
      title: 'Information',
      description: 'L\'export PDF sera disponible prochainement. Pour l\'instant, vous pouvez imprimer cette page (Ctrl+P) pour générer un PDF.',
      duration: 5000
    });
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
      <div className="space-y-2">
        {manualData.chapters.map(chapter => {
          const chapterSections = manualData.sections.filter(
            s => chapter.sections.includes(s.id)
          );
          const isExpanded = expandedChapters.has(chapter.id);

          return (
            <div key={chapter.id} className="border-b pb-2">
              <div
                className="flex items-center justify-between p-2 hover:bg-gray-100 rounded cursor-pointer"
                onClick={() => toggleChapter(chapter.id)}
              >
                <div className="flex items-center gap-2 flex-1">
                  {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                  <span className="font-semibold text-sm">{chapter.title}</span>
                </div>
              </div>
              
              {isExpanded && chapterSections.length > 0 && (
                <div className="ml-6 mt-1 space-y-1">
                  {chapterSections.map(section => (
                    <div
                      key={section.id}
                      className={`p-2 text-sm rounded cursor-pointer hover:bg-blue-50 ${
                        selectedSection?.id === section.id ? 'bg-blue-100 font-medium' : ''
                      }`}
                      onClick={() => selectSection(section, chapter)}
                    >
                      {section.title}
                      {section.level !== 'both' && (
                        <span className={`ml-2 text-xs px-1 rounded ${
                          section.level === 'beginner' ? 'bg-green-100 text-green-700' : 'bg-orange-100 text-orange-700'
                        }`}>
                          {section.level === 'beginner' ? 'Débutant' : 'Avancé'}
                        </span>
                      )}
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
      <div className="prose max-w-none">
        <div className="mb-6">
          <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
            <Home size={14} />
            <ChevronRight size={14} />
            <span>{selectedChapter?.title}</span>
            <ChevronRight size={14} />
            <span className="text-gray-700">{selectedSection.title}</span>
          </div>
          <h1 className="text-3xl font-bold mb-4">{selectedSection.title}</h1>
        </div>
        
        {/* Contenu en Markdown - pour l'instant en texte brut */}
        <div className="whitespace-pre-wrap">{selectedSection.content}</div>
        
        {/* Images si présentes */}
        {selectedSection.images && selectedSection.images.length > 0 && (
          <div className="mt-6 space-y-4">
            {selectedSection.images.map((img, idx) => (
              <img key={idx} src={img} alt={`Illustration ${idx + 1}`} className="rounded border" />
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
                onChange={(e) => {
                  setLevelFilter(e.target.value);
                  setManualData(null); // Forcer le rechargement
                }}
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
