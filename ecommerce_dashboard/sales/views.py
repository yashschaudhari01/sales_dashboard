from rest_framework.views import APIView
from .models import Order, Customer, Delivery, Platform
from django.db.models import Sum, Q
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.db import transaction
import csv
from io import TextIOWrapper
from django.db.models.functions import TruncMonth


class ImportDataView(APIView):
    parser_classes = [MultiPartParser, FormParser]  # To handle file uploads

    def post(self, request, *args, **kwargs):
        # Ensure the file is included in the request
        csv_file = request.FILES.get("file")

        platform_name = request.data.get("platform_name")  # Platform (e.g., Flipkart)
        if not csv_file:
            return Response({"error": "No file provided."}, status=400)
        if not platform_name:
            return Response({"error": "Platform name is required."}, status=400)

        # Decode file and process rows
        try:
            platform, _ = Platform.objects.get_or_create(platform_name=platform_name)
            file_data = TextIOWrapper(csv_file.file, encoding="utf-8")
            reader = csv.DictReader(file_data)

            with transaction.atomic():  # Ensure all-or-nothing for the import
                for row in reader:
                    # Create or update customer
                    customer, _ = Customer.objects.get_or_create(
                        customer_id=row["CustomerID"],
                        defaults={
                            "customer_name": row["CustomerName"],
                            "contact_email": row["ContactEmail"],
                            "phone_number": row["PhoneNumber"],
                        },
                    )

                    # Create order
                    order, created = Order.objects.update_or_create(
                        order_id=row["OrderID"],
                        defaults={
                            "product_id": row["ProductID"],
                            "product_name": row["ProductName"],
                            "category": row["Category"],
                            "quantity_sold": int(row["QuantitySold"]),
                            "selling_price": float(row["SellingPrice"]),
                            "total_sale_value": float(
                                int(row["QuantitySold"]) * float(row["SellingPrice"])
                            ),
                            "date_of_sale": row["DateOfSale"],
                            "customer_id": customer,
                            "platform_id": platform,
                        },
                    )

                    # Create delivery
                    Delivery.objects.update_or_create(
                        order=order,
                        defaults={
                            "address": row["DeliveryAddress"],
                            "delivery_date": row["DeliveryDate"],
                            "delivery_status": row["DeliveryStatus"],
                            "delivery_partner": (
                                row["DeliveryPartner"] if "ResellerName" in row else ""
                            ),
                        },
                    )
            return Response({"message": "Data imported successfully."})
        except Exception as e:
            return Response({"error": str(e)}, status=500)


class MerticViews(APIView):
    def get(self, request):
        total_revenue = Order.objects.aggregate(Sum("total_sale_value"))[
            "total_sale_value__sum"
        ]
        total_order = Order.objects.count()
        cancelled_order = Order.objects.filter(
            delivery__delivery_status="Cancelled"
        ).count()
        month_wise_sales = (
            Order.objects.annotate(
                month=TruncMonth("date_of_sale")
            )  # Extract month and year
            .values("month")  # Group by month
            .annotate(
                total_sales=Sum("quantity_sold") * Sum("selling_price")
            )  # Calculate total sales
            .order_by("month")  # Order by month
        )
        return Response(
            {
                "total_revenue": total_revenue,
                "total_orders": total_order,
                "cancelled_order_percent": (cancelled_order / total_order) * 100,
                "month_wise_sales": month_wise_sales,
            }
        )


class FilteredDataView(APIView):
    def get(self, request):
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        category = request.query_params.get("category")
        delivery_status = request.query_params.get("delivery_status")
        platform = request.query_params.get("platform")
        state = request.query_params.get("state")

        # Build query
        query = Q()
        if start_date and end_date:
            query &= Q(date_of_sale__range=[start_date, end_date])
        if category:
            query &= Q(category__iexact=category)
        if delivery_status:
            query &= Q(delivery__delivery_status__iexact=delivery_status)
        if platform:
            query &= Q(platform_id__platform_name__iexact=platform)
        if state:
            query &= Q(delivery__address__icontains=state)

        # Fetch the filtered data
        # filtered_data = Order.objects.filter(query).select_related(
        #     "platform_id", "delivery"
        # )
        print('query',query)
        filtered_data = Order.objects.filter(query).select_related('platform_id')  # Fetch platform relation
        deliveries = Delivery.objects.filter(order__in=filtered_data)  # Fetch related deliveries
        print('filtered_fdata' , filtered_data)
        print('deliveries',[i for i in deliveries])

        # Serialize the data
        results = [
            {
                "order_id": order.order_id,
                "product_name": order.product_name,
                "category": order.category,
                "quantity_sold": order.quantity_sold,
                "total_sale_value": order.total_sale_value,
                "date_of_sale": order.date_of_sale,
                "platform": order.platform_id.platform_name,
                # "delivery_status": next(
                #     (delivery.delivery_status for delivery in deliveries if delivery.order == order.order_id), 
                #     "No Delivery Info"
                # ),
                # "state": next(
                #     (delivery.address for delivery in deliveries if delivery.order == order.order_id),
                #     "State Not Found"
                # ),
                "delivery_status": next(
                    (delivery.delivery_status for delivery in deliveries if delivery.order == order.order_id), 
                    "No Delivery Info"
                ),
                "state": next(
                    (delivery.address for delivery in deliveries if delivery.order == order.order_id),
                    "State Not Found"
                ),
            }
            for order in filtered_data
        ]

        return Response(results)
