from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import subprocess
import logging
from typing import Optional
from dependencies import get_current_user

router = APIRouter(prefix="/ssh", tags=["SSH Terminal"])
logger = logging.getLogger(__name__)

class CommandRequest(BaseModel):
    command: str

class CommandResponse(BaseModel):
    stdout: str
    stderr: str
    exit_code: int

@router.post("/execute", response_model=CommandResponse)
async def execute_ssh_command(
    request: CommandRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Exécuter une commande SSH dans le container
    Réservé aux super administrateurs uniquement
    """
    try:
        # Vérifier que l'utilisateur est admin
        # Autoriser: rôle "admin", "ADMIN", ou emails spécifiques
        user_role = current_user.get("role", "").upper()
        user_email = current_user.get("email", "")
        
        allowed_emails = ["admin@gmao-iris.local", "buenogy@gmail.com"]
        
        if user_role != "ADMIN" and user_email not in allowed_emails:
            raise HTTPException(
                status_code=403, 
                detail="Accès refusé. Réservé aux super administrateurs uniquement."
            )
        
        # Exécuter la commande de manière sécurisée
        result = subprocess.run(
            request.command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,  # Timeout de 30 secondes
            cwd="/app"  # Exécuter depuis le dossier /app
        )
        
        logger.info(f"SSH Command executed by {current_user.get('email')}: {request.command}")
        
        return CommandResponse(
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode
        )
    
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Timeout: La commande a pris trop de temps")
    except Exception as e:
        logger.error(f"Error executing SSH command: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@router.get("/status")
async def get_ssh_status(current_user: dict = Depends(get_current_user)):
    """Vérifier le statut du service SSH"""
    try:
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Accès refusé")
        
        result = subprocess.run(
            ["systemctl", "is-active", "ssh"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        return {
            "status": "active" if result.returncode == 0 else "inactive",
            "message": result.stdout.strip()
        }
    except Exception as e:
        return {"status": "unknown", "message": str(e)}
