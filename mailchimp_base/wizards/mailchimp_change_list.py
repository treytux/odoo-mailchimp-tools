# -*- coding: utf-8 -*-
###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2014-Today Trey, Kilobytes de Soluciones <www.trey.es>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from openerp import models, fields, api, _, exceptions
import mailchimp

import logging

_log = logging.getLogger(__name__)


class MailchimpChangeList(models.TransientModel):
    _name = 'mailchimp.change.list'
    _description = 'Mailching change list'

    name = fields.Char(string='Emmpty')
    subscription_list_id = fields.Many2one(
        comodel_name='mailchimp.list',
        string='Subscription list',
        help="Available lists MailChimp API.")

    # Cargar listas de suscripcion disponibles
    def action_get_lists(self):
        # Buscar config mailchimp
        mailchimps = self.env['mailchimp.config'].search([])
        if mailchimps:
            # Siempre conecta, pero para saber si los datos de la API o la
            # lista de suscripcion son correctos, necesitamos ejecutar las
            # siguientes funciones
            try:
                # Conectar
                mapi = mailchimp.Mailchimp(mailchimps[0].mapi)

                # Eliminar los registros de la tabla por si las listas han
                # cambiado
                mailchimp_lists = self.env['mailchimp.list'].search([])
                for mailchimp_list in mailchimp_lists:
                    mailchimp_list.unlink()

                # Obtener las listas de subscripcion
                lists = mapi.lists.list()
                _log.info('.'*100)
                _log.info('lists: %s' % lists)

                # Crear registros de listas
                for l in lists['data']:
                    data = {
                        'name': l['name'],
                    }
                    self.env['mailchimp.list'].create(data)
            except:
                raise exceptions.Warning(_('Data error Mailchimp connection.'))

        else:
            raise exceptions.Warning(_(
                'Not exists configuration of Mailchimp in the system.\n'
                'Make sure you have saved the settings.'))

    # Escribir la lista seleccionada en el campo lista de suscripcion de la
    # configuracion
    @api.one
    def button_accept(self):
        # Buscar config mailchimp
        mailchimps = self.env['mailchimp.config'].search([])
        if mailchimps:
            record = self.env['mailchimp.config'].browse(mailchimps[0].id)
            record.write({'subscription_list': self.subscription_list_id.name})
        else:
            raise exceptions.Warning(_(
                'Not exists configuration of Mailchimp in the system.\n'
                'Make sure you have saved the settings.'))

        return {'type': 'ir.actions.act_window_close'}
