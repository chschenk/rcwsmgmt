from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from base.models import Order, Workshop, LogEntry, Participant
from .pretix_api import PretixAPI

# ToDo: Check
VALID_ORDERS = ['n', 'p']

class Command(BaseCommand):
	help = 'Syncs workshops from pretix to rcwsmgmt. Should be run periodically'

	def handle(self, *args, **kwargs):
		api = PretixAPI(settings.PRETIX_URL, settings.PRETIX_AUTH_TOKEN, settings.PRETIX_ORGANIZER, settings.PRETIX_EVENT)
		products = api.get_products()
		admission_product_ids = [x['id'] for x in products if x['admission']]
		orders = api.get_orders()

		timeslot_mapping = {
			settings.PRETIX_WORKSHOP_TIMESLOT_ANSWER_MORNING: Workshop.TIMESLOT_MORNING,
			settings.PRETIX_WORKSHOP_TIMESLOT_ANSWER_AFTERNOON: Workshop.TIMESLOT_AFTERNOON,
			settings.PRETIX_WORKSHOP_TIMESLOT_ANSWER_BOTH: Workshop.TIMESLOT_BOTH,
		}

		for order in orders:
			try:
				try:
					rc_order = Order.objects.get(code=order['code'])
					if order['status'] not in VALID_ORDERS:
						rc_order.delete()
						continue
				except Order.DoesNotExist:
					if order['status'] in VALID_ORDERS:
						rc_order = Order()
						rc_order.code = order['code']
						rc_order.email = order['email']
						rc_order.secret = order['secret']
						# participant_count is non-nullable in the database, ensure a default
						rc_order.participant_count = 0
						rc_order.save()
					else:
						continue

				clan_name = None
				district_name = None
				first_name = None
				last_name = None
				for position in order['positions']:
					if position['item'] != int(settings.PRETIX_ORDER_CLAN_PRODUCT_ID):
						continue
					for answer in position['answers']:
						if answer['question_identifier'] == settings.PRETIX_ORDER_CLAN_QUESTION_NAME:
							clan_name = answer['answer']
						if answer['question_identifier'] == settings.PRETIX_ORDER_CLAN_QUESTION_DISTRICT:
							district_name = answer['answer']
						if answer['question_identifier'] == settings.PRETIX_ORDER_CLAN_CONTACT_GIVENNAME:
							first_name = answer['answer']
						if answer['question_identifier'] == settings.PRETIX_ORDER_CLAN_CONTACT_FAMILYNAME:
							last_name = answer['answer']
				if clan_name is None or first_name is None or last_name is None or district_name is None:
					raise ValueError("Order {} has no basic informations".format(order['code']))
				rc_order.clan = clan_name
				rc_order.district = district_name
				rc_order.first_name = first_name
				rc_order.last_name = last_name
				rc_order.save()

				participant_count = 0
				for position in order['positions']:
					if position['item'] not in admission_product_ids:
						continue
					participant_count += 1
					participant_id = position.get('secret')
					if participant_id:
						# Create or update Participant
						participant, created = Participant.objects.get_or_create(
							participant_id=participant_id,
							order=rc_order
						)
						if not created:
							participant.save()  # update timestamp

				rc_order.participant_count = participant_count
				rc_order.save()

				updated_workshops = set()
				for position in order['positions']:
					if position['item'] != int(settings.PRETIX_WORKSHOP_PRODUCT_ID):
						continue
					workshop_name = None
					workshop_description = None
					workshop_timeslot = None
					for answer in position['answers']:
						if answer['question_identifier'] == settings.PRETIX_WORKSHOP_QUESTION_NAME:
							workshop_name = answer['answer']
						if answer['question_identifier'] == settings.PRETIX_WORKSHOP_QUESTION_DESCRIPTION:
							workshop_description = answer['answer']
						if answer['question_identifier'] == settings.PRETIX_WORKSHOP_QUESTION_TIMESLOT:
							workshop_timeslot = answer['answer']
					if workshop_name is None or workshop_description is None or workshop_timeslot is None:
						raise ValueError("Got an Workshop without answers from order {}".format(order['code']))
					if workshop_timeslot not in timeslot_mapping:
						raise ValueError("Got an Workshop with an invalid timeslot in order {}".format(order['code']))
					try:
						rc_workshop = rc_order.workshop_set.get(order=rc_order, position_id=position['positionid'])

						updated_workshops.add(rc_workshop)
						if rc_workshop.name == workshop_name and rc_workshop.description == workshop_description and timeslot_mapping[workshop_timeslot] == rc_workshop.time_slot:
							continue
						entry = LogEntry()
						entry.workshop = rc_workshop
						entry.action = "Workshop wurde überarbeitet"
						entry.title = workshop_name
						entry.message = workshop_description
						entry.old_status = rc_workshop.status
						entry.new_status =  Workshop.STATUS_REVISED
						entry.time_slot = timeslot_mapping[workshop_timeslot]
						entry.by_customer = True
						entry.save()
						rc_workshop.name = workshop_name
						rc_workshop.description = workshop_description
						rc_workshop.status = Workshop.STATUS_REVISED
						rc_workshop.time_slot = timeslot_mapping[workshop_timeslot]
						rc_workshop.save()

					except Workshop.DoesNotExist:
						rc_workshop = Workshop()
						rc_workshop.order = rc_order
						rc_workshop.name = workshop_name
						rc_workshop.description = workshop_description
						rc_workshop.position_id = position['positionid']
						rc_workshop.status = Workshop.STATUS_NEW
						rc_workshop.time_slot = timeslot_mapping[workshop_timeslot]
						rc_workshop.save()
						updated_workshops.add(rc_workshop)
						entry = LogEntry()
						entry.workshop = rc_workshop
						entry.action = "Workshop wurde eingereicht"
						entry.title = workshop_name
						entry.message = workshop_description
						entry.old_status = None
						entry.new_status = Workshop.STATUS_NEW
						entry.time_slot = timeslot_mapping[workshop_timeslot]
						entry.by_customer = True
						entry.save()

				for workshop in rc_order.workshop_set.all():
					if workshop not in updated_workshops:
						entry = LogEntry()
						entry.workshop = workshop
						entry.action = "Workshop gelöscht"
						entry.title = workshop.name
						entry.message = workshop.description
						entry.time_slot = workshop.time_slot
						entry.old_status = workshop.status
						entry.new_status = Workshop.STATUS_DELETED
						entry.by_customer = True
						entry.save()
						workshop.status = Workshop.STATUS_DELETED
						workshop.save()
			except Exception as e:
				send_mail("Fehler beim pretix sync von Bestellung {}".format(order['code']), str(e), settings.EMAIL_FROM, [settings.ADMIN_EMAIL])
