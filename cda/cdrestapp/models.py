from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from decimal import Decimal


class CourierType(models.Model):
	courier_type = models.CharField(primary_key=True, max_length=20)
	capacity = models.IntegerField()
	earnings_coef = models.IntegerField()
	
	
class Courier(models.Model):
	courier_id = models.IntegerField(primary_key=True)
	courier_type = models.ForeignKey(CourierType, on_delete=models.CASCADE)


class WorkingHours(models.Model):
	courier_id = models.ForeignKey(Courier, related_name='working_hours', on_delete=models.CASCADE)
	work_start = models.TimeField(blank=False)
	work_end = models.TimeField(blank=False)
	

class CourierRegions(models.Model):
	courier_id = models.ForeignKey(Courier, related_name='regions', on_delete=models.CASCADE)
	region = models.IntegerField(validators=[MinValueValidator(1)])
	
	
class Order(models.Model):
	class Meta:
		ordering = ['-complete_time']

	order_id = models.IntegerField(primary_key=True)
	courier_id = models.ForeignKey(Courier, on_delete=models.CASCADE, null=True)
	weight = models.DecimalField(max_digits=4, decimal_places=2, default=1,
								 validators=[MinValueValidator(Decimal('0.01')), MaxValueValidator(Decimal('50'))])
	region = models.IntegerField(validators=[MinValueValidator(1)])
	assign_time = models.DateTimeField(null=True)
	complete_time = models.DateTimeField(null=True)
	courier_type = models.ForeignKey(CourierType, on_delete=models.CASCADE, null=True)


class DeliveryHours(models.Model):
	order_id = models.ForeignKey(Order, related_name='delivery_hours', on_delete=models.CASCADE)
	delivery_start = models.TimeField()
	delivery_end = models.TimeField()
