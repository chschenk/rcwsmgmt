from django.urls import path, include
from base.views import WorkshopListView, WorkshopDetailView, WorkshopFeedbackView, OrderListView, OrderDetailView
from base.views import OrderRedirect, WorkshopPrintBatchListView, WorkshopAnnotateView, WorkshopPrintView
from base.views import WorkshopPrintBatchDownloadView, WorkshopPrintBatchDeleteView, WorkshopEquivalentUpdateView, WorkshopUpdateView
from base.views import WorkshopListCreateView, WorkshopListListView, WorkshopListDetailView, WorkshopListDeleteView
from base.views import WorkshopAddToListFormView, WorkshopRemoveFromListFormView, WorkshopListDownloadView
from base.views import WorkshopAllDownloadView, ClanListDownloadView, BreakfastListDownloadView, WorkshopLocationUpdateView
from base.views import WorkshopVoteListView, VoteView, check_qr_code
urlpatterns = [
    path('', WorkshopListView.as_view(), name="workshop-list"),
    path('workshop/<int:pk>/detail', WorkshopDetailView.as_view(), name='workshop-detail'),
    path('workshop/<int:pk>/addtolist', WorkshopAddToListFormView.as_view(), name='workshop-add-to-list'),
    path('workshop/<int:pk>/removefromlist/<int:wl_pk>', WorkshopRemoveFromListFormView.as_view(), name='workshop-remove-from-list'),
    path('workshop/<int:pk>/eq-update', WorkshopEquivalentUpdateView.as_view(), name='workshop-equivalent'),
    path('workshop/<int:pk>/update', WorkshopUpdateView.as_view(), name='workshop-update'),
    path('workshop/<int:pk>/location-update', WorkshopLocationUpdateView.as_view(), name='workshop-location'),
    path('workshop/<int:pk>/feedback/<str:template>/<str:next_status>', WorkshopFeedbackView.as_view(), name='workshop-feedback'),
    path('orders', OrderListView.as_view(), name="order-list"),
    path('orders/<int:pk>/detail', OrderDetailView.as_view(), name="order-detail"),
    path('orders/bycode', OrderRedirect.as_view(), name="order-by-code"),
    path('orders/download', ClanListDownloadView.as_view(), name="order-download"),
    path('orders/breakfastDownload', BreakfastListDownloadView.as_view(), name="breakfast-download"),
    path('printbatches', WorkshopPrintBatchListView.as_view(), name="printbatch-list"),
    path('printbatches/annotate', WorkshopAnnotateView.as_view(), name="printbatch-annotate"),
    path('printbatches/create', WorkshopPrintView.as_view(), name="printbatch-create"),
    path('printbatches/<int:pk>/download', WorkshopPrintBatchDownloadView.as_view(), name="printbatch-download"),
    path('printbatches/<int:pk>/delete', WorkshopPrintBatchDeleteView.as_view(), name="printbatch-delete"),
    path('printbatches/all/download', WorkshopAllDownloadView.as_view(), name="all-ws-download"),
    path('lists/create', WorkshopListCreateView.as_view(), name='workshoplist-create'),
    path('lists', WorkshopListListView.as_view(), name='workshoplist-list'),
    path('lists/<int:pk>', WorkshopListDetailView.as_view(), name='workshoplist-detail'),
    path('lists/<int:pk>/delete', WorkshopListDeleteView.as_view(), name='workshoplist-delete'),
    path('lists/<int:pk>/download', WorkshopListDownloadView.as_view(), name='workshoplist-download'),
    path('vote/', VoteView.as_view(), name="vote"),
    path('api/check_qr_code/', check_qr_code, name='check_qr_code'),
    path('workshop_votelist/', WorkshopVoteListView.as_view(), name='workshop-votelist'),

]

