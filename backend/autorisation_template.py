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
    
    # Types de travaux (checkboxes)
    type_point_chaud = "☑" if autorisation.get("type_point_chaud") else "☐"
    type_fouille = "☑" if autorisation.get("type_fouille") else "☐"
    type_espace_clos = "☑" if autorisation.get("type_espace_clos") else "☐"
    type_autre_cas = "☑" if autorisation.get("type_autre_cas") else "☐"
    
    newline = "\n"
    br_tag = "<br>"
    description_travaux = autorisation.get("description_travaux", "").replace(newline, br_tag)
    horaire_debut = autorisation.get("horaire_debut", "")
    horaire_fin = autorisation.get("horaire_fin", "")
    lieu_travaux = autorisation.get("lieu_travaux", "")
    
    risques_potentiels = autorisation.get("risques_potentiels", "").replace(newline, br_tag)
    
    # Fonction helper pour afficher les mesures de sécurité
    def format_mesure(key):
        value = autorisation.get(key, "")
        if value == "FAIT":
            return '<span style="color: green; font-weight: bold;">✓ FAIT</span>'
        elif value == "A_FAIRE":
            return '<span style="color: orange; font-weight: bold;">⚠ À FAIRE</span>'
        else:
            return '<span style="color: gray;">-</span>'
    
    # Mesures de sécurité
    mesures_rows = f"""
        <tr><td>CONSIGNATION MAT. OU PIÈCE EN MOUV</td><td>{format_mesure("mesure_consignation_materiel")}</td></tr>
        <tr><td>CONSIGNATION ÉLECTRIQUE</td><td>{format_mesure("mesure_consignation_electrique")}</td></tr>
        <tr><td>DÉBRANCHEMENT FORCE MOTRICE</td><td>{format_mesure("mesure_debranchement_force")}</td></tr>
        <tr><td>VIDANGE APPAREIL/TUYAUTERIE</td><td>{format_mesure("mesure_vidange_appareil")}</td></tr>
        <tr><td>DÉCONTAMINATION/LAVAGE</td><td>{format_mesure("mesure_decontamination")}</td></tr>
        <tr><td>DÉGAZAGE</td><td>{format_mesure("mesure_degazage")}</td></tr>
        <tr><td>POSE JOINT PLEIN</td><td>{format_mesure("mesure_pose_joint")}</td></tr>
        <tr><td>VENTILATION FORCÉE</td><td>{format_mesure("mesure_ventilation")}</td></tr>
        <tr><td>ZONE BALISÉE</td><td>{format_mesure("mesure_zone_balisee")}</td></tr>
        <tr><td>CANALISATIONS ÉLECTRIQUES</td><td>{format_mesure("mesure_canalisations_electriques")}</td></tr>
        <tr><td>SOUTERRAINES BALISÉES</td><td>{format_mesure("mesure_souterraines_balisees")}</td></tr>
        <tr><td>ÉGOUTS ET CÂBLES PROTÉGÉS</td><td>{format_mesure("mesure_egouts_cables")}</td></tr>
        <tr><td>TAUX D'OXYGÈNE</td><td>{format_mesure("mesure_taux_oxygene")}</td></tr>
        <tr><td>TAUX D'EXPLOSIVITÉ</td><td>{format_mesure("mesure_taux_explosivite")}</td></tr>
        <tr><td>EXPLOSIMÈTRE EN CONTINU</td><td>{format_mesure("mesure_explosimetre")}</td></tr>
        <tr><td>ÉCLAIRAGE DE SÛRETÉ</td><td>{format_mesure("mesure_eclairage_surete")}</td></tr>
        <tr><td>EXTINCTEUR TYPE</td><td>{format_mesure("mesure_extincteur")}</td></tr>
        <tr><td>AUTRES</td><td>{format_mesure("mesure_autres")}</td></tr>
    """
    
    mesures_securite_texte = autorisation.get("mesures_securite_texte", "").replace(newline, br_tag)
    
    # EPI (checkboxes)
    epi_list = []
    if autorisation.get("epi_visiere"): epi_list.append("VISIÈRE")
    if autorisation.get("epi_tenue_impermeable"): epi_list.append("TENUE IMPERMÉABLE, BOTTES")
    if autorisation.get("epi_cagoule_air"): epi_list.append("CAGOULE AIR RESPIRABLE/ART")
    if autorisation.get("epi_masque"): epi_list.append("MASQUE TYPE")
    if autorisation.get("epi_gant"): epi_list.append("GANT TYPE")
    if autorisation.get("epi_harnais"): epi_list.append("HARNAIS DE SÉCURITÉ")
    if autorisation.get("epi_outillage_anti_etincelle"): epi_list.append("OUTILLAGE ANTI-ÉTINCELLE")
    if autorisation.get("epi_presence_surveillant"): epi_list.append("PRÉSENCE D'UN SURVEILLANT")
    if autorisation.get("epi_autres"): epi_list.append("AUTRES")
    
    epi_display = "<br>• ".join(epi_list) if epi_list else "Aucun EPI sélectionné"
    if epi_list:
        epi_display = "• " + epi_display
    
    equipements_protection_texte = autorisation.get("equipements_protection_texte", "").replace(newline, br_tag)
    
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
            font-size: 10pt;
            line-height: 1.3;
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
            font-size: 9pt;
        }}
        h1 {{
            text-align: center;
            font-size: 14pt;
            font-weight: bold;
            margin: 10px 0;
            text-transform: uppercase;
        }}
        .ref-box {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            border: 2px solid #000;
            padding: 6px;
            background: #f0f0f0;
        }}
        .ref-item {{
            font-size: 9pt;
            font-weight: bold;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 8px;
        }}
        th {{
            background-color: #e0e0e0;
            border: 1px solid #000;
            padding: 5px;
            font-weight: bold;
            text-align: left;
            font-size: 9pt;
        }}
        td {{
            border: 1px solid #000;
            padding: 5px;
            font-size: 9pt;
        }}
        .section-title {{
            background-color: #c0c0c0;
            border: 1px solid #000;
            padding: 5px;
            font-weight: bold;
            margin-top: 8px;
            font-size: 10pt;
        }}
        .field-label {{
            font-weight: bold;
            font-size: 9pt;
        }}
        .textarea-field {{
            min-height: 60px;
            vertical-align: top;
        }}
        .signature-section {{
            display: flex;
            justify-content: space-between;
            margin-top: 15px;
        }}
        .signature-box {{
            width: 48%;
            border: 1px solid #000;
            padding: 8px;
        }}
        .signature-title {{
            font-weight: bold;
            margin-bottom: 8px;
            text-align: center;
        }}
        .signature-line {{
            margin-top: 30px;
            border-top: 1px solid #000;
            padding-top: 4px;
            font-size: 8pt;
        }}
        .checkbox-group {{
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            padding: 8px;
        }}
        .checkbox-item {{
            display: flex;
            align-items: center;
            gap: 5px;
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

        <!-- Type de travaux -->
        <div class="section-title">TYPE DE TRAVAUX</div>
        <div class="checkbox-group">
            <div class="checkbox-item">
                <span style="font-size: 12pt;">{type_point_chaud}</span>
                <span>Par point chaud</span>
            </div>
            <div class="checkbox-item">
                <span style="font-size: 12pt;">{type_fouille}</span>
                <span>De fouille</span>
            </div>
            <div class="checkbox-item">
                <span style="font-size: 12pt;">{type_espace_clos}</span>
                <span>En espace clos ou confiné</span>
            </div>
            <div class="checkbox-item">
                <span style="font-size: 12pt;">{type_autre_cas}</span>
                <span>Autre cas</span>
            </div>
        </div>
        {f'<div style="padding: 8px; border: 1px solid #ddd; margin-top: 5px;"><strong>Précisions:</strong> {description_travaux}</div>' if description_travaux else ''}

        <!-- Horaires et lieu -->
        <table style="margin-top: 10px;">
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
                <td class="textarea-field">{risques_potentiels if risques_potentiels else "Aucun risque identifié"}</td>
            </tr>
        </table>

        <!-- Mesures de sécurité -->
        <div class="section-title">MESURES DE SÉCURITÉ</div>
        <table>
            <thead>
                <tr>
                    <th style="width: 70%;">MESURE</th>
                    <th style="width: 30%; text-align: center;">STATUT</th>
                </tr>
            </thead>
            <tbody>
                {mesures_rows}
            </tbody>
        </table>
        {f'<div style="padding: 8px; border: 1px solid #ddd; margin-top: 5px;"><strong>Précisions:</strong> {mesures_securite_texte}</div>' if mesures_securite_texte else ''}

        <!-- Équipements de protection -->
        <div class="section-title">ÉQUIPEMENTS DE PROTECTION INDIVIDUELLE (EPI)</div>
        <table>
            <tr>
                <td class="textarea-field">{epi_display}</td>
            </tr>
        </table>
        {f'<div style="padding: 8px; border: 1px solid #ddd; margin-top: 5px;"><strong>Précisions:</strong> {equipements_protection_texte}</div>' if equipements_protection_texte else ''}

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
