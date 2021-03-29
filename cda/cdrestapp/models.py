from decimal import Decimal
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator


class CourierType(models.Model):
    """
    Stores a single courier type
    with it's capacity and earning coefficient.
    """

    courier_type = models.CharField(primary_key=True, max_length=20)
    capacity = models.IntegerField(validators=[MinValueValidator(0)])
    earnings_coef = models.IntegerField(validators=[MinValueValidator(0)])


class Courier(models.Model):
    """
    Stores a single courier with it's id and earnings,
    related to :model:`CourierType`.
    """

    courier_id = models.IntegerField(primary_key=True, validators=[MinValueValidator(1)])
    courier_type = models.ForeignKey(CourierType, on_delete=models.CASCADE)
    earnings = models.IntegerField(default=0)


class WorkingHours(models.Model):
    """
    Stores a single pair of work start and work end
    related to :model:`Courier`.
    """

    courier_id = models.ForeignKey(Courier, related_name='working_hours', on_delete=models.CASCADE)
    work_start = models.TimeField(blank=False)
    work_end = models.TimeField(blank=False)


class CourierRegions(models.Model):
    """Stores a single region related to :model:`Courier`"""
    courier_id = models.ForeignKey(Courier, related_name='regions', on_delete=models.CASCADE)
    region = models.IntegerField(validators=[MinValueValidator(1)])


class Order(models.Model):
    """
    Stores a single order with it's id, weight, region, assign time,
    complete time and bool field delivery_complete, which indicates
    if a delivery which this order is associated with is over,
    related to :model:`CourierType` and :model:`Courier`.
    """

    order_id = models.IntegerField(primary_key=True)
    courier_id = models.ForeignKey(Courier, on_delete=models.CASCADE, null=True)
    weight = models.DecimalField(
        max_digits=4, decimal_places=2, default=1,
        validators=[MinValueValidator(Decimal('0.01')), MaxValueValidator(Decimal('50'))]
    )
    region = models.IntegerField(validators=[MinValueValidator(1)])
    assign_time = models.DateTimeField(null=True)
    complete_time = models.DateTimeField(null=True)
    courier_type = models.ForeignKey(CourierType, on_delete=models.CASCADE, null=True)
    delivery_complete = models.BooleanField(null=True)

    class Meta:
        ordering = ['-complete_time', 'weight']


class DeliveryHours(models.Model):
    """
    Stores a single pair of delivery start and delivery end
    related to :model:`Order`.
    """

    order_id = models.ForeignKey(Order, related_name='delivery_hours', on_delete=models.CASCADE)
    delivery_start = models.TimeField()
    delivery_end = models.TimeField()
