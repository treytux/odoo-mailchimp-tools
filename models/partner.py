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


# class Partner(models.Model):
#     _inherit = 'res.partner'

#     @api.model
#     def create(self, data):
#         partner_id = super(Partner, self).create(data)

#         #####
#         #
#         #####
#         # Comprobar si es cliente (o contacto) y esta activo

#         # Si tiene relleno el campo email, comprobar si ya existe en la lista
#         # de mailchimp.

#         # Si existe, actualizar campos del suscriptor
#         # Si no existe, crear suscriptor
#         if 'email' in data:
#         #     picking_obj = self.env['stock.picking']
#         #     picking = picking_obj.browse(data['picking_id'])
#         #     picking._calc_breakdown_taxes()
#         # return partner_id


#         partner = self.pool.get('res.partner').browse(cr, uid, id, context=context)
#         if partner.customer is True:
#             ## Conectar con MailChimp
#             mapi = self.pool.get('trey.mailchimp').connect(cr, uid)

#             ## Crear subscriptor con los datos

#             # Comprobar si el cliente tiene un contacto creado y este contiene un email. Si es asi, se dara de alta en MailChimp el cliente con ese correo
#             # Leer el email del contacto
#             contact_ids = self.pool.get('res.partner.contact').search(cr, uid, [('partner_id', '=', id)])
#             if contact_ids != []:
#                 contact = self.pool.get('res.partner.contact').browse(cr, uid, contact_ids[0], context=context)

#                 email = contact.email or ''

#                 if email != '':
#                     data_subscribe = {
#                         "email": email,
#                     }

#                     language = self.get_language_name(cr, uid, contact)
#                     aniversary = format_mm_dd(contact.birthdate)
#                     initdate = format_mm_dd_yyyy(partner.date)

#                     # Las keys del diccionario son los nombres de los campos en MailChimp
#                     # Para evitar errores fijarse en List Fileds and MERGE tags (del menu de COnfiguracion), no en los campos del formulario
#                     merge_vars = {
#                         "fname": contact.first_name or '',
#                         "lname": contact.last_name or '',
#                         "aniversary": aniversary or '',
#                         "initdate": initdate or '',
#                         "language": language,
#                     }

#                     ## Obtener el id de la lista
#                     subscription_list_id = self.pool.get('trey.mailchimp').get_subscription_list_id(cr, uid, mapi)

#                     ## Subcribir en esa lista
#                     try:
#                         # double_optin=False: para que no pida confirmacón al usuario para crear la subscripcion
#                         mapi.lists.subscribe(subscription_list_id, data_subscribe, merge_vars, double_optin=False)
#                     except mailchimp.ListAlreadySubscribedError:
#                         raise osv.except_osv('Error', 'Ya existe otro suscriptor en esta lista con el mismo correo.')
#                     except mailchimp.ListMergeFieldRequiredError:
#                         raise osv.except_osv('Error', 'La direccion de correo no es valida.')

