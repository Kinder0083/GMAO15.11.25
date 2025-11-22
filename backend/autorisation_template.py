"""
Template HTML pour la génération du PDF Autorisation Particulière de Travaux
Format: MAINT_FE_003_V03
"""

# Logo IRIS en Base64 SVG (placeholder)
LOGO_IRIS_BASE64 = """data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIwIiBoZWlnaHQ9IjYwIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPgogIDxkZWZzPgogICAgPGxpbmVhckdyYWRpZW50IGlkPSJncmFkIiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUiIHkyPSIwJSI+CiAgICAgIDxzdG9wIG9mZnNldD0iMCUiIHN0eWxlPSJzdG9wLWNvbG9yOiM0YzFkOTU7c3RvcC1vcGFjaXR5OjEiIC8+CiAgICAgIDxzdG9wIG9mZnNldD0iMTAwJSIgc3R5bGU9InN0b3AtY29sb3I6IzY4NGU5ZjtzdG9wLW9wYWNpdHk6MSIgLz4KICAgIDwvbGluZWFyR3JhZGllbnQ+CiAgPC9kZWZzPgogIDxyZWN0IHdpZHRoPSIxMjAiIGhlaWdodD0iNjAiIGZpbGw9IiNmOWY5ZjkiIHJ4PSI1Ii8+CiAgPHBhdGggZD0iTSAyNSAyMCBRIDMwIDE1LCAzNSAyMCBRIDQwIDI1LCAzNSAzMCBRIDMwIDM1LCAyNSAzMCBRIDIwIDI1LCAyNSAyMCBaIiBmaWxsPSJ1cmwoI2dyYWQpIi8+CiAgPHRleHQgeD0iNDUiIHk9IjM1IiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMjQiIGZvbnQtd2VpZ2h0PSJib2xkIiBmaWxsPSIjNGMxZDk1Ij5JUklTPC90ZXh0Pgo8L3N2Zz4="""


def generate_autorisation_html(autorisation):
    """
    Génère le HTML de l'autorisation particulière selon le format MAINT_FE_003_V03
    """
    
    # Date formatée
    date_delivrance = autorisation.get('date_delivrance', '')[:10] if autorisation.get('date_delivrance') else ''
    
    # Fonction helper pour les checkboxes de type de travaux
    def checkbox_type(checked):
        return '☑' if checked else '☐'
    
    # Fonction helper pour les précautions (3 colonnes)
    def prec_row(label, prec_dict, precision_value=None):
        prec = prec_dict if isinstance(prec_dict, dict) else {"non": False, "oui": False, "fait": False}
        
        non_check = '✓' if prec.get('non', False) else ''
        oui_check = '✓' if prec.get('oui', False) else ''
        fait_check = '✓' if prec.get('fait', False) else ''
        
        precision_text = f' <span style="font-size: 9pt;">({precision_value})</span>' if precision_value else ''
        
        return f"""
        <tr>
            <td style="padding: 4px; border: 1px solid #000;">{label}{precision_text}</td>
            <td style="padding: 4px; border: 1px solid #000; text-align: center; width: 40px;">{non_check}</td>
            <td style="padding: 4px; border: 1px solid #000; text-align: center; width: 40px;">{oui_check}</td>
            <td style="padding: 4px; border: 1px solid #000; text-align: center; width: 40px;">{fait_check}</td>
        </tr>
        """
    
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Autorisation Particulière de Travaux - MAINT_FE_003_V03</title>
    <style>
        @page {{
            size: A4;
            margin: 15mm;
        }}
        
        body {{
            font-family: 'Calibri', 'Arial', sans-serif;
            margin: 0;
            padding: 0;
            font-size: 10pt;
            line-height: 1.3;
            color: #000;
        }}
        
        /* En-tête avec logo */
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #000;
        }}
        
        .header-left {{
            flex: 1;
        }}
        
        .logo {{
            width: 120px;
            height: 60px;
        }}
        
        .header-center {{
            flex: 2;
            text-align: center;
        }}
        
        .header-title {{
            font-size: 14pt;
            font-weight: bold;
            margin: 0;
        }}
        
        .header-subtitle {{
            font-size: 12pt;
            font-weight: bold;
            margin: 3px 0;
        }}
        
        .header-right {{
            flex: 1;
            text-align: right;
            font-size: 9pt;
        }}
        
        /* Instructions importantes */
        .instructions {{
            background-color: #fff8dc;
            border: 2px solid #ffa500;
            padding: 10px;
            margin: 15px 0;
            font-weight: bold;
            text-align: center;
        }}
        
        /* Sections */
        .section {{
            margin: 15px 0;
        }}
        
        .section-title {{
            font-weight: bold;
            font-size: 11pt;
            text-decoration: underline;
            margin-bottom: 8px;
        }}
        
        /* Champs */
        .field {{
            margin: 6px 0;
        }}
        
        .field-label {{
            font-weight: bold;
        }}
        
        .field-value {{
            border-bottom: 1px dotted #666;
            min-width: 200px;
            display: inline-block;
            padding: 0 5px;
        }}
        
        /* Cases à cocher type de travaux */
        .checkbox-group {{
            margin: 8px 0;
            display: flex;
            gap: 20px;
        }}
        
        .checkbox-item {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        
        /* Tableau des précautions */
        .precautions-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0;
            font-size: 9pt;
        }}
        
        .precautions-table th {{
            background-color: #d0d0d0;
            border: 2px solid #000;
            padding: 6px;
            font-weight: bold;
            text-align: center;
        }}
        
        .precautions-table td {{
            border: 1px solid #000;
            padding: 4px;
        }}
        
        /* Section validation */
        .validation {{
            margin: 20px 0;
            padding: 10px;
            border: 2px solid #000;
        }}
        
        /* Tableau vérifications */
        .verif-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0;
        }}
        
        .verif-table th,
        .verif-table td {{
            border: 2px solid #000;
            padding: 10px;
            text-align: center;
        }}
        
        .verif-table th {{
            background-color: #d0d0d0;
            font-weight: bold;
        }}
        
        /* Pied de page */
        .footer {{
            margin-top: 20px;
            padding-top: 10px;
            border-top: 1px solid #000;
            font-size: 9pt;
            font-style: italic;
            text-align: center;
        }}
        
        @media print {{
            body {{ margin: 0; }}
        }}
    </style>
