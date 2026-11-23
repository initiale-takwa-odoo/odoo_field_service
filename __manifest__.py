{
    # 'name': 'Gestion des Interventions',
    'name': 'Field service management',
    'version': '1.0',
    'category': 'Services',
    'author': 'Ajili takwa (Ingénieur)',
    'summary': 'Gestion des Interventions Techniques sur le Terrain',
     'depends': [
        'base', 
        'web',
        'mail' # 🌟 LE LIEN MAGIQUE AVEC LE SERVEUR DE MESSAGERIE D'ODOO
    ],

            'data': [
        # 1. LA SÉCURITÉ EN PREMIER 🛡️ (Pour créer les règles et les groupes)
        'security/field_service_security.xml',  
        
        # 2. LES ACCÈS DES TABLES EN DEUXIÈME 📋 (S'appuie sur la sécurité ci-dessus)
        'security/ir.model.access.csv',
        
        # 3. LES DONNÉES TECHNIQUES COMPOSANTES ⚙️ (Séquences de numérotation)
        'data/field_service_sequence.xml',
        
        # 4. L'INTERFACE GRAPHIQUE 🎨 (Les menus, formulaires et listes pour les utilisateurs)
        'views/field_service_view.xml', 
        
        # 5. LA LOGIQUE DE COMMUNICATION 📧 (Les modèles d'emails basés sur les vues/champs)
        'data/mail_template_data.xml',  
        
        # 6. LES IMPRESSIONS EN DERNIER 📄 (Les rapports PDF qui impriment les données des vues)
        'report/field_service_report.xml',
    ],



    'installable': True, 
    'application': True,
}


