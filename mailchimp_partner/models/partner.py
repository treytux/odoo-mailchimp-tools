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

    # Comprueba si hay que exportar los datos del partner basandose en los
    # datos de configuracion
    def checkExportData(self, mailchimp_config, partner):
        export = False

        # Customers: customer and is_company
        if mailchimp_config.customers is True and partner.customer is True \
           and partner.is_company is True:
            export = True

        # Suppliers: suppliers and is_company
        if mailchimp_config.suppliers is True and partner.supplier is True \
           and partner.is_company is True:
            export = True

        # Customer contacts: customer and not is_company
        if mailchimp_config.customer_contacts is True \
           and partner.customer is True and partner.is_company is False:
            export = True

        # Supplier contacts: supplier and not is_company
        if mailchimp_config.supplier_contacts is True \
           and partner.supplier is True and partner.is_company is False:
            export = True

        return export

    @api.model
    def create(self, data):
        partner = super(Partner, self).create(data)

        # Comprobar si existe configuracion para mailchimp,
        mailchimp_configs = self.env['mailchimp.config'].search([])
        if not mailchimp_configs:
            _log.warning('Not exists configuration of Mailchimp in the system.'
                         'Make sure you have saved the settings.')
        else:
            if data.get('email'):
                # Conectar con MailChimp
                mapi = mailchimp.Mailchimp(mailchimp_configs[0].mapi)

                # Comprobar si hay que exportar los datos
                if self.checkExportData(mailchimp_configs[0], partner):
                    # Datos para crear el suscriptor
                    data_email = {
                        'email': data['email'],
                    }

                    # Obtener los valores de las lineas de mapeo de la config
                    vals = {}
                    for map_line in mailchimp_configs.map_line_ids:
                        vals[map_line.field_mailchimp] = data.get(
                            map_line.field_odoo, '')

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

        return partner

    @api.multi
    def write(self, vals):
        # Comprobar si existe configuracion para mailchimp
        mailchimp_configs = self.env['mailchimp.config'].search([])
        if not mailchimp_configs:
            _log.warning('Not exists configuration of Mailchimp in the system.'
                         'Make sure you have saved the settings.')
        else:
            # Conectar con MailChimp
            mapi = mailchimp.Mailchimp(mailchimp_configs[0].mapi)

            # Obtener la lista
            list_id = self.env['mailchimp.config'].getListId(
                mapi,
                mailchimp_configs[0].subscription_list)

            # Comprobar si hay que exportar los datos
            if self.checkExportData(mailchimp_configs[0], self):

                # Si ya tenia asignado un correo, se actualiza el suscriptor
                if self.email:
                    # Email antiguo
                    data_email = {
                        'email': self.email,
                    }
                    # # Datos modificados
                    # data_updated = {
                    #     'fname': vals.get('name') or self.name,
                    # }
                    # Obtener los valores modificados de las lineas de mapeo de
                    # la configuracion
                    data_updated = {}
                    for map_line in mailchimp_configs.map_line_ids:

                        # @TODO
                        # Como obtengo self.name (en general self.<field_odoo>)
                        # para asignar el valor antiguo si no viene el nuevo??
                        # Si no hago eso, se borraran los valores que no haya
                        # modificado esta vez
                        # 'fname': vals.get('name') or self.name,
                        data_updated[map_line.field_mailchimp] = vals.get(
                            map_line.field_odoo, '') ## or eval(self.vals.get(map_line.field_odoo, ''))

                    # Si se modifica el correo, almacenamos el nuevo valor
                    if vals.get('email'):
                        data_updated.update({'new-email': vals.get('email')})

                    # Actualizar suscriptor
                    self.env['mailchimp.config'].updateSubscriptor(
                        mapi,
                        list_id,
                        data_email,
                        data_updated)

                # Si no tenia asignado correo, hay que comprobar si ha
                # insertado algun correo o no
                else:

                    # Si ha insertado correo, hay que crear el suscriptor
                    if vals.get('email'):
                        # Datos para crear el suscriptor
                        data_email = {
                            'email': vals.get('email'),
                        }

                        # Obtener los valores de las lineas de mapeo de la config
                        vals = {}
                        for map_line in mailchimp_configs.map_line_ids:
                            vals[map_line.field_mailchimp] = vals.get(
                                map_line.field_odoo, '')

                        # Crear el suscriptor
                        self.env['mailchimp.config'].createSubscriptor(
                            mapi,
                            list_id,
                            data_email,
                            vals)

                    # Si elimina el correo sin sustituirlo, eliminar el
                    # suscriptor en Mailchimp
                    else:
                        if self.email:
                            data_email = {
                                'email': self.email,
                            }

                            # Eliminar suscriptor
                            self.env['mailchimp.config'].deleteSubscriptor(
                                mapi,
                                list_id,
                                data_email)
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

            # Comprobar si hay que exportar los datos
            if self.checkExportData(mailchimp_configs[0], self):
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
