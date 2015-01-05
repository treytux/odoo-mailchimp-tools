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

    # Abre el asitente para seleccionar una de las listas de suscripcion
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
    def isConnected(self):
        # Conectar
        mapi = mailchimp.Mailchimp(self.mapi)

        # Siempre conecta, pero para saber si los datos de la API o la lista de
        # suscripcion son correctos, necesitamos hacer las siguientes
        # comprobaciones
        try:
            # Obtener las listas de subscripcion
            mapi.lists.list()
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
        _log.error('The list does %s not exist.' % list_name)

    # Devuelve el id de una lista
    def getListId(self, mapi, list_name):
        self.existsList(mapi, list_name)
        for l in self.getLists(mapi)['data']:
            if l['name'] == list_name:
                return l['id']
        return 0

    # Crear un suscriptor en una lista
    def createSubscriptor(self, mapi, list_id, data_email, vals):
        # double_optin=False: para que no pida confirmacion al usuario para
        # crear la subscripcion
        try:
            res = mapi.lists.subscribe(
                list_id, data_email, vals, double_optin=False)
            _log.info('%s subscribed to the list %s with values: %s' % (
                data_email, list_id, vals))
            return res
        except mailchimp.ListAlreadySubscribedError:
            raise exceptions.Warning(
                _('Another subscriber already exists in this list with the '
                  'same email.'))
        except mailchimp.ListMergeFieldRequiredError:
            raise exceptions.Warning(_('The email address is not valid.'))
        else:
            raise exceptions.Warning(_('Unknown error.'))

    # Actualizar un suscriptor en una lista
    def updateSubscriptor(self, mapi, list_id, data_email, vals):
        # double_optin=False: para que no pida confirmacion al usuario para
        # crear la subscripcion
        try:
            res = mapi.lists.subscribe(
                list_id, data_email, vals, double_optin=False,
                update_existing=True)
            _log.info('%s updated to %s in the list: %s' % (
                data_email, vals, list_id))
            return res
        except mailchimp.ListAlreadySubscribedError:
            raise exceptions.Warning(
                _('Another subscriber already exists in this list with the '
                  'same email.'))
        except mailchimp.ListMergeFieldRequiredError:
            raise exceptions.Warning(_('The email address is not valid.'))
        else:
            raise exceptions.Warning(_('Unknown error.'))

    # Eliminar un suscriptor en una lista
    def deleteSubscriptor(self, mapi, list_id, data_email):
        # delete_member=True Para que lo elimine
        # send_goodbye=False Para que no envie correo de despedida
        # send_notify=False Para que no envie correo de notificacion
        try:
            res = mapi.lists.unsubscribe(
                list_id, data_email, delete_member=True, send_goodbye=False,
                send_notify=False)
            _log.info('%s deleted in the list %s' % (data_email, list_id))
            return res
        except mailchimp.EmailNotExistsError:
            # raise exceptions.Warning(
            #     _('The email %s is not suscribed in the list, it can not '
            #       'eliminated.' % data_email))
            _log.warn('The email %s is not suscribed in the list, it can not '
                      'eliminated.' % data_email)
        else:
            raise exceptions.Warning(_('Unknown error.'))
