from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Max
from django.http import HttpResponse, JsonResponse
from django.views.generic import ListView, DetailView, FormView, View, UpdateView, CreateView, DeleteView
from django.views.generic.base import RedirectView
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from io import BytesIO
from django.views.decorators.csrf import csrf_exempt
from xlsxwriter import Workbook
from base.models import  Workshop, Order, LogEntry, WorkshopPrintBatch, WorkshopList, Participant
from base.forms import WorkshopFeedbackForm, WorkshopAnnotateForm, WorkshopPrintForm, WorkshopAddToListForm
from base.forms import WorkshopRemoveFromListForm
import math

class OrderListView(LoginRequiredMixin, ListView):
	model = Order

class OrderDetailView(LoginRequiredMixin, DetailView):
	model = Order

class WorkshopListView(LoginRequiredMixin, ListView):
	model = Workshop
	ordering = ['status', 'updated']

class WorkshopDetailView(LoginRequiredMixin, DetailView):
	model = Workshop

class WorkshopEquivalentUpdateView(LoginRequiredMixin, UpdateView):
	model = Workshop
	fields = ("weq", )
	success_url = reverse_lazy("order-list")

	def get_context_data(self, **kwargs):
		ctx = super().get_context_data(**kwargs)
		ctx['edit_title'] = "Workshop Äquivalenz Punkte ändern"
		return ctx

class WorkshopUpdateView(LoginRequiredMixin, UpdateView):
	model = Workshop
	fields = ("status", )
	success_url = reverse_lazy("order-list")

	def get_context_data(self, **kwargs):
		messages.error(self.request, "Achtung du änderst gerade den Status eines Workshops ohne eine Mail zu versenden")
		ctx = super().get_context_data(**kwargs)
		ctx['edit_title'] = "Workshop Status ändern"
		return ctx

	def form_valid(self, form):
		entry = LogEntry()
		entry.workshop = self.get_object()
		entry.action = "Status manuell geändert"
		entry.title = ""
		entry.message = ""
		entry.time_slot = self.get_object().time_slot
		entry.old_status = self.get_object().status

		valid = super(WorkshopUpdateView, self).form_valid(form)

		entry.new_status = self.get_object().status
		entry.user = self.request.user
		entry.save()
		return valid

class WorkshopFeedbackView(LoginRequiredMixin, FormView):
	form_class = WorkshopFeedbackForm
	template_name = "base/workshop_feedback.html"

	def get_context_data(self, **kwargs):
		ctx = super().get_context_data(**kwargs)
		ctx['object'] = get_object_or_404(Workshop, id=self.kwargs['pk'])
		return ctx

	def get_initial(self):
		initial = super().get_initial()
		ctx = dict()
		ctx['workshop'] = get_object_or_404(Workshop, id=self.kwargs['pk'])
		template = f"base/workshop_feedback_{self.kwargs['template']}"
		initial['subject'] = render_to_string(f"{template}_subject.txt", ctx, self.request)
		initial['message'] = render_to_string(f"{template}.txt", ctx, self.request)
		return initial

	def form_valid(self, form):
		workshop = get_object_or_404(Workshop, id=self.kwargs['pk'])
		next_status = self.kwargs['next_status']
		send_mail(form.cleaned_data['subject'], form.cleaned_data['message'], settings.EMAIL_FROM, [workshop.order.email])
		entry = LogEntry()
		entry.workshop = workshop
		entry.action = "Rückmeldung versendet"
		entry.title = form.cleaned_data['subject']
		entry.message = form.cleaned_data['message']
		entry.time_slot = workshop.time_slot
		entry.old_status = workshop.status
		entry.new_status = next_status
		entry.user = self.request.user
		entry.save()
		workshop.status = next_status
		workshop.save()
		messages.success(self.request, "Rückmeldung erfolgreich versand!")
		return super(WorkshopFeedbackView, self).form_valid(form)


	def get_success_url(self):
		return reverse("workshop-detail", args=(self.kwargs['pk'],))

class OrderRedirect(LoginRequiredMixin, RedirectView):
	def get_redirect_url(self, *args, **kwargs):
		code = self.request.GET['code'].upper()
		try:
			order = Order.objects.get(code=code)
		except Order.DoesNotExist:
			messages.error(self.request, "Keine Bestellung mit diesem Code gefunden!")
			return reverse("order-list")
		return reverse("order-detail", args=(order.id,))

