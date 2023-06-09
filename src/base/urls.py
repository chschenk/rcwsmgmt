from django.urls import path, include
from base.views import WorkshopListView, WorkshopDetailView, WorkshopFeedbackView, OrderListView, OrderDetailView
from base.views import OrderRedirect, WorkshopPrintBatchListView, WorkshopAnnotateView, WorkshopPrintView
from base.views import WorkshopPrintBatchDownloadView, WorkshopEquivalentUpdateView, WorkshopUpdateView
urlpatterns = [
    path('', WorkshopListView.as_view(), name="workshop-list"),
    path('workshop/<int:pk>/detail', WorkshopDetailView.as_view(), name='workshop-detail'),
    path('workshop/<int:pk>/eq-update', WorkshopEquivalentUpdateView.as_view(), name='workshop-equivalent'),
    path('workshop/<int:pk>/update', WorkshopUpdateView.as_view(), name='workshop-update'),
    path('workshop/<int:pk>/feedback/<str:template>/<str:next_status>', WorkshopFeedbackView.as_view(), name='workshop-feedback'),
    path('orders', OrderListView.as_view(), name="order-list"),
    path('orders/<int:pk>/detail', OrderDetailView.as_view(), name="order-detail"),
    path('orders/bycode', OrderRedirect.as_view(), name="order-by-code"),
    path('printbatches', WorkshopPrintBatchListView.as_view(), name="printbatch-list"),
    path('printbatches/annotate', WorkshopAnnotateView.as_view(), name="printbatch-annotate"),
    path('printbatches/create', WorkshopPrintView.as_view(), name="printbatch-create"),
    path('printbatches/<int:pk>/download', WorkshopPrintBatchDownloadView.as_view(), name="printbatch-download"),
]

