from django.db import models

# Create your models here.

class Platform(models.Model):
    platform_name = models.CharField(max_length=100, unique=True)
    platform_id = models.AutoField(primary_key=True)
    seller_id = models.IntegerField(primary_key=True)

class Customer(models.Model):
    customer_id = models.CharField(primary_key=True)
    customer_name = models.CharField(max_length=256)
    contact_email = models.EmailField()
    phone_number = models.CharField(max_length=15)


class Order(models.Model):
    order_id = models.IntegerField(primary_key=True)
    product_id = models.IntegerField()
    quantity_sold = models.IntegerField()
    total_sale_value = models.DecimalField(max_digits=10, decimal_places=2)
    date_of_sale = models.DateField()
    customer_id = models.ForeignKey(Customer,on_delete=models.CASCADE)

class Product(models.Model):
    product_id = models.IntegerField(primary_key=True)
    product_name = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)

class Delivery(models.Model):
    order = models.OneToOneField(Order,on_delete=models.CASCADE)
    address = models.TextField()
    delivery_date = models.DateField()
    delivery_status = models.CharField()
    delivery_partner = models.CharField()







