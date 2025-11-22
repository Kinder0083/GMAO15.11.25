"""
Template HTML pour générer le PDF d'Autorisation Particulière de Travaux
Format: MAINT_FE_003_V03
"""

def generate_autorisation_html(autorisation: dict) -> str:
    """Génère le HTML pour l'autorisation particulière - Format strict selon MAINT_FE_003_V03"""
    
    # Données de l'autorisation
    numero = autorisation.get("numero", "")
    date_etablissement = autorisation.get("date_etablissement", "")
    service_demandeur = autorisation.get("service_demandeur", "")
    responsable = autorisation.get("responsable", "")
    
    # Personnel autorisé (4 entrées)
    personnel_autorise = autorisation.get("personnel_autorise", [])
    personnel_rows = ""
    for i in range(4):
        if i < len(personnel_autorise):
            nom = personnel_autorise[i].get("nom", "")
            fonction = personnel_autorise[i].get("fonction", "")
        else:
            nom = ""
            fonction = ""
        personnel_rows += f"""
            <tr>
                <td style="border: 1px solid black; padding: 8px 4px; text-align: center; height: 30px;">{i+1}</td>
                <td style="border: 1px solid black; padding: 8px; height: 30px;">{nom}</td>
                <td style="border: 1px solid black; padding: 8px; height: 30px;">{fonction}</td>
            </tr>
        """
    
    # Remplacer les sauts de ligne par <br> pour l'affichage HTML
    newline = "\n"
    br_tag = "<br>"
    description_travaux = autorisation.get("description_travaux", "").replace(newline, br_tag)
    horaire_debut = autorisation.get("horaire_debut", "")
    horaire_fin = autorisation.get("horaire_fin", "")
    lieu_travaux = autorisation.get("lieu_travaux", "")
    
    # Convertir les listes en HTML
    risques_potentiels = autorisation.get("risques_potentiels", "").replace(newline, br_tag)
    mesures_securite = autorisation.get("mesures_securite", "").replace(newline, br_tag)
    equipements_protection = autorisation.get("equipements_protection", "").replace(newline, br_tag)
    
    signature_demandeur = autorisation.get("signature_demandeur", "")
    date_signature_demandeur = autorisation.get("date_signature_demandeur", "")
    signature_responsable_securite = autorisation.get("signature_responsable_securite", "")
    date_signature_responsable = autorisation.get("date_signature_responsable", "")
    
    html = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Autorisation Particulière de Travaux - N°{numero}</title>
    <style>
        @page {{
            size: A4;
            margin: 15mm;
        }}
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: Arial, sans-serif;
            font-size: 11pt;
            line-height: 1.2;
            color: #000;
        }}
        .container {{
            width: 100%;
            max-width: 210mm;
            margin: 0 auto;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 10px;
            border-bottom: 2px solid #000;
            padding-bottom: 10px;
        }}
        .logo {{
            width: 120px;
            height: auto;
        }}
        .header-right {{
            text-align: right;
            font-size: 10pt;
        }}
        h1 {{
            text-align: center;
            font-size: 16pt;
            font-weight: bold;
            margin: 15px 0;
            text-transform: uppercase;
        }}
        .ref-box {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 15px;
            border: 2px solid #000;
            padding: 8px;
            background: #f0f0f0;
        }}
        .ref-item {{
            font-size: 10pt;
            font-weight: bold;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 10px;
        }}
        th {{
            background-color: #e0e0e0;
            border: 1px solid #000;
            padding: 6px;
            font-weight: bold;
            text-align: left;
            font-size: 10pt;
        }}
        td {{
            border: 1px solid #000;
            padding: 6px;
            font-size: 10pt;
        }}
        .section-title {{
            background-color: #c0c0c0;
            border: 1px solid #000;
            padding: 6px;
            font-weight: bold;
            margin-top: 10px;
            font-size: 11pt;
        }}
        .field-label {{
            font-weight: bold;
            font-size: 10pt;
        }}
        .textarea-field {{
            min-height: 80px;
            vertical-align: top;
        }}
        .signature-section {{
            display: flex;
            justify-content: space-between;
            margin-top: 20px;
        }}
        .signature-box {{
            width: 48%;
            border: 1px solid #000;
            padding: 10px;
        }}
        .signature-title {{
            font-weight: bold;
            margin-bottom: 10px;
            text-align: center;
        }}
        .signature-line {{
            margin-top: 40px;
            border-top: 1px solid #000;
            padding-top: 5px;
            font-size: 9pt;
        }}
        .small-text {{
            font-size: 9pt;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- En-tête -->
        <div class="header">
            <div>
                <div style="width: 120px; height: 60px; border: 1px solid #ccc; display: flex; align-items: center; justify-content: center; font-size: 9pt; color: #666;">
                    LOGO
                </div>
            </div>
            <div class="header-right">
                <div><strong>Référence :</strong> MAINT_FE_003</div>
                <div><strong>Révision :</strong> V03</div>
                <div><strong>Date :</strong> {date_etablissement}</div>
            </div>
        </div>

        <!-- Titre principal -->
        <h1>AUTORISATION PARTICULIÈRE DE TRAVAUX</h1>

        <!-- Référence -->
        <div class="ref-box">
            <span class="ref-item">N° D'AUTORISATION : {numero}</span>
            <span class="ref-item">DATE D'ÉTABLISSEMENT : {date_etablissement}</span>
        </div>

        <!-- Informations principales -->
        <table>
            <tr>
                <th style="width: 30%;">SERVICE DEMANDEUR</th>
                <td>{service_demandeur}</td>
            </tr>
            <tr>
                <th>RESPONSABLE</th>
                <td>{responsable}</td>
            </tr>
        </table>

        <!-- Personnel autorisé -->
        <div class="section-title">PERSONNEL AUTORISÉ</div>
        <table>
            <thead>
                <tr>
                    <th style="width: 8%; text-align: center;">N°</th>
                    <th style="width: 46%;">NOM ET PRÉNOM</th>
                    <th style="width: 46%;">FONCTION</th>
                </tr>
            </thead>
            <tbody>
                {personnel_rows}
            </tbody>
        </table>

        <!-- Description des travaux -->
        <div class="section-title">DESCRIPTION DES TRAVAUX</div>
        <table>
            <tr>
                <td class="textarea-field">{description_travaux}</td>
            </tr>
        </table>

        <!-- Horaires et lieu -->
        <table>
            <tr>
                <th style="width: 30%;">HORAIRE DÉBUT</th>
                <td style="width: 20%;">{horaire_debut}</td>
                <th style="width: 30%;">HORAIRE FIN</th>
                <td style="width: 20%;">{horaire_fin}</td>
            </tr>
            <tr>
                <th>LIEU DES TRAVAUX</th>
                <td colspan="3">{lieu_travaux}</td>
            </tr>
        </table>

        <!-- Risques potentiels -->
        <div class="section-title">RISQUES POTENTIELS</div>
        <table>
            <tr>
                <td class="textarea-field">{risques_potentiels}</td>
            </tr>
        </table>

        <!-- Mesures de sécurité -->
        <div class="section-title">MESURES DE SÉCURITÉ</div>
        <table>
            <tr>
                <td class="textarea-field">{mesures_securite}</td>
            </tr>
        </table>

        <!-- Équipements de protection -->
        <div class="section-title">ÉQUIPEMENTS DE PROTECTION INDIVIDUELLE (EPI)</div>
        <table>
            <tr>
                <td class="textarea-field">{equipements_protection}</td>
            </tr>
        </table>

        <!-- Signatures -->
        <div class="signature-section">
            <div class="signature-box">
                <div class="signature-title">DEMANDEUR</div>
                <div><strong>Nom :</strong> {signature_demandeur}</div>
                <div class="signature-line">Date : {date_signature_demandeur}</div>
            </div>
            <div class="signature-box">
                <div class="signature-title">RESPONSABLE SÉCURITÉ</div>
                <div><strong>Nom :</strong> {signature_responsable_securite}</div>
                <div class="signature-line">Date : {date_signature_responsable}</div>
            </div>
        </div>
    </div>
</body>
</html>
"""
    return html
