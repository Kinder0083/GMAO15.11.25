import React, { useState } from 'react';
import { Button } from '../ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui/dialog';
import { Textarea } from '../ui/textarea';
import { Label } from '../ui/label';
import { useToast } from '../../hooks/use-toast';
import { HelpCircle, Loader2 } from 'lucide-react';
import { toPng } from 'html-to-image';
import axios from 'axios';
import { getBackendURL } from '../../utils/config';

const HelpButton = () => {
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState('');
  const [sending, setSending] = useState(false);
  const { toast } = useToast();

  const captureScreenshot = async () => {
    try {
      // Sauvegarder l'URL actuelle avant toute manipulation
      const currentUrl = window.location.href;
      console.log('📸 Capture de la page:', currentUrl);
      
      // Fermer temporairement la modale pour la capture
      setOpen(false);
      
      // Attendre que la modale se ferme complètement et que le DOM se stabilise
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Vérifier qu'on est toujours sur la même page
      if (window.location.href !== currentUrl) {
        console.warn('⚠️ Navigation détectée pendant la capture, annulation...');
        setOpen(true);
        return null;
      }
      
      // Masquer temporairement le badge Emergent pour la capture
      const emergentBadge = document.getElementById('emergent-badge');
      const originalBadgeDisplay = emergentBadge ? emergentBadge.style.display : null;
      if (emergentBadge) {
        emergentBadge.style.display = 'none';
      }
      
      // Capturer avec html-to-image (meilleure gestion CSS)
      const rootElement = document.getElementById('root') || document.body;
      const dataUrl = await toPng(rootElement, {
        quality: 0.8,
        pixelRatio: 1,
        cacheBust: true,
        filter: (node) => {
          // Filtrer les éléments à exclure
          if (node.id === 'emergent-badge') return false;
          const style = window.getComputedStyle(node);
          return style.display !== 'none' && style.visibility !== 'hidden';
        }
      });
      
      // Restaurer le badge
      if (emergentBadge && originalBadgeDisplay !== null) {
        emergentBadge.style.display = originalBadgeDisplay;
      }
      
      console.log('✅ Capture réussie pour:', currentUrl);
      
      // Rouvrir la modale après la capture
      setOpen(true);
      
      return dataUrl;
    } catch (error) {
      console.error('Erreur lors de la capture d\'écran:', error);
      setOpen(true);
      return null;
    }
  };

  const collectConsoleLogs = () => {
    // Récupérer les erreurs console récentes (si disponibles)
    const logs = [];
    
    // En production, on ne peut pas accéder aux console.error directement
    // mais on peut récupérer les erreurs stockées si on a un système de logging
    if (window.__consoleErrors && Array.isArray(window.__consoleErrors)) {
      logs.push(...window.__consoleErrors.slice(-10));
    }
    
    return logs;
  };

  const getBrowserInfo = () => {
    const ua = navigator.userAgent;
    let browserName = 'Unknown';
    let osName = 'Unknown';
    
    // Détecter le navigateur
    if (ua.indexOf('Chrome') > -1 && ua.indexOf('Edg') === -1) {
      browserName = 'Chrome';
    } else if (ua.indexOf('Safari') > -1 && ua.indexOf('Chrome') === -1) {
      browserName = 'Safari';
    } else if (ua.indexOf('Firefox') > -1) {
      browserName = 'Firefox';
    } else if (ua.indexOf('Edg') > -1) {
      browserName = 'Edge';
    } else if (ua.indexOf('MSIE') > -1 || ua.indexOf('Trident') > -1) {
      browserName = 'Internet Explorer';
    }
    
    // Détecter le système d'exploitation
    if (ua.indexOf('Win') > -1) {
      osName = 'Windows';
    } else if (ua.indexOf('Mac') > -1) {
      osName = 'MacOS';
    } else if (ua.indexOf('Linux') > -1) {
      osName = 'Linux';
    } else if (ua.indexOf('Android') > -1) {
      osName = 'Android';
    } else if (ua.indexOf('iOS') > -1) {
      osName = 'iOS';
    }
    
    return `${browserName} sur ${osName}`;
  };

  const handleSendHelp = async () => {
    setSending(true);
    
    try {
      // 1. Capturer l'écran
      toast({
        title: 'Capture en cours...',
        description: 'Préparation de votre demande d\'aide'
      });
      
      const screenshot = await captureScreenshot();
      
      if (!screenshot) {
        throw new Error('Impossible de capturer l\'écran');
      }
      
      console.log('📸 Screenshot capturé, taille:', screenshot.length, 'caractères');
      
      // 2. Collecter les informations
      const helpData = {
        screenshot: screenshot,
        user_message: message || null,
        page_url: window.location.href,
        browser_info: getBrowserInfo(),
        console_logs: collectConsoleLogs()
      };
      
      console.log('📦 Données préparées pour envoi');
      
      // 3. Envoyer au backend
      const token = localStorage.getItem('token');
      const backend_url = getBackendURL();
      
      console.log('🚀 Envoi vers:', `${backend_url}/api/support/request-help`);
      
      const response = await axios.post(
        `${backend_url}/api/support/request-help`,
        helpData,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      
      console.log('✅ Réponse reçue:', response.data);
      
      // 4. Confirmer le succès
      toast({
        title: 'Demande envoyée avec succès !',
        description: response.data.message,
        variant: 'default'
      });
      
      // Fermer la modale et réinitialiser
      setOpen(false);
      setMessage('');
      
    } catch (error) {
      console.error('❌ Erreur complète:', error);
      console.error('❌ Message:', error.message);
      console.error('❌ Response:', error.response);
      
      let errorMessage = 'Une erreur est survenue lors de l\'envoi';
      
      if (error.response?.status === 429) {
        errorMessage = 'Limite de demandes atteinte. Veuillez réessayer dans 1 heure.';
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      }
      
      toast({
        title: 'Erreur',
        description: errorMessage,
        variant: 'destructive'
      });
    } finally {
      setSending(false);
    }
  };

  return (
    <>
      <Button
        variant="outline"
        size="sm"
        onClick={() => setOpen(true)}
        className="gap-2 bg-red-50 hover:bg-red-100 text-red-700 border-red-200"
        title="Demander de l'aide"
      >
        <HelpCircle size={18} />
        <span className="hidden md:inline">Aide</span>
      </Button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <HelpCircle className="text-red-600" />
              Demander de l'aide
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <p className="text-sm text-gray-600">
              En cliquant sur "Envoyer", nous capturerons automatiquement :
            </p>
            <ul className="text-sm text-gray-600 list-disc list-inside space-y-1">
              <li>Une capture d'écran de votre page actuelle</li>
              <li>Les informations de votre navigateur</li>
              <li>L'URL de la page</li>
              <li>Les éventuelles erreurs console</li>
            </ul>
            
            <div className="space-y-2">
              <Label htmlFor="message">
                Décrivez votre problème (optionnel)
              </Label>
              <Textarea
                id="message"
                placeholder="Ex: Je n'arrive pas à créer un ordre de travail..."
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                rows={4}
                disabled={sending}
              />
            </div>
            
            <p className="text-xs text-gray-500">
              💡 Votre demande sera envoyée à tous les administrateurs du système.
            </p>
          </div>
          
          <div className="flex justify-end gap-2">
            <Button
              variant="outline"
              onClick={() => setOpen(false)}
              disabled={sending}
            >
              Annuler
            </Button>
            <Button
              onClick={handleSendHelp}
              disabled={sending}
              className="gap-2"
            >
              {sending ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  Envoi en cours...
                </>
              ) : (
                'Envoyer la demande'
              )}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default HelpButton;
