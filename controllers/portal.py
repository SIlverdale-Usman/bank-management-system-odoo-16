from odoo.addons.portal.controllers.portal import CustomerPortal, pager
from odoo.http import request
from odoo import http, _
from odoo.tools import groupby as groupbyelem
from operator import itemgetter


class ClientPortal(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        res = super(ClientPortal, self)._prepare_home_portal_values(counters)
        res["ticket_counts"] = request.env["bank.complaint"].search_count([])
        return res

    @http.route(['/my/tickets', '/my/tickets/page/<int:page>'], type='http', auth="user", website=True)
    def ticket_list_view(self, page=1, sortby='id', search="", search_in="All", groupby="none", **kw):
        if not groupby:
            groupby = 'none'

        sorted_list = {
            'id': {'label': 'ID Desc', 'order': 'id desc'},
            'date': {'label': "Date Desc", 'order': 'date_created desc'},
        }

        search_list = {
            'All': {'label': 'All', 'input': 'All', 'domain': []},
            'Account': {'label': 'Account Name', 'input': 'Account', 'domain': [('account_id.title', 'ilike', search)]},
            'Subject': {'label': 'Subject', 'input': 'Subject', 'domain': [('subject', 'ilike', search)]},
        }

        groupby_list = {
            'none': {'input': 'none', 'label': _("None"), "order": 1},
            'account_id': {'input': 'account_id', 'label': _("Account"), "order": 1},
            'state': {'input': 'state', 'label': _("Status"), "order": 1},
            'priority': {'input': 'priority', 'label': _("Priority"), "order": 1},
        }

        #  retrieve the details for the selected groupby criteria from the groupby_list dictionary. If groupby is not found, it returns an empty dictionary.
        ticket_group_by = groupby_list.get(groupby, {})

        tickets_records = request.env["bank.complaint"]

        default_order_by = sorted_list[sortby]['order']

        if groupby in ("account_id", "state", "priority"):
            ticket_group_by = ticket_group_by.get("input")
            default_order_by = ticket_group_by + "," + default_order_by

        else:
            ticket_group_by = ''

        search_domain = search_list[search_in]['domain']

        total_appointments = tickets_records.search_count(search_domain)

        page_detail = pager(url='/my/tickets', total=total_appointments, page=page, step=4,
                            url_args={'sortby': sortby, 'search_in': search_in, 'search': search, 'groupby': groupby})

        tickets = tickets_records.search(search_domain, limit=4, offset=page_detail['offset'], order=default_order_by)

        # groupelem -> (dataToIterate,key) -> gives groupby option in grouplist
        if ticket_group_by:
            tickets_group_list = [{ticket_group_by: k, 'tickets': tickets_records.concat(*g)} for k, g in
                                  groupbyelem(tickets, itemgetter(ticket_group_by))]
        else:
            tickets_group_list = [{'tickets': tickets}]

        vals = {'default_url': '/my/tickets', 'tickets': tickets, 'group_tickets': tickets_group_list,
                'page_name': 'tickets_list_view', 'sortby': sortby,
                'searchbar_sortings': sorted_list,
                'pager': page_detail, 'search_in': search_in,
                'searchbar_inputs': search_list, 'search': search, 'groupby': groupby,
                'searchbar_groupby': groupby_list}

        return request.render("bank.ticket_list_view_portal", vals)

    @http.route(['/my/tickets/<model("bank.complaint"):ticket_id>'], type='http', auth="user", website=True)
    def ticket_form_view(self, ticket_id, **kw):
        vals = {"ticket": ticket_id, 'page_name': 'tickets_form_view'}

        ticket_records = request.env["bank.complaint"].search([])
        ticket_ids = ticket_records.ids
        ticket_index = ticket_ids.index(ticket_id.id)

        if ticket_index != 0 and ticket_ids[ticket_index - 1]:
            vals['prev_record'] = '/my/tickets/{}'.format(ticket_ids[ticket_index - 1])

        if ticket_index < len(ticket_ids) - 1 and ticket_ids[ticket_index + 1]:
            vals['next_record'] = '/my/tickets/{}'.format(ticket_ids[ticket_index + 1])

        return request.render("bank.ticket_form_view_portal", vals)
