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


class MailchimpList(models.Model):
    _name = 'mailchimp.list'
    _description = 'Mailchimp list'

    name = fields.Char(string='Name')


class MailchimpConfig(models.Model):
    _name = 'mailchimp.config'
    _description = 'Mailchimp configuration'

    name = fields.Char(string='Name')
    mapi = fields.Char(string='API', required=True)
    subscription_list = fields.Char(string='Subscription List')

    # Abre el asitente para seleccionar una de las listas de suscripcion
    # disponibles
    @api.multi
    def button_change_list(self):
        cr, uid, context = self.env.args
        change_list = self.env['mailchimp.change.list'].create({})
        self.env['mailchimp.change.list'].action_get_lists()

        return {
            'name': 'Subscription lists',
            'type': 'ir.actions.act_window',
            'res_model': 'mailchimp.change.list',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': change_list.id,
            'nodestroy': True,
            'target': 'new',
            'context': context,
        }

    # Obtener la lista de subscriptores de la configuracion
    def get_subscription_list_id(self, mapi):
        # Comprobar si hay algun registro
        mailchimps = self.env['mailchimp.config'].search([])

        if len(mailchimps) > 0:
            subscription_list_name = mailchimps[0].subscription_list
            try:
                # Obtener las listas de subscripcion
                lists = mapi.lists.list()
            except:
                raise exceptions.Warning(
                    _('Data error Mailchimp connection, review the '
                      'Mailchimp/Configuration menu.'))

            # Inicializar por si no la encuentra
            list_id = 0

            for l in lists['data']:
                if l['name'] == subscription_list_name:
                    list_id = l['id']
                    break
            if list_id == 0:
                raise exceptions.Warning(
                    _('The list \'%s\' does not exist in Mailchimp.' %
                        (subscription_list_name)))
            return list_id
        else:
            raise exceptions.Warning(_(
                'You must define a configuration for your Mailchimp account.'))

    # Comprueba si conecta o no
    @api.one
    def is_connected(self):
        # Conectar
        mapi = mailchimp.Mailchimp(self.mapi)

        # Siempre conecta, pero para saber si los datos de la API o la lista de
        # suscripcion son correctos, necesitamos hacer las siguientes
        # comprobaciones
        try:
            # Obtener las listas de subscripcion
            mapi.lists.list()
            # Obtener las lista de subscripcion definida en la configuracion
            self.get_subscription_list_id(mapi)
        except:
            raise exceptions.Warning(
                _('Data error Mailchimp connection, review the '
                  'Mailchimp/Configuration menu.'))

        return True

    @api.one
    def test_connect(self):
        res = self.is_connected()
        if res:
            raise exceptions.Warning(
                _('The connection was made successfully.'))
        return True
