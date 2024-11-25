from rest_framework.views import APIView
from .models import Order
from django.db.models import Sum 
from rest_framework.response import Response

# Create your views here.

class MerticViews(APIView):
    def get(self, request):
        total_revenue = Order.objects.aggregate(Sum('total_sale_value'))['total_sale_value__sum']
        total_order = Order.objects.count()
        cancelled_order = Order.objects.filter(delivery__delivery_status='Cancelled').count()

        return Response(
            {
                'total_revenue' : total_revenue,
                'total_orders' : total_order,
                'cancelled_order_percent' : (cancelled_order/total_order) * 100
            }
        )
    

