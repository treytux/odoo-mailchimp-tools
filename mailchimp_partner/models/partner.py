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
from openerp import models, fields, api
import mailchimp

import logging
_log = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create(self, data):
        partner_id = super(Partner, self).create(data)

        # Comprobar si existe configuracion para mailchimp,
        mailchimp_configs = self.env['mailchimp.config'].search([])
        if not mailchimp_configs:
            _log.warning('Not exists configuration of Mailchimp in the system.'
                         'Make sure you have saved the settings.')
        else:
            # @ TODO Comprobar la configuracion de los datos a exportar
            # export = False
            # if 'email' in data:
            #     if 'customer' in data and mailchimp_configs[0].customers:
            #         if ''
            #         export = True
            #     if 'supplier' in data and mailchimp_configs[0].suppliers:
            #         export = True

            ### @TODO Por ahora exportar solo los clientes (sean o no empresa)
            if data.get('email') and\
               'customer' in data and data['customer'] is True:

                # Conectar con MailChimp
                mapi = mailchimp.Mailchimp(mailchimp_configs[0].mapi)

                # Datos para crear el suscriptor
                data_email = {
                    'email': data['email'],
                }
                vals = {
                    'fname': data.get('name', ''),
                    # @TODO
                    # Cambiar porque no hay campo especifico para el apellido
                    'apellidos': data.get('name', ''),
                }
                # Obtener la lista
                list_id = self.env['mailchimp.config'].getListId(
                    mapi,
                    mailchimp_configs[0].subscription_list)

                # Crear el suscriptor
                self.env['mailchimp.config'].createSubscriptor(
                    mapi,
                    list_id,
                    data_email,
                    vals)
            else:
                _log.error('The customer has no email address associated, it '
                           'is omitted.')

        return partner_id

    @api.multi
    def write(self, vals):
        # Comprobar si existe configuracion para mailchimp,
        mailchimp_configs = self.env['mailchimp.config'].search([])
        if not mailchimp_configs:
            _log.warning('Not exists configuration of Mailchimp in the system.'
                         'Make sure you have saved the settings.')
        else:
            # Conectar con MailChimp
            mapi = mailchimp.Mailchimp(mailchimp_configs[0].mapi)

            # Email antiguo
            data_email = {
                'email': self.email,
            }
            # Datos modificados
            data_updated = {
                'fname': vals.get('name') or self.name,
            }

            # Si se modifica el correo, almacenamos el nuevo valor
            if vals.get('email'):
                data_updated.update({'new-email': vals.get('email')})

            # Obtener la lista
            list_id = self.env['mailchimp.config'].getListId(
                mapi,
                mailchimp_configs[0].subscription_list)

            # Actualizar suscriptor
            self.env['mailchimp.config'].updateSubscriptor(
                mapi,
                list_id,
                data_email,
                data_updated)

        res = super(Partner, self).write(vals)
        return res

    @api.multi
    def unlink(self):
        # Comprobar si existe configuracion para mailchimp,
        mailchimp_configs = self.env['mailchimp.config'].search([])
        if not mailchimp_configs:
            _log.warning('Not exists configuration of Mailchimp in the system.'
                         'Make sure you have saved the settings.')
        else:
            # Conectar con MailChimp
            mapi = mailchimp.Mailchimp(mailchimp_configs[0].mapi)

            if self.email:
                data_email = {
                    'email': self.email,
                }

                # Obtener la lista
                list_id = self.env['mailchimp.config'].getListId(
                    mapi,
                    mailchimp_configs[0].subscription_list)

                # Eliminar suscriptor
                self.env['mailchimp.config'].deleteSubscriptor(
                    mapi,
                    list_id,
                    data_email)

        return super(Partner, self).unlink()



