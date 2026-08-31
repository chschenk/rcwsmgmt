from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Model, CharField, TextField, PositiveIntegerField, DateTimeField, ForeignKey, CASCADE
from django.db.models import BooleanField, SET_NULL, Sum, EmailField, ManyToManyField
class Order(Model):
	clan = CharField(
		max_length=64,
		verbose_name="Stamm",
	)
	district = CharField(
		max_length=128,
		verbose_name="Diözese / Bezirk",
	)
	first_name = CharField(max_length=64, verbose_name="Vorname")
	last_name = CharField(max_length=64, verbose_name="Nachname")
	email = EmailField(verbose_name="E-Mail", max_length=254)
	secret = CharField(max_length=32)
	participant_count = PositiveIntegerField()
	code = CharField(
		max_length=16,
		verbose_name="Bestellungscode",
		db_index=True
	)

	def get_pretix_url(self):
		return f"{settings.PRETIX_URL}/control/event/{settings.PRETIX_ORGANIZER}/{settings.PRETIX_EVENT}/orders/{self.code}/"

	def sufficient_workshops(self):
		order_weq = 0
		for ws in self.workshop_set.all():
			order_weq += ws.get_weq()
		return max(1, int(self.participant_count / settings.WORKSHOPS_PER_PARTICIPANT)) <= order_weq

	def get_pretix_user_url(self):
		return f"{settings.PRETIX_URL}/{settings.PRETIX_ORGANIZER}/{settings.PRETIX_EVENT}/order/{self.code}/{self.secret}/"


class WorkshopPrintBatch(Model):
	created = DateTimeField(auto_now_add=True)

class Workshop(Model):
	STATUS_NEW = "A"
	STATUS_REVISED = "E"
	STATUS_REJECTED = "R"
	STATUS_UNCLEAR = "U"
	STATUS_OKAY = "V"
	STATUS_OKAY_WITHOUT_PRINTING = "X"
	STATUS_DELETED = "Z"
	STATUS_CHOICE=(
		(STATUS_NEW, "Neuer Workshop"),
		(STATUS_REVISED, "Workshop überarbeitet"),
		(STATUS_OKAY, "Workshop okay"),
		(STATUS_OKAY_WITHOUT_PRINTING, "Workshop okay (Nicht drucken)"),
		(STATUS_REJECTED, "Workshop nicht okay"),
		(STATUS_UNCLEAR, "Workshop unklar"),
		(STATUS_DELETED, "Workshop gelöscht"),
	)
	TIMESLOT_MORNING = "M"
	TIMESLOT_AFTERNOON = "A"
	TIMESLOT_BOTH = "B"
	TIMESLOT_CAMP_SERVICE = "C"
	TIMESLOT_CHOICE=(
		(TIMESLOT_MORNING, "Vormittags"),
		(TIMESLOT_AFTERNOON, "Nachmittags"),
		(TIMESLOT_BOTH, "Vor- & Nachmittags"),
		(TIMESLOT_CAMP_SERVICE, ""),
	)
	LOCATION_CENTRAL = "Z"
	LOCATION_DECENTRAL = "D"
	LOCATION_CHOICES=(
		(LOCATION_CENTRAL, "Zentral"),
		(LOCATION_DECENTRAL, "Dezentral"),
	)
	name = CharField(max_length=64, verbose_name="Name")
	order = ForeignKey(Order, on_delete=CASCADE)
	description = TextField(verbose_name="Beschreibung")
	position_id = PositiveIntegerField()
	weq = PositiveIntegerField(default=1, verbose_name="Workshop Äquivalenz Punkte")
	time_slot = CharField(max_length=1, choices=TIMESLOT_CHOICE, verbose_name="Workshopphase")
	location = CharField(max_length=1, choices=LOCATION_CHOICES, default=LOCATION_CENTRAL, verbose_name="Ort")
	status = CharField(max_length=1, choices=STATUS_CHOICE, verbose_name="Status")
	printed = ForeignKey(WorkshopPrintBatch, null=True, on_delete=SET_NULL)
	annotated_id = PositiveIntegerField(null=True)
	updated = DateTimeField(auto_now=True)

	def __str__(self):
		return self.name

	def get_weq(self):
		if self.time_slot == Workshop.TIMESLOT_BOTH:
			return self.weq * 2
		return self.weq

class Participant(Model):
	participant_id = CharField(max_length=64, verbose_name="Teilnehmer-ID", unique=True)
	updated = DateTimeField(auto_now=True)
	order = ForeignKey(Order, on_delete=CASCADE, related_name="participants")
	votes = ManyToManyField(Workshop, blank=True, related_name="voted_participants")

	def clean(self):
		if self.votes.count() > 3:
			raise ValidationError("A participant can vote for up to 3 workshops.")

	def __str__(self):
		return self.participant_id

class LogEntry(Model):
	workshop = ForeignKey(Workshop, on_delete=CASCADE)
	by_customer = BooleanField(default=False)
	user = ForeignKey(User, null=True, on_delete=SET_NULL, related_name="rcwsmgmt_logentries")
	created = DateTimeField(auto_now_add=True)
	old_status = CharField(max_length=1, null=True, choices=Workshop.STATUS_CHOICE, verbose_name="Alter Status")
	new_status = CharField(max_length=1, choices=Workshop.STATUS_CHOICE, verbose_name="Neuer Status")
	action = CharField(max_length=64)
	title = CharField(max_length=256, verbose_name="Betreff")
	message = TextField(verbose_name="Nachricht")
	time_slot = CharField(max_length=1, choices=Workshop.TIMESLOT_CHOICE, verbose_name="Workshopphase")


class WorkshopList(Model):
	name = CharField(max_length=256, verbose_name="Name")
	workshops = ManyToManyField(Workshop)

	def __str__(self):
		return self.name