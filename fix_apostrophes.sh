#!/bin/bash
cd /app/frontend/src
sed -i "s/formatErrorMessage(error, 'Impossible de modifier l\\\\')utilisateur'/formatErrorMessage(error, 'Impossible de modifier l\\'utilisateur')/g" components/Common/EditUserDialog.jsx
sed -i "s/formatErrorMessage(error, 'Impossible d\\\\')envoyer l\\'invitation'/formatErrorMessage(error, 'Impossible d\\'envoyer l\\'invitation')/g" components/Common/InviteMemberDialog.jsx
sed -i "s/formatErrorMessage(error, 'Impossible d\\\\')uploader le fichier'/formatErrorMessage(error, 'Impossible d\\'uploader le fichier')/g" components/Improvements/AttachmentUploader.jsx
sed -i "s/formatErrorMessage(error, 'Impossible d\\\\')ajouter le relevé'/formatErrorMessage(error, 'Impossible d\\'ajouter le relevé')/g" components/Meters/MeterDialog.jsx
sed -i "s/formatErrorMessage(error, 'Impossible d\\\\')uploader le fichier'/formatErrorMessage(error, 'Impossible d\\'uploader le fichier')/g" components/WorkOrders/AttachmentUploader.jsx
echo "Corrections appliquées"