class WorkshopAnnotateView(LoginRequiredMixin, FormView):
	form_class = WorkshopAnnotateForm
	template_name = "base/workshop_annotate.html"

	def form_valid(self, form):
		index =  Workshop.objects.all().aggregate(Max('annotated_id'))['annotated_id__max']
		if index is None:
			index = 0
		index += 1
		workshops = Workshop.objects.filter(status="V", annotated_id=None)
		for workshop in workshops:
			workshop.annotated_id = index
			index += 1
			workshop.save()
		return super(WorkshopAnnotateView, self).form_valid(form)

	def get_success_url(self):
		return reverse('printbatch-list')

class WorkshopPrintView(LoginRequiredMixin, FormView):
	form_class = WorkshopPrintForm
	template_name = "base/workshop_print.html"

	def form_valid(self, form):
		workshops = Workshop.objects.filter(printed=None).exclude(annotated_id=None)
		if len(workshops)==0:
			return super(WorkshopPrintView, self).form_valid(form)
		batch = WorkshopPrintBatch()
		batch.save()
		for workshop in workshops:
			workshop.printed = batch
			workshop.save()
		return super(WorkshopPrintView, self).form_valid(form)

	def get_success_url(self):
		return reverse('printbatch-list')


class WorkshopPrintBatchListView(LoginRequiredMixin, ListView):
	model = WorkshopPrintBatch
	ordering = ['created']

class WorkshopPrintBatchDownloadView(LoginRequiredMixin, View):

	def get(self, request, *args, **kwargs):
		batch = get_object_or_404(WorkshopPrintBatch, pk=self.kwargs['pk'])
		output = BytesIO()
		workbook = Workbook(output)
		sheet = workbook.add_worksheet("Workshops")
		sheet.write(0, 0, "Diözese / Bezirk")
		sheet.write(0, 1, "Stamm")
		sheet.write(0, 2, "Name")
		sheet.write(0, 3, "Workshop Nummer")
		sheet.write(0, 4, "Zeitslot")
		sheet.write(0, 5, "Ort")
		row = 1
		for workshop in batch.workshop_set.all():
			sheet.write(row, 0, str(workshop.order.district))
			sheet.write(row, 1, str(workshop.order.clan))
			sheet.write(row, 2, str(workshop.name))
			sheet.write(row, 3, int(workshop.annotated_id))
			sheet.write(row, 4, str(workshop.get_time_slot_display()))
			sheet.write(row, 5, str(workshop.get_location_display()))
			row += 1

		workbook.close()
		output.seek(0)
		filename="Workshops-{}.xlsx".format(batch.created.strftime("%Y-%m-%d-%H-%M"))
		response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
		response['Content-Disposition'] = 'attachment; filename={}'.format(filename)
		return response

class WorkshopPrintBatchDeleteView(LoginRequiredMixin, DeleteView):
	model = WorkshopPrintBatch
	success_url = reverse_lazy('printbatch-list')

class WorkshopAllDownloadView(LoginRequiredMixin, View):

	def get(self, request, *args, **kwargs):
		output = BytesIO()
		workbook = Workbook(output)
		sheet = workbook.add_worksheet("Workshops")
		sheet.write(0, 0, "Diözese / Bezirk")
		sheet.write(0, 1, "Stamm")
		sheet.write(0, 2, "Name")
		sheet.write(0, 3, "Workshop Nummer")
		sheet.write(0, 4, "Zeitslot")
		sheet.write(0, 5, "Ort")
		sheet.write(0, 6, "Stimmen")
		row = 1
		for workshop in Workshop.objects.filter(status="V"):
			sheet.write(row, 0, str(workshop.order.district))
			sheet.write(row, 1, str(workshop.order.clan))
			sheet.write(row, 2, str(workshop.name))
			if workshop.annotated_id is None:
				sheet.write(row, 3, "Noch nicht nummeriert")
			else:
				sheet.write(row, 3, int(workshop.annotated_id))
			sheet.write(row, 4, str(workshop.get_time_slot_display()))
			sheet.write(row, 5, str(workshop.get_location_display()))
			sheet.write(row, 6, workshop.voted_participants.count())
			row += 1

		workbook.close()
		output.seek(0)
		filename="Alle-Workshops.xlsx"
		response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
		response['Content-Disposition'] = 'attachment; filename={}'.format(filename)
		return response

