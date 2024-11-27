
from django.urls import path
from sales.views import ImportDataView,MerticViews,FilteredDataView

urlpatterns = [
    path('import_data/', ImportDataView.as_view()),
    path('getmetrics', MerticViews.as_view()),
    path('filtered-data/', FilteredDataView.as_view())
]
