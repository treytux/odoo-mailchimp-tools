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


class MailchimpMapLine(models.Model):
    _name = 'mailchimp.map.line'
    _description = 'Mailchimp map line'

    name = fields.Char(string='Name')
    config_id = fields.Many2one(
        comodel_name='mailchimp.config',
        string='Configuration')
    field_odoo = fields.Char(string='Field Odoo')
    field_mailchimp = fields.Char(string='Field MailChimp')


class MailchimpConfig(models.Model):
    _name = 'mailchimp.config'
    _description = 'Mailchimp configuration'

    name = fields.Char(string='Name')
    mapi = fields.Char(string='API', required=True)
    subscription_list = fields.Char(string='Subscription List')
    map_line_ids = fields.One2many(
        comodel_name='mailchimp.map.line',
        inverse_name='config_id',
        string='Map lines')

    # Abre el asistente para seleccionar una de las listas de suscripcion
    # disponibles
    @api.multi
    def buttonChangeList(self):
        cr, uid, context = self.env.args
        change_list = self.env['mailchimp.change.list'].create({})
        self.env['mailchimp.change.list'].actionGetLists()

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
    def getSubscriptionListId(self, mapi):
        # Obtener configuracion
        mailchimp_config = self.getConfiguration()

        if len(mailchimp_config) > 0:
            subscription_list_name = mailchimp_config.subscription_list
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
    def isConnected(self):
        # Conectar
        mapi = self.connect()

        # Siempre conecta, pero para saber si los datos de la API o la lista de
        # suscripcion son correctos, necesitamos hacer las siguientes
        # comprobaciones
        try:
            # Obtener las lista de subscripcion definida en la configuracion
            self.getSubscriptionListId(mapi)
        except:
            raise exceptions.Warning(
                _('Data error Mailchimp connection, review the '
                  'Mailchimp/Configuration menu.'))

        return True

    @api.one
    def testConnect(self):
        res = self.isConnected()
        if res:
            raise exceptions.Warning(
                _('The connection was made successfully.'))
        return True

    @api.model
    def create(self, data):
        # Comprobar que solo hay un registro de configuracion de mailchimp
        if len(self.env['mailchimp.config'].search([])) >= 1:
            raise exceptions.Warning(
                _('There can be only one configuration of Mailchimp in the '
                    'system.'))
        return super(MailchimpConfig, self).create(data)

    ########################################################################
    # Funciones necesarias para las operaciones con la API de Mailchimp
    ########################################################################
    # Obtener listas diponibles
    def getLists(self, mapi):
        return mapi.lists.list()

    # Comprueba si la lista existe
    def existsList(self, mapi, list_name):
        for l in self.getLists(mapi)['data']:
            if l['name'] == list_name:
                return True
        _log.error(_('The list does %s not exist.' % list_name))

    # Devuelve el id de una lista
    def getListId(self, mapi, list_name):
        self.existsList(mapi, list_name)
        for l in self.getLists(mapi)['data']:
            if l['name'] == list_name:
                return l['id']
        return 0

    # Obtener configuracion de MailChimp
    def getConfiguration(self):
        # Comprobar si existe configuracion para mailchimp
        mailchimp_configs = self.env['mailchimp.config'].search([])
        if not mailchimp_configs:
            _log.warning(
                _('Not exists configuration of Mailchimp in the system.'
                  'Make sure you have saved the settings.'))
        return mailchimp_configs[0]

    # Conecta con MailChimp
    def connect(self):
        try:
            # Obtener configuracion
            mailchimp_config = self.getConfiguration()
            # Conectar
            mapi = mailchimp.Mailchimp(mailchimp_config.mapi)
        except:
            raise exceptions.Warning(_('Connection error.'))
        return mapi

    # Comprueba si hay que exportar los datos del partner basandose en los
    # datos de configuracion
    def checkExportData(self, partner):
        # Comprobar si tiene cporreo
        if not partner.email:
            return False

        # Obtener configuracion
        mailchimp_config = self.getConfiguration()

        # Customers: customer and is_company
        if mailchimp_config.customers is True and partner.customer is True \
           and partner.is_company is True:
            return True

        # Suppliers: suppliers and is_company
        if mailchimp_config.suppliers is True and partner.supplier is True \
           and partner.is_company is True:
            return True

        # Customer contacts: customer and not is_company
        if mailchimp_config.customer_contacts is True \
           and partner.customer is True and partner.is_company is False:
            return True

        # Supplier contacts: supplier and not is_company
        if mailchimp_config.supplier_contacts is True \
           and partner.supplier is True and partner.is_company is False:
            return True

        return False

    # Comprueba si un id de mailchimp (leid) esta dado de alta en una lista
    def existLeid(self, leid):
        # Conectar
        mapi = self.connect()
        # Obtener configuracion
        mailchimp_config = self.getConfiguration()

        # Obtener id de la lista
        list_id = self.env['mailchimp.config'].getListId(
            mapi, mailchimp_config.subscription_list)

        data_clients = mapi.lists.members(list_id)
        if 'data' in data_clients:
            for c in data_clients['data']:
                if leid == c['leid']:
                    return True
        return False


    # Crear un suscriptor en una lista a partir de un correo
    def createSubscriptor(self, email, vals):
        # Conectar con MailChimp
        mapi = self.connect()

        # Obtener configuracion
        mailchimp_config = self.getConfiguration()

        # Obtener id de la lista
        list_id = self.env['mailchimp.config'].getListId(
            mapi, mailchimp_config.subscription_list)

        # double_optin=False: para que no pida confirmacion al usuario para
        # crear la subscripcion
        try:
            res = mapi.lists.subscribe(
                list_id, {'email': email}, vals, double_optin=False,
                update_existing=True)
            _log.info(_('%s updated to %s in the list: %s' % (
                {'email': email}, vals, list_id)))
            return res
        except mailchimp.ListAlreadySubscribedError:
            raise exceptions.Warning(
                _('Another subscriber already exists in this list with the '
                  'same email.'))
        except mailchimp.ListMergeFieldRequiredError:
            raise exceptions.Warning(_('The email address is not valid.'))
        else:
            raise exceptions.Warning(_('Unknown error.'))


    # Actualizar un suscriptor en una lista a partir de leid
    def updateSubscriptor(self, leid, vals):
        # Conectar con MailChimp
        mapi = self.connect()

        # Obtener configuracion
        mailchimp_config = self.getConfiguration()

        # Obtener id de la lista
        list_id = self.env['mailchimp.config'].getListId(
            mapi, mailchimp_config.subscription_list)

        # double_optin=False: para que no pida confirmacion al usuario para
        # crear la subscripcion
        try:
            res = mapi.lists.subscribe(
                list_id, {'leid': leid}, vals, double_optin=False,
                update_existing=True)
            _log.info(_('%s updated to %s in the list: %s' % (
                {'leid': leid}, vals, list_id)))
            return res
        except mailchimp.ListAlreadySubscribedError:
            raise exceptions.Warning(
                _('Another subscriber already exists in this list with the '
                  'same email.'))
        except mailchimp.ListMergeFieldRequiredError:
            raise exceptions.Warning(_('The email address is not valid.'))
        # Si han borrado desde mailchimp el registro, en odoo sigue existiendo
        except mailchimp.EmailNotExistsError:
            raise exceptions.Warning(
                _('There is no record of an email address with leid %s on '
                  'that list.' % leid))
        else:
            raise exceptions.Warning(_('Unknown error.'))

    # Eliminar un suscriptor en una lista a partir de leid
    def deleteSubscriptor(self, leid):
        # Conectar con MailChimp
        mapi = self.connect()

        # Obtener configuracion
        mailchimp_config = self.getConfiguration()

        # Obtener id de la lista
        list_id = self.env['mailchimp.config'].getListId(
            mapi, mailchimp_config.subscription_list)

        # delete_member=True Para que lo elimine
        # send_goodbye=False Para que no envie correo de despedida
        # send_notify=False Para que no envie correo de notificacion
        try:
            res = mapi.lists.unsubscribe(
                list_id, {'leid': leid}, delete_member=True,
                send_goodbye=False, send_notify=False)
            _log.info(_('%s deleted in the list %s' % (
                {'leid': leid}, list_id)))
            return res
        except mailchimp.EmailNotExistsError:
            _log.warn(
                _('The leid %s is not suscribed in the list, it can not '
                  'eliminated.' % {'leid': leid}))
        else:
            raise exceptions.Warning(_('Unknown error.'))
