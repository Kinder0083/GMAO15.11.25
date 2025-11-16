"""
Service de gestion des mises à jour GMAO Iris
"""
import os
import json
import asyncio
import logging
import aiohttp
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict
import shutil

logger = logging.getLogger(__name__)

class UpdateService:
    def __init__(self, db):
        self.db = db
        self.current_version = "1.2.0"
        self.github_user = "Kinder0083"
        self.github_repo = "GMAO"
        self.github_branch = "main"
        self.version_file_url = f"https://raw.githubusercontent.com/{self.github_user}/{self.github_repo}/{self.github_branch}/updates/version.json"
        
    def parse_version(self, version_str: str) -> tuple:
        """Parse une version string en tuple (major, minor, patch)"""
        try:
            parts = version_str.split('.')
            return tuple(int(p) for p in parts)
        except:
            return (0, 0, 0)
    
    def compare_versions(self, v1: str, v2: str) -> int:
        """
        Compare deux versions
        Retourne: 1 si v1 > v2, -1 si v1 < v2, 0 si égales
        """
        v1_tuple = self.parse_version(v1)
        v2_tuple = self.parse_version(v2)
        
        if v1_tuple > v2_tuple:
            return 1
        elif v1_tuple < v2_tuple:
            return -1
        else:
            return 0
    
    async def check_for_updates(self) -> Optional[Dict]:
        """
        Vérifie si une mise à jour est disponible sur GitHub
        Retourne les informations de mise à jour si disponible, None sinon
        """
        try:
            logger.info(f"🔍 Vérification des mises à jour depuis {self.version_file_url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.version_file_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        remote_version_info = await response.json()
                        remote_version = remote_version_info.get("version", "0.0.0")
                        
                        # Comparer les versions
                        comparison = self.compare_versions(remote_version, self.current_version)
                        
                        if comparison > 0:
                            # Une nouvelle version est disponible
                            logger.info(f"✅ Nouvelle version disponible: {remote_version} (actuelle: {self.current_version})")
                            
                            # Enregistrer la notification dans la DB
                            await self._save_update_notification(remote_version_info)
                            
                            return {
                                "available": True,
                                "current_version": self.current_version,
                                "new_version": remote_version,
                                "version_name": remote_version_info.get("versionName", ""),
                                "release_date": remote_version_info.get("releaseDate", ""),
                                "description": remote_version_info.get("description", ""),
                                "changes": remote_version_info.get("changes", []),
                                "breaking": remote_version_info.get("breaking", False),
                                "download_url": remote_version_info.get("downloadUrl", "")
                            }
                        else:
                            logger.info(f"✅ Version à jour: {self.current_version}")
                            return {
                                "available": False,
                                "current_version": self.current_version,
                                "message": "Vous disposez de la dernière version"
                            }
                    else:
                        logger.error(f"❌ Erreur HTTP {response.status} lors de la vérification des mises à jour")
                        return None
                        
        except asyncio.TimeoutError:
            logger.error("❌ Timeout lors de la vérification des mises à jour")
            return None
        except Exception as e:
            logger.error(f"❌ Erreur lors de la vérification des mises à jour: {str(e)}")
            return None
    
    async def _save_update_notification(self, version_info: Dict):
        """Enregistre la notification de mise à jour dans la DB"""
        try:
            # Vérifier si cette version a déjà été notifiée
            existing = await self.db.update_notifications.find_one({
                "version": version_info.get("version")
            })
            
            if not existing:
                await self.db.update_notifications.insert_one({
                    "version": version_info.get("version"),
                    "version_name": version_info.get("versionName"),
                    "release_date": version_info.get("releaseDate"),
                    "description": version_info.get("description"),
                    "changes": version_info.get("changes", []),
                    "notified_at": datetime.utcnow(),
                    "dismissed": False
                })
                logger.info(f"📝 Notification de mise à jour sauvegardée: {version_info.get('version')}")
        except Exception as e:
            logger.error(f"❌ Erreur lors de la sauvegarde de la notification: {str(e)}")
    
    async def get_update_status(self) -> Dict:
        """Récupère le statut des mises à jour"""
        try:
            # Vérifier s'il y a une notification non-dismissée
            notification = await self.db.update_notifications.find_one(
                {"dismissed": False},
                sort=[("notified_at", -1)]
            )
            
            if notification:
                return {
                    "update_available": True,
                    "version": notification.get("version"),
                    "version_name": notification.get("version_name"),
                    "release_date": notification.get("release_date"),
                    "description": notification.get("description"),
                    "changes": notification.get("changes", []),
                    "current_version": self.current_version
                }
            else:
                return {
                    "update_available": False,
                    "current_version": self.current_version
                }
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération du statut: {str(e)}")
            return {"update_available": False, "current_version": self.current_version}
    
    async def dismiss_update_notification(self, version: str):
        """Marque une notification de mise à jour comme dismissée"""
        try:
            await self.db.update_notifications.update_one(
                {"version": version},
                {"$set": {"dismissed": True, "dismissed_at": datetime.utcnow()}}
            )
            logger.info(f"✅ Notification de mise à jour dismissée: {version}")
        except Exception as e:
            logger.error(f"❌ Erreur lors du dismiss de la notification: {str(e)}")
    
    async def create_backup(self) -> Dict:
        """Crée une sauvegarde complète avant mise à jour"""
        try:
            logger.info("📦 Création de la sauvegarde...")
            
            backup_dir = Path("/app/backups")
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_v{self.current_version}_{timestamp}"
            backup_path = backup_dir / backup_name
            backup_path.mkdir(exist_ok=True)
            
            # 1. Sauvegarde MongoDB avec mongodump
            mongo_backup_path = backup_path / "mongodb"
            mongo_backup_path.mkdir(exist_ok=True)
            
            mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
            db_name = os.environ.get('DB_NAME', 'gmao_iris')
            
            result = subprocess.run(
                ["mongodump", "--uri", mongo_url, "--db", db_name, "--out", str(mongo_backup_path)],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                raise Exception(f"Erreur mongodump: {result.stderr}")
            
            logger.info(f"✅ Sauvegarde MongoDB créée: {mongo_backup_path}")
            
            # 2. Export Excel de toutes les données
            excel_path = backup_path / "export_data.xlsx"
            await self._export_all_data_to_excel(excel_path)
            
            logger.info(f"✅ Export Excel créé: {excel_path}")
            
            # 3. Sauvegarde des fichiers uploads
            uploads_src = Path("/app/backend/uploads")
            if uploads_src.exists():
                uploads_dest = backup_path / "uploads"
                shutil.copytree(uploads_src, uploads_dest)
                logger.info(f"✅ Fichiers uploads sauvegardés: {uploads_dest}")
            
            # Enregistrer les infos de sauvegarde dans la DB
            backup_info = {
                "backup_name": backup_name,
                "backup_path": str(backup_path),
                "version": self.current_version,
                "created_at": datetime.utcnow(),
                "type": "pre_update",
                "size_mb": self._get_directory_size(backup_path)
            }
            
            await self.db.backups.insert_one(backup_info)
            
            return {
                "success": True,
                "backup_name": backup_name,
                "backup_path": str(backup_path),
                "message": "Sauvegarde créée avec succès"
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la création de la sauvegarde: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Erreur lors de la création de la sauvegarde"
            }
    
    async def _export_all_data_to_excel(self, excel_path: Path):
        """Exporte toutes les données au format Excel"""
        try:
            import pandas as pd
            from openpyxl import Workbook
            from openpyxl.utils.dataframe import dataframe_to_rows
            
            wb = Workbook()
            wb.remove(wb.active)  # Supprimer la feuille par défaut
            
            # Collections à exporter
            collections = [
                "users", "work_orders", "equipments", "locations",
                "inventory", "preventive_maintenance", "vendors",
                "intervention_requests", "improvement_requests", "improvements",
                "meters", "meter_readings"
            ]
            
            for collection_name in collections:
                try:
                    collection = self.db[collection_name]
                    data = await collection.find().to_list(length=None)
                    
                    if data:
                        # Convertir en DataFrame
                        df = pd.DataFrame(data)
                        
                        # Supprimer _id si présent
                        if '_id' in df.columns:
                            df = df.drop('_id', axis=1)
                        
                        # Créer une feuille
                        ws = wb.create_sheet(title=collection_name[:31])  # Max 31 chars pour Excel
                        
                        # Écrire les données
                        for r in dataframe_to_rows(df, index=False, header=True):
                            ws.append(r)
                        
                        logger.info(f"✅ Collection {collection_name} exportée ({len(data)} documents)")
                except Exception as e:
                    logger.error(f"❌ Erreur export {collection_name}: {str(e)}")
            
            wb.save(str(excel_path))
            logger.info(f"✅ Export Excel complet sauvegardé: {excel_path}")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'export Excel: {str(e)}")
            raise
    
    def _get_directory_size(self, path: Path) -> float:
        """Calcule la taille d'un répertoire en Mo"""
        try:
            total_size = sum(f.stat().st_size for f in path.glob('**/*') if f.is_file())
            return round(total_size / (1024 * 1024), 2)
        except:
            return 0.0
    
    async def apply_update(self, version: str) -> Dict:
        """Applique la mise à jour (git pull + restart)"""
        
        # Fonction helper pour logger dans un fichier ET dans le logger
        def log_detailed(message, level="INFO"):
            logger.info(message)
            try:
                from datetime import datetime
                with open("/tmp/update_process.log", "a") as f:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"[{timestamp}] [{level}] {message}\n")
            except Exception as e:
                logger.error(f"Erreur écriture log: {e}")
        
        try:
            log_detailed(f"🚀 Application de la mise à jour vers {version}...")
            log_detailed(f"Current version: {self.current_version}")
            log_detailed(f"Branch: {self.github_branch}")
            
            # 1. Créer une sauvegarde
            log_detailed("📋 Étape 1/7: Création du backup de la base de données...")
            backup_result = await self.create_backup()
            if not backup_result.get("success"):
                log_detailed(f"❌ ÉCHEC BACKUP: {backup_result.get('error')}", "ERROR")
                return {
                    "success": False,
                    "step": "backup",
                    "error": backup_result.get("error"),
                    "message": "Échec de la sauvegarde"
                }
            log_detailed(f"✅ Backup créé: {backup_result.get('backup_name')}")
            
            # 2. Git pull
            logger.info("📥 Téléchargement de la mise à jour depuis GitHub...")
            result = subprocess.run(
                ["git", "pull", "origin", self.github_branch],
                cwd="/app",
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                raise Exception(f"Erreur git pull: {result.stderr}")
            
            logger.info(f"✅ Mise à jour téléchargée: {result.stdout}")
            
            # 3. Installer les dépendances backend si requirements.txt a changé
            logger.info("📦 Installation des dépendances backend...")
            result = subprocess.run(
                ["/root/.venv/bin/pip", "install", "-r", "requirements.txt"],
                cwd="/app/backend",
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                logger.warning(f"⚠️ Attention lors de l'installation des dépendances: {result.stderr}")
            
            # 4. Installer les dépendances frontend si package.json a changé
            logger.info("📦 Installation des dépendances frontend...")
            result = subprocess.run(
                ["yarn", "install"],
                cwd="/app/frontend",
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                logger.warning(f"⚠️ Attention lors de l'installation des dépendances frontend: {result.stderr}")
            
            # 5. Enregistrer la mise à jour dans la DB
            await self.db.update_history.insert_one({
                "from_version": self.current_version,
                "to_version": version,
                "applied_at": datetime.utcnow(),
                "backup_name": backup_result.get("backup_name"),
                "success": True
            })
            
            # 6. Mettre à jour la version actuelle
            self.current_version = version
            
            # 7. Programmer le redémarrage des services avec délai
            logger.info("🔄 Programmation du redémarrage des services dans 3 secondes...")
            
            # Créer un script temporaire qui attendra 3 secondes puis redémarrera les services
            restart_script = """#!/bin/bash
sleep 3
sudo supervisorctl restart all
"""
            restart_script_path = "/tmp/restart_services.sh"
            with open(restart_script_path, "w") as f:
                f.write(restart_script)
            
            # Rendre le script exécutable
            os.chmod(restart_script_path, 0o755)
            
            # Lancer le script en arrière-plan
            subprocess.Popen(
                [restart_script_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True  # Détacher du processus parent
            )
            
            return {
                "success": True,
                "from_version": backup_result.get("backup_name"),
                "to_version": version,
                "backup_name": backup_result.get("backup_name"),
                "message": "Mise à jour appliquée avec succès. Les services redémarrent dans 3 secondes..."
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'application de la mise à jour: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Erreur lors de l'application de la mise à jour: {str(e)}"
            }
    
    async def get_recent_updates_info(self, days: int = 3) -> Optional[Dict]:
        """
        Récupère les informations des mises à jour récentes (pour le popup utilisateur)
        Retourne les infos si une MAJ a été faite dans les X derniers jours
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            recent_update = await self.db.update_history.find_one(
                {
                    "applied_at": {"$gte": cutoff_date},
                    "success": True
                },
                sort=[("applied_at", -1)]
            )
            
            if recent_update:
                # Récupérer les détails de la version depuis update_notifications
                version_info = await self.db.update_notifications.find_one({
                    "version": recent_update.get("to_version")
                })
                
                if version_info:
                    return {
                        "show_popup": True,
                        "version": recent_update.get("to_version"),
                        "version_name": version_info.get("version_name"),
                        "applied_at": recent_update.get("applied_at"),
                        "description": version_info.get("description"),
                        "changes": version_info.get("changes", [])
                    }
            
            return {"show_popup": False}
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des infos de MAJ: {str(e)}")
            return {"show_popup": False}