class ClanListDownloadView(LoginRequiredMixin, View):

	def get(self, request, *args, **kwargs):
		output = BytesIO()
		workbook = Workbook(output)
		sheet = workbook.add_worksheet("Stämme")
		sheet.write(0, 0, "Diözese / Bezirk")
		sheet.write(0, 1, "Stamm")
		sheet.write(0, 2, "Name")
		sheet.write(0, 3, "Anzahl Teilnehmende")
		row = 1
		for order in Order.objects.all():
			sheet.write(row, 0, str(order.district))
			sheet.write(row, 1, str(order.clan))
			sheet.write(row, 2, str(f"{order.first_name} {order.last_name}"))
			sheet.write(row, 3, order.participant_count)
			row += 1

		workbook.close()
		output.seek(0)
		filename="Alle-Staemme.xlsx"
		response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
		response['Content-Disposition'] = 'attachment; filename={}'.format(filename)
		return response

class BreakfastListDownloadView(LoginRequiredMixin, View):

	def get(self, request, *args, **kwargs):
		output = BytesIO()
		workbook = Workbook(output)
		sheet = workbook.add_worksheet("Stämme")
		sheet.write(0, 0, "Diözese / Bezirk")
		sheet.write(0, 1, "Stamm")
		sheet.write(0, 2, "Name")
		sheet.write(0, 3, "Anzahl Teilnehmende")
		sheet.write(0, 4, "Brötchen")
		sheet.write(0, 5, "Milch")
		row = 1
		for order in Order.objects.all():
			sheet.write(row, 0, str(order.district))
			sheet.write(row, 1, str(order.clan))
			sheet.write(row, 2, str(f"{order.first_name} {order.last_name}"))
			sheet.write(row, 3, order.participant_count)
			sheet.write(row, 4, order.participant_count * 2)
			sheet.write(row, 5, math.ceil(order.participant_count * 0.25))
			row += 1

		workbook.close()
		output.seek(0)
		filename="Fruehstueck.xlsx"
		response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
		response['Content-Disposition'] = 'attachment; filename={}'.format(filename)
		return response

class WorkshopListDownloadView(LoginRequiredMixin, View):

	def get(self, request, *args, **kwargs):
		workshop_list = get_object_or_404(WorkshopList, pk=self.kwargs['pk'])
		output = BytesIO()
		workbook = Workbook(output)
		sheet = workbook.add_worksheet("Workshops")
		sheet.write(0, 0, "Diözese / Bezirk")
		sheet.write(0, 1, "Stamm")
		sheet.write(0, 2, "Name")
		sheet.write(0, 3, "Workshop Nummer")
		sheet.write(0, 4, "Zeitslot")
		sheet.write(0, 5, "Ort")
		row = 1
		for workshop in workshop_list.workshops.all():
			sheet.write(row, 0, str(workshop.order.district))
			sheet.write(row, 1, str(workshop.order.clan))
			sheet.write(row, 2, str(workshop.name))
			if workshop.annotated_id is None:
				sheet.write(row, 3, "Noch nicht nummeriert")
			else:
				sheet.write(row, 3, int(workshop.annotated_id))
			sheet.write(row, 4, str(workshop.get_time_slot_display()))
			sheet.write(row, 5, str(workshop.get_location_display()))
			row += 1

		workbook.close()
		output.seek(0)
		filename="Workshoplist-{}.xlsx".format(workshop_list.name)
		response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
		response['Content-Disposition'] = 'attachment; filename={}'.format(filename)
		return response

class WorkshopListCreateView(LoginRequiredMixin, CreateView):
	model = WorkshopList
	success_url = reverse_lazy('workshoplist-list')
	fields = ("name",)

class WorkshopListListView(LoginRequiredMixin, ListView):
	model = WorkshopList
	ordering = ['name']

class WorkshopListDetailView(LoginRequiredMixin, DetailView):
	model = WorkshopList

class WorkshopListDeleteView(LoginRequiredMixin, DeleteView):
	model = WorkshopList
	success_url = reverse_lazy('workshoplist-list')