</head>
<body>
    <!-- EN-TÊTE -->
    <div class="header">
        <div class="header-left">
            <img src="{LOGO_IRIS_BASE64}" alt="Logo IRIS" class="logo">
        </div>
        <div class="header-center">
            <div class="header-title">FORMULAIRE / ENREGISTREMENT</div>
            <div class="header-subtitle">Autorisation particulière de travaux</div>
        </div>
        <div class="header-right">
            <div><strong>MAINT/FE/003</strong></div>
            <div>Page 1/1</div>
            <div>Version 4</div>
        </div>
    </div>
    
    <!-- INSTRUCTIONS IMPORTANTES -->
    <div class="instructions">
        <div>À LIRE ATTENTIVEMENT</div>
        <div>À CONSERVER PAR L'EXÉCUTANT PENDANT L'INTERVENTION</div>
    </div>
    
    <p style="margin: 10px 0; font-style: italic; font-size: 9pt;">
        À rédiger par le donneur d'ordre avant le début des travaux
    </p>
    
    <!-- SECTION: TYPE DE TRAVAUX -->
    <div class="section">
        <div class="section-title">Cette autorisation particulière de travail concerne des travaux :</div>
        <div class="checkbox-group">
            <div class="checkbox-item">
                <span style="font-size: 14pt;">{checkbox_type(autorisation.get('type_point_chaud', False))}</span>
                <span>par point chaud</span>
            </div>
            <div class="checkbox-item">
                <span style="font-size: 14pt;">{checkbox_type(autorisation.get('type_espace_clos', False))}</span>
                <span>en espace clos ou confiné</span>
            </div>
            <div class="checkbox-item">
                <span style="font-size: 14pt;">{checkbox_type(autorisation.get('type_fouille', False))}</span>
                <span>de fouille</span>
            </div>
            <div class="checkbox-item">
                <span style="font-size: 14pt;">{checkbox_type(autorisation.get('type_autre', False))}</span>
                <span>autre cas : {autorisation.get('type_autre_precision', '')}</span>
            </div>
        </div>
    </div>
    
    <!-- DÉTAIL DES TRAVAUX -->
    <div class="section">
        <div class="field-label">Détail des travaux à réaliser :</div>
        <div style="border: 1px solid #000; padding: 8px; min-height: 60px; white-space: pre-wrap;">
            {autorisation.get('detail_travaux', '')}
        </div>
    </div>
    
    <!-- LIEU D'INTERVENTION -->
    <div class="section">
        <div class="section-title">Lieu d'intervention :</div>
        <div class="field">
            <span class="field-label">Matériel ou appareillage utilisé par l'entreprise :</span>
            <div class="field-value">{autorisation.get('lieu_materiel_appareillage', '')}</div>
        </div>
        <div class="field">
            <span class="field-label">Dernier produit ou fluide contenu dans l'appareil (ou tuyauterie) :</span>
            <div class="field-value">{autorisation.get('lieu_dernier_produit', '')}</div>
        </div>
    </div>
    
    <!-- DANGER ASSOCIÉ -->
    <div class="section">
        <div class="section-title">Danger associé :</div>
        <div class="field">
            <span class="field-label">Appareil, matériel ou activité avoisinantes présentant un danger :</span>
            <div class="field-value">{autorisation.get('lieu_danger_avoisinant', '')}</div>
        </div>
    </div>
    
    <!-- PRÉCAUTIONS À PRENDRE -->
    <div class="section">
        <div class="section-title">PRÉCAUTIONS À PRENDRE :</div>
        <table class="precautions-table">
            <thead>
                <tr>
                    <th style="width: 60%;">PRÉCAUTION</th>
                    <th>NON</th>
                    <th>OUI</th>
                    <th>FAIT</th>
                </tr>
            </thead>
            <tbody>
                {prec_row('CONSIGNATION MAT. OU PIÈCE EN MOUVEMENT', autorisation.get('prec_consignation_materiel', {}))}
                {prec_row('CONSIGNATION ÉLECTRIQUE', autorisation.get('prec_consignation_electrique', {}))}
                {prec_row('DÉBRANCHEMENT FORCE MOTRICE', autorisation.get('prec_debranchement_force', {}))}
                {prec_row('VIDANGE APPAREIL/TUYAUTERIE', autorisation.get('prec_vidange_appareil', {}))}
                {prec_row('DÉCONTAMINATION/LAVAGE', autorisation.get('prec_decontamination', {}))}
                {prec_row('DÉGAZAGE', autorisation.get('prec_degazage', {}))}
                {prec_row('POSE JOINT PLEIN', autorisation.get('prec_pose_joint_plein', {}))}
                {prec_row('VENTILATION FORCÉE', autorisation.get('prec_ventilation_forcee', {}))}
                {prec_row('ZONE BALISÉE', autorisation.get('prec_zone_balisee', {}))}
                {prec_row('CANALISATIONS ÉLECTRIQUES', autorisation.get('prec_canalisations_electriques', {}))}
                {prec_row('SOUTERRAINES BALISÉES', autorisation.get('prec_souterraines_balisees', {}))}
                {prec_row('ÉGOUTS ET CÂBLES PROTÉGÉS', autorisation.get('prec_egouts_cables', {}))}
                {prec_row('TAUX D\'OXYGÈNE', autorisation.get('prec_taux_oxygene', {}))}
                {prec_row('TAUX D\'EXPLOSIVITÉ', autorisation.get('prec_taux_explosivite', {}))}
                {prec_row('EXPLOSIMÈTRE EN CONTINU', autorisation.get('prec_explosimetre_continu', {}))}
                {prec_row('ÉCLAIRAGE DE SÛRETÉ', autorisation.get('prec_eclairage_surete', {}))}
                {prec_row('EXTINCTEUR TYPE', autorisation.get('prec_extincteur_type', {}), autorisation.get('prec_extincteur_type_precision', ''))}
                {prec_row('AUTRES (matérielles)', autorisation.get('prec_autres_materielles', {}), autorisation.get('prec_autres_materielles_precision', ''))}
                {prec_row('VISIÈRE', autorisation.get('prec_visiere', {}))}
                {prec_row('TENUE IMPERMÉABLE, BOTTES', autorisation.get('prec_tenue_impermeable', {}))}
                {prec_row('CAGOULE AIR RESPIRABLE/ART', autorisation.get('prec_cagoule_air', {}))}
                {prec_row('MASQUE TYPE', autorisation.get('prec_masque_type', {}), autorisation.get('prec_masque_type_precision', ''))}
                {prec_row('GANT TYPE', autorisation.get('prec_gant_type', {}), autorisation.get('prec_gant_type_precision', ''))}
                {prec_row('HARNAIS DE SÉCURITÉ', autorisation.get('prec_harnais_securite', {}))}
                {prec_row('OUTILLAGE ANTI-ÉTINCELLE', autorisation.get('prec_outillage_anti_etincelle', {}))}
                {prec_row('PRÉSENCE D\'UN SURVEILLANT', autorisation.get('prec_presence_surveillant', {}))}
                {prec_row('AUTRES (EPI)', autorisation.get('prec_autres_epi', {}), autorisation.get('prec_autres_epi_precision', ''))}
            </tbody>
        </table>
    </div>
    
    <!-- VALIDATION -->
    <div class="validation">
        <div style="font-weight: bold; text-decoration: underline; margin-bottom: 10px;">
            Validation (Responsable du site ou son délégué) :
        </div>
        <div style="margin: 8px 0;">
            <span class="field-label">Cette autorisation est établie par :</span>
            <span class="field-value" style="min-width: 300px;">{autorisation.get('etablie_par', '')}</span>
        </div>
        <div style="margin: 8px 0;">
            <span class="field-label">Est délivrée à :</span>
            <span class="field-value" style="min-width: 300px;">{autorisation.get('delivree_a', '')}</span>
            <span class="field-label" style="margin-left: 20px;">Le :</span>
            <span class="field-value">{date_delivrance}</span>
        </div>
    </div>
    
    <!-- VÉRIFICATION POST-INTERVENTION -->
    <div class="section">
        <div class="section-title">
            Vérification à la fin des travaux de l'absence de risque résiduel suite à l'intervention
        </div>
        <table class="verif-table">
            <thead>
                <tr>
                    <th>Visite AM après la fin de l'intervention</th>
                    <th style="width: 200px;">Visa AM</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>30 minutes</td>
                    <td>{autorisation.get('verif_30min_visa', '')}</td>
                </tr>
                <tr>
                    <td>1 heure</td>
                    <td>{autorisation.get('verif_1h_visa', '')}</td>
                </tr>
                <tr>
                    <td>2 heures</td>
                    <td>{autorisation.get('verif_2h_visa', '')}</td>
                </tr>
            </tbody>
        </table>
    </div>
    
    <!-- PIED DE PAGE -->
    <div class="footer">
        Remettre une copie à l'intervenant – Archivage Direction du site
    </div>
</body>
</html>
    """
    
    return html_content
