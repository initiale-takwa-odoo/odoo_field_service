from odoo import models, fields, api
from odoo.exceptions import ValidationError

class FieldService(models.Model):
    _name = 'field.service'
    _description = 'Intervention à faire'
    _inherit = ['mail.thread'] # 🌟 ON INJECTE LE MOTEUR DE MESSAGERIE ICI
    _order = 'time_slot asc'

    name = fields.Char(string='Nom de l\'Intervenant', required=True)
        # 🔢 Le numéro unique de l'intervention (généré par la séquence)
    code = fields.Char(string='Numéro d\'intervention', required=True, copy=False, readonly=True, default=lambda self: 'Nouveau')
    name1 = fields.Char(string='Nom de chantier')
    is_done = fields.Boolean(string='Chantier Clôturé ?', default=False, readonly=True)
    time_slot = fields.Char(string="Plage horaire")
    deadline = fields.Date(string='Date limite')
        # 💰 Le montant financier de l'intervention (Hors Taxes)
    price_subtotal = fields.Float(string='Montant HT', default=0.0, currency_field='currency_id', # 🌟 LIEN DE SÉCURITÉ MONÉTAIRE
                                  help="Saisissez le prix facturé pour cette intervention")
        # 🪙 Champ technique de Devise (Multi-currency)
        # 🪙 La devise devient un choix libre sur la fiche !
    currency_id = fields.Many2one(
        'res.currency', 
        string='Devise', 
        required=True,
        default=lambda self: self.env.company.currency_id
    )

    start_datetime = fields.Datetime(string="Date/Heure de début", readonly=True)
    worker_comment = fields.Text(string="Commentaire de fin de chantier")

    # 👤 Liaison Client & Sous-tâches
    partner_id = fields.Many2one('res.partner', string="Client concerné")
    partner_phone = fields.Char(string="Téléphone du client", related="partner_id.phone", readonly=True)
    partner_email = fields.Char(string="Email du client", related="partner_id.email", readonly=True)
    # 🏢 LIAISON MULTI-SOCIÉTÉS
    # Odoo prendra automatiquement la société actuelle de l'utilisateur comme valeur par défaut
    company_id = fields.Many2one(
        'res.company', 
        string='Société', 
        required=True, 
        default=lambda self: self.env.company
    )
    subtask_ids = fields.One2many('field.subtask', 'task_id', string='Sous-tâches')

    # 📅 Planification & Catégories
    day = fields.Selection([
        ('monday', 'Lundi'), ('tuesday', 'Mardi'), ('wednesday', 'Mercredi'),
        ('thursday', 'Jeudi'), ('friday', 'Vendredi'), ('saturday', 'Samedi'),
        ('sunday', 'Dimanche'), ('anytime', 'Toute la semaine')
    ], string='Jour', required=True, default='monday')

    category = fields.Selection([
        ('ins', 'Installation 🛠️'),
        ('ec', 'Entretien courant 🪛'),
        ('du', 'Dépannage d\'urgence 🚨'),
        ('R', 'Réparation 🔧'),
    ], string='Type d\'Intervention', default='ins', required=True)

    priority = fields.Selection([('0', 'Normale'), ('1', 'Urgent ⭐')], string='Priorité', default='0')
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('in_progress', 'En Cours 🛠️'),
        ('paused', 'En Pause ⏸️'),
        ('done', 'Terminé 🎉')
    ], string="Statut", default='draft', readonly=True ,tracking=True) # 🌟 SUIVI AUTOMATIQUE DU WORKFLOW

    # 📊 Le compteur de sous-tâches
    remaining_subtasks_count = fields.Integer(string="Sous-tâches restantes", compute="_compute_remaining_subtasks")



    @api.depends('subtask_ids.is_done')
    def _compute_remaining_subtasks(self):
        for record in self:
            remaining = record.subtask_ids.filtered(lambda s: not s.is_done)
            record.remaining_subtasks_count = len(remaining)

    # 🚀 LES BOUTONS MANUELS DU WORKFLOW (ÉCRITURE STRICTE EN BASE DE DONNÉES)
    def action_start_task(self):
        for record in self:
            record.state = 'in_progress'
            record.start_datetime = fields.Datetime.now()


    def action_paused_task(self):
        for record in self:
            if record.state == 'in_progress':
                record.state = 'paused'

    def action_resume_task(self):
        for record in self:
            if record.state == 'paused':
                record.state = 'in_progress'

    # 🎉 LE VRAI BOUTON DE CLÔTURE DE WORKFLOW ODOO
    def action_complete_task(self):
        for record in self:
            if record.remaining_subtasks_count > 0:
                raise ValidationError(
                    f"🛑 Action impossible ! Il vous reste encore {record.remaining_subtasks_count} sous-tâche(s) à accomplir."
                )
            record.is_done = True
            record.state = 'done'

    # 🔄 LE BOUTON ANNULER / MARCHE ARRIÈRE (ERREUR HUMAINE)
    def action_cancel_completion(self):
        for record in self:
            # 🌟 SÉCURITÉ ANCIENS CHANTIERS : Si la fiche est restée sur "Nouveau", on lui donne son numéro !
                if record.code == 'Nouveau' or not record.code:
                    record.code = self.env['ir.sequence'].next_by_code('field.service') or 'Nouveau'
                record.is_done = False
                record.state = 'in_progress'

        # 🔢 SÉQUENCE AUTOMATIQUE CORRIGÉE (CODE : field.service)
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', 'Nouveau') == 'Nouveau':
                # 🌟 ICI : On met 'field.service' pour correspondre exactement à votre base !
                vals['code'] = self.env['ir.sequence'].next_by_code('field.service') or 'Nouveau'
        
        return super(FieldService, self).create(vals_list)


     # ✉️ BOUTON ENVOI EMAIL AUTOMATISÉ CONFORME ODOO 19
    def action_send_intervention_email(self):
        self.ensure_one()
        template_id = self.env.ref('odoo_field_service.email_template_field_service').id
        
        # 🌟 LOGIQUE CORRIGÉE : On prend la langue de l'utilisateur connecté (l'application)
        user_lang = self.env.user.lang or 'en_US'
        
        ctx = {
            'default_model': 'field.service',
            'default_res_ids': [self.id],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'force_email': True,
            # 🌟 ON FORCE LA LANGUE DE L'UTILISATEUR 'lang': user_lang,
        }
        
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            # 🌟 TRÈS IMPORTANT : On force l'environnement du wizard dans la langue de l'utilisateur
            'context': self.with_context(lang=user_lang).env.context | ctx,
        }

    
  




class FieldSubtask(models.Model):
    _name = 'field.subtask'
    _description = 'Sous-tâche Technique'

    name = fields.Char(string='Nom de la sous-tâche', required=True)
    is_done = fields.Boolean(string='Fait ?', default=False)
    task_id = fields.Many2one('field.service', string='Intervention principale', ondelete='cascade')