class WorkshopAddToListFormView(LoginRequiredMixin, FormView):
	form_class = WorkshopAddToListForm
	template_name = "base/workshop_add_to_list.html"
	success_url = reverse_lazy('workshop-list')

	def form_valid(self, form):
		workshop = get_object_or_404(Workshop, pk=self.kwargs['pk'])
		workshop_list = form.cleaned_data['workshop_list']
		if workshop in workshop_list.workshops.all():
			messages.error(self.request, "Der Workshop befindet sich bereits in der Liste")
		else:
			workshop_list.workshops.add(workshop)
			workshop_list.save()
			messages.success(self.request, "Der Workshop wurde zu der Liste hinzugefügt")
		return super().form_valid(form)

class WorkshopRemoveFromListFormView(LoginRequiredMixin, FormView):
	form_class = WorkshopRemoveFromListForm
	template_name = "base/workshop_remove_from_list.html"
	success_url = reverse_lazy('workshoplist-list')

	def get_context_data(self, **kwargs):
		ctx = super().get_context_data(**kwargs)
		ctx['workshop'] = get_object_or_404(Workshop, pk=self.kwargs['pk'])
		ctx['workshop_list'] = get_object_or_404(WorkshopList, pk=self.kwargs['wl_pk'])
		return ctx

	def form_valid(self, form):
		workshop = get_object_or_404(Workshop, pk=self.kwargs['pk'])
		workshop_list = get_object_or_404(WorkshopList, pk=self.kwargs['wl_pk'])
		if workshop in workshop_list.workshops.all():
			workshop_list.workshops.remove(workshop)
			workshop_list.save()
			messages.success(self.request, "Der Workshop wurde von der Liste entfernt")
		else:
			messages.error(self.request, "Der Workshop befindet sich bereits in der Liste")
		return super().form_valid(form)

class WorkshopLocationUpdateView(LoginRequiredMixin, UpdateView):
	model = Workshop
	fields = ("location", )
	success_url = reverse_lazy("order-list")

	def get_context_data(self, **kwargs):
		ctx = super().get_context_data(**kwargs)
		ctx['edit_title'] = "Workshop Ort ändern"
		return ctx

	def form_valid(self, form):
		entry = LogEntry()
		entry.workshop = self.get_object()
		entry.title = ""
		entry.message = ""
		old_location = self.get_object().get_location_display()
		entry.time_slot = self.get_object().time_slot
		entry.old_status = self.get_object().status

		valid = super(WorkshopLocationUpdateView, self).form_valid(form)
		new_location = self.get_object().get_location_display()

		entry.action = f"Ort des Workshops von {old_location} auf {new_location} geändert"
		entry.new_status = self.get_object().status
		entry.user = self.request.user
		entry.save()
		return valid

class VoteView(ListView):
	model = Workshop
	ordering = ['status', 'updated']
	template_name = "base/vote.html"

class WorkshopVoteListView(ListView):
	model = Workshop
	template_name = "base/workshop_votelist.html"
	context_object_name = "workshops"

	def dispatch(self, request, *args, **kwargs):
		participant_id = request.GET.get("participant")
		if not participant_id or not Participant.objects.filter(participant_id=participant_id).exists():
			# Redirect to vote page or show error
			return redirect("vote")  # or use messages and redirect
		self.participant = Participant.objects.get(participant_id=participant_id)
		return super().dispatch(request, *args, **kwargs)

	def get_queryset(self):
		# Nur Workshops mit annotated_id, aufsteigend sortiert
		return Workshop.objects.exclude(annotated_id=None).order_by("annotated_id")

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context["participant_id"] = self.request.GET.get("participant")
		context["voted_workshop_ids"] = list(self.participant.votes.values_list("id", flat=True))
		context["participant_order_id"] = self.participant.order.id
		return context
	
	def post(self, request, *args, **kwargs):
		votes = request.POST.getlist("votes")
		if len(votes) > 3:
			messages.error(request, "Du kannst nur für maximal 3 Workshops abstimmen.")
			return redirect(f"{request.path}?participant={self.participant.participant_id}")
		else:
			self.participant.votes.set(votes)
			self.participant.save()
			messages.success(request, "Deine Stimme wurde gespeichert.")
			return redirect("vote")  # Redirect to VoteView after successful voting

@csrf_exempt
def check_qr_code(request):
	if request.method == "POST":
		import json
		data = json.loads(request.body)
		scanned_id = data.get("qr_code")
		exists = Participant.objects.filter(participant_id=scanned_id).exists()
		return JsonResponse({"exists": exists})
	return JsonResponse({"error": "Invalid request"}, status=400)