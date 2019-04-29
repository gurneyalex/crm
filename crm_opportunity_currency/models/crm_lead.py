# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    customer_currency_id = fields.Many2one(
        string='Customer currency',
        comodel_name='res.currency',
        default=lambda self: self.env.user.company_id.currency_id,
    )
    amount_customer_currency = fields.Monetary(
        string='Customer amount',
        currency_field='customer_currency_id',
        store=True,
    )
    is_same_currency = fields.Boolean(
        string='Same currency',
        compute='_compute_is_same_currency',
    )

    @api.onchange('customer_currency_id', 'amount_customer_currency')
    def _onchange_currency(self):
        for lead in self:
            lead.planned_revenue = lead.get_revenue_in_company_currency()

    @api.multi
    def get_revenue_in_company_currency(self):
        """Compute the planned revenue in the company currency.

        If the customer currency is different than the company currency,
        the planned revenue is computed in the company currency.
        """
        self.ensure_one()
        if self.is_same_currency:
            return self.planned_revenue
        return self.customer_currency_id._convert(
            self.amount_customer_currency or 0,
            self.company_currency,
            self.env.user.company_id,
            fields.Datetime.now(),
        )

    @api.multi
    def _compute_is_same_currency(self):
        for lead in self:
            lead.is_same_currency = (
                lead.customer_currency_id == lead.company_currency
            )

    @api.multi
    def write(self, vals):
        res = super().write(vals)
        if (
            'customer_currency_id' in vals
            or 'amount_customer_currency' in vals
        ):
            # Due to the readonly in the view the compute does not work
            for lead in self:
                lead.write({
                    'planned_revenue': lead.get_revenue_in_company_currency()
                })
        return res
