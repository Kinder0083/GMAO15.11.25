"""
Template HTML pour la génération du PDF Bon de Travail
Format: MAINT_FE_004_V02 - Basé sur le document Word officiel
"""

def generate_bon_travail_html(bon):
    """
    Génère le HTML du bon de travail selon le format MAINT_FE_004_V02
    
    Args:
        bon: dictionnaire contenant toutes les données du bon de travail (formData)
    
    Returns:
        str: HTML complet du document
    """
    
    # Extraction des données
    date_engagement = bon.get('date_engagement', '')[:10] if bon.get('date_engagement') else ''
    
    # Fonction helper pour générer les checkboxes
    def checkbox(label, checked_list, value):
        checked = value in (checked_list or [])
        check_mark = '✓' if checked else ''
        return f'<div class="checkbox-line"><span class="checkbox {"checked" if checked else ""}">{check_mark}</span> {label}</div>'
    
    # Listes des risques
    risques_materiel_list = ['Chute plain pied', 'Chute en hauteur', 'Manutention', 'Matériel en rotation', 'Electricité', 'Circulation engin']
    risques_autorisation_list = ['Point chaud', 'Espace confiné']
    risques_produits_list = ['Toxique', 'Inflammable', 'Corrosif', 'Irritant', 'CMR']
    risques_environnement_list = ['Co-activité', 'Passage chariot', 'Zone piétonne', 'Zone ATEX']
    
    # Listes des précautions
    precautions_materiel_list = ['Echafaudage', 'Nacelle', 'Harnais', 'Ligne vie', 'Consignation', 'Déconsignation']
    precautions_epi_list = ['Casque', 'Lunettes', 'Gants', 'Chaussures S3', 'Masque', 'Bouchons oreilles', 'Gilet HV']
    precautions_environnement_list = ['Balisage', 'Signalisation', 'Permis feu', 'Ventilation']
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Bon de travail - MAINT_FE_004_V02</title>
        <style>
            @page {{
                size: A4;
                margin: 15mm;
            }}
            body {{
                font-family: 'Calibri', 'Arial', sans-serif;
                margin: 0;
                padding: 0;
                font-size: 11pt;
                line-height: 1.4;
                color: #000;
            }}
            
            /* En-tête */
            .header {{
                text-align: center;
                margin-bottom: 10px;
                border-bottom: 2px solid #000;
                padding-bottom: 10px;
            }}
            .header h1 {{
                margin: 0;
                font-size: 18pt;
                font-weight: bold;
            }}
            .header .reference {{
                margin: 5px 0;
                font-size: 10pt;
                font-weight: bold;
            }}
            
            /* Introduction */
            .intro {{
                font-size: 10pt;
                text-align: justify;
                margin: 15px 0;
                padding: 10px;
                background-color: #f5f5f5;
                border: 1px solid #ccc;
            }}
            
            /* Sections */
            .section {{
                margin: 15px 0;
            }}
            .section-title {{
                font-weight: bold;
                font-size: 12pt;
                text-decoration: underline;
                margin-bottom: 10px;
            }}
            .subsection-title {{
                font-weight: bold;
                font-size: 11pt;
                margin-top: 10px;
                margin-bottom: 5px;
            }}
            
            /* Tableau de contenu */
            .content-table {{
                width: 100%;
                border-collapse: collapse;
                margin: 10px 0;
            }}
            .content-table td {{
                border: 1px solid #000;
                padding: 8px;
                vertical-align: top;
            }}
            .content-table .label-cell {{
                font-weight: bold;
                background-color: #e0e0e0;
                width: 30%;
            }}
            
            /* Checkboxes */
            .checkbox-line {{
                margin: 5px 0;
                padding-left: 5px;
            }}
            .checkbox {{
                display: inline-block;
                width: 14px;
                height: 14px;
                border: 2px solid #000;
                margin-right: 8px;
                vertical-align: middle;
                text-align: center;
                line-height: 12px;
                font-size: 12px;
                font-weight: bold;
            }}
            .checkbox.checked {{
                background-color: #000;
                color: white;
            }}
            
            /* Notes */
            .note {{
                font-size: 9pt;
                font-style: italic;
                margin: 10px 0;
                padding: 8px;
                background-color: #fff8dc;
                border-left: 3px solid #ffa500;
            }}
            
            /* Engagement */
            .engagement {{
                margin: 20px 0;
                padding: 10px;
                border: 1px solid #000;
                background-color: #f9f9f9;
            }}
            
            /* Tableau signatures */
            .signature-table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }}
            .signature-table th {{
                border: 2px solid #000;
                padding: 10px;
                background-color: #d0d0d0;
                font-weight: bold;
                text-align: center;
            }}
            .signature-table td {{
                border: 2px solid #000;
                padding: 15px;
                height: 80px;
                vertical-align: top;
                text-align: center;
            }}
            
            /* Pied de page */
            .footer {{
                margin-top: 30px;
                padding-top: 10px;
                border-top: 1px solid #000;
                font-size: 9pt;
                font-style: italic;
                text-align: center;
            }}
            
            @media print {{
                body {{ margin: 0; }}
                .no-print {{ display: none; }}
            }}
        </style>
    </head>
    <body>
        <!-- 1. EN-TÊTE -->
        <div class="header">
            <h1>Bon de travail</h1>
            <div class="reference">MAINT_FE_004_V02</div>
        </div>
        
        <!-- 2. PARAGRAPHE D'INTRODUCTION -->
        <div class="intro">
            Le bon de travail, permet d'identifier les risques liés aux travaux spécifiés ci-dessous ainsi que les précautions à prendre pour éviter tout accident, dégât matériel ou atteinte à l'environnement. Ce bon de travail tient lieu de plan de prévention. Sauf contre-indication particulière (ou modification des conditions d'intervention), le bon de travail est valable pour toute la durée du chantier (dans la limite de 24 heures).
        </div>
        
        <!-- 3. SECTION: TRAVAUX À RÉALISER -->
        <div class="section">
            <div class="section-title">TRAVAUX À RÉALISER</div>
            <table class="content-table">
                <tr>
                    <td class="label-cell">Titre du bon de travail :</td>
                    <td>{bon.get('titre', '')}</td>
                </tr>
                <tr>
                    <td class="label-cell">Localisation / Ligne :</td>
                    <td>{bon.get('localisation_ligne', '')}</td>
                </tr>
                <tr>
                    <td class="label-cell">Description des travaux :</td>
                    <td>{bon.get('description_travaux', '')}</td>
                </tr>
                <tr>
                    <td class="label-cell">Nom des intervenants :</td>
                    <td>{bon.get('nom_intervenants', '')}</td>
                </tr>
                <tr>
                    <td class="label-cell">Entreprise :</td>
                    <td>{bon.get('entreprise', '')}</td>
                </tr>
            </table>
        </div>
        
        <!-- 4. SECTION: RISQUES IDENTIFIÉS -->
        <div class="section">
            <div class="section-title">RISQUES IDENTIFIÉS</div>
            
            <div class="subsection-title">Risques matériels :</div>
            {''.join([checkbox(label, bon.get('risques_materiel', []), label) for label in risques_materiel_list])}
            <div class="checkbox-line"><strong>Autre (préciser) :</strong> {bon.get('risques_materiel_autre', '')}</div>
            
            <div class="subsection-title">Autorisation nécessaire :</div>
            {''.join([checkbox(label, bon.get('risques_autorisation', []), label) for label in risques_autorisation_list])}
            
            <div class="subsection-title">Risques liés aux produits :</div>
            {''.join([checkbox(label, bon.get('risques_produits', []), label) for label in risques_produits_list])}
            
            <div class="subsection-title">Risques liés à l'environnement :</div>
            {''.join([checkbox(label, bon.get('risques_environnement', []), label) for label in risques_environnement_list])}
            <div class="checkbox-line"><strong>Autre (préciser) :</strong> {bon.get('risques_environnement_autre', '')}</div>
        </div>
        
        <!-- 5. SECTION: PRÉCAUTIONS À PRENDRE -->
        <div class="section">
            <div class="section-title">PRÉCAUTIONS À PRENDRE</div>
            
            <div class="subsection-title">Précautions matérielles :</div>
            {''.join([checkbox(label, bon.get('precautions_materiel', []), label) for label in precautions_materiel_list])}
            <div class="checkbox-line"><strong>Autre (préciser) :</strong> {bon.get('precautions_materiel_autre', '')}</div>
            
            <div class="note">
                <strong>Note obligatoire :</strong> L'utilisation d'un chariot ou d'une nacelle n'est possible qu'après que l'entreprise intervenante ait fourni à IRIS une autorisation nominative de conduite.
            </div>
            
            <div class="subsection-title">Équipements de Protection Individuelle (EPI) :</div>
            {''.join([checkbox(label, bon.get('precautions_epi', []), label) for label in precautions_epi_list])}
            <div class="checkbox-line"><strong>Autre (préciser) :</strong> {bon.get('precautions_epi_autre', '')}</div>
            
            <div class="subsection-title">Précautions environnementales :</div>
            {''.join([checkbox(label, bon.get('precautions_environnement', []), label) for label in precautions_environnement_list])}
            <div class="checkbox-line"><strong>Autre (préciser) :</strong> {bon.get('precautions_environnement_autre', '')}</div>
        </div>
        
        <!-- 6. SECTION: ENGAGEMENT -->
        <div class="engagement">
            <strong>ENGAGEMENT</strong><br><br>
            Le représentant de l'entreprise intervenante reconnaît avoir pris connaissance des risques liés aux travaux qui lui sont confiés et s'engage à appliquer et faire appliquer les mesures de précaution qui lui ont été notifiées.
        </div>
        
        <!-- 7. SECTION: TABLE DES SIGNATURES -->
        <table class="signature-table">
            <tr>
                <th>Date</th>
                <th>Nom et visa du demandeur</th>
                <th>Nom et visa du représentant de l'intervenant</th>
            </tr>
            <tr>
                <td>{date_engagement}</td>
                <td>{bon.get('nom_agent_maitrise', '')}</td>
                <td>{bon.get('nom_representant', '')}</td>
            </tr>
        </table>
        
        <!-- 8. PIED DE PAGE -->
        <div class="footer">
            Remettre une copie à l'intervenant – Archivage Direction du site
        </div>
    </body>
    </html>
    """
    
    return html_content
