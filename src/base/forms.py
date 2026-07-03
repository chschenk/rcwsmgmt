from django.forms import Form, Textarea, CharField, BooleanField, ModelChoiceField, IntegerField
from base.models import WorkshopList

class WorkshopFeedbackForm(Form):
	subject = CharField(required=True, max_length=256)
	message = CharField(widget=Textarea, required=True)

class WorkshopAnnotateForm(Form):
	annotate = BooleanField(required=True, label='Alle Workshops mit Status "Okay" durchnummerieren')

class WorkshopPrintForm(Form):
	generate_batch = BooleanField(required=True, label="Einen neuen Druckauftrag für alle ungedruckten Workshops erstellen")

class WorkshopAddToListForm(Form):
	workshop_list = ModelChoiceField(WorkshopList.objects.all(), label="Workshopliste")

class WorkshopRemoveFromListForm(Form):
	pass


class RuntimeSettingsForm(Form):
	auto_sync_enabled = BooleanField(required=False, label='Automatische Workshop-Synchronisation aktivieren (jede volle Stunde)')
	pretix_event = CharField(required=True, label='Pretix Event', max_length=255)
	pretix_auth_token = CharField(
		required=True,
		label='API token',
		max_length=255,
		help_text='Help: https://docs.pretix.eu/dev/api/tokenauth.html',
	)
	pretix_workshop_product_id = IntegerField(required=True, label='Pretix Workshop Product ID', min_value=1)
	pretix_order_clan_product_id = IntegerField(required=True, label='Pretix Order Clan Product ID', min_value=1)