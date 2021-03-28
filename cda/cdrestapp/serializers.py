from rest_framework.serializers import ValidationError, ModelSerializer
from django.db.models import Q, F
from django.utils import timezone
from datetime import datetime, timezone
from .models import CourierType, CourierRegions, Courier, \
    Order, WorkingHours, DeliveryHours
from .functions import time_interval_re, WRONG_TIME_FORMAT_MESSAGE, WRONG_TIME_INTERVAL_ORDER, work_delivery_intersect
from decimal import Decimal

from rest_framework.fields import empty
from rest_framework.settings import api_settings


class CourierTypeSerializer(ModelSerializer):
    class Meta:
        model = CourierType
        fields = "__all__"

    def to_representation(self, instance):
        return instance.courier_type


class CourierRegionsSerializer(ModelSerializer):
    class Meta:
        model = CourierRegions
        fields = "__all__"

    def to_representation(self, instance):
        return instance.region

    def create(self, validated_data):
        region = CourierRegions.objects.create(courier_id=Courier.objects.get(courier_id=validated_data['courier_id']),
                                               region=validated_data['region'])
        return region

    # TODO refactor this
    def to_internal_value(self, data):
        if isinstance(data, int):
            if data <= 0:
                raise ValidationError({data: 'Ensure this value is greater than or equal to 1.'})
        elif isinstance(data, dict):
            if data['region'] <= 0 or isinstance(data['region'], float):
                raise ValidationError({data['region']: 'A valid integer is required.'})
        else:
            raise ValidationError({data: 'A valid integer is required.'})
        return data


class WorkingHoursSerializer(ModelSerializer):
    class Meta:
        model = WorkingHours
        fields = "__all__"

    def to_representation(self, instance):
        return str(instance.work_start)[:5] + '-' + str(instance.work_end)[:5]

    def create(self, validated_data):
        wh = WorkingHours.objects.create(courier_id=Courier.objects.get(courier_id=validated_data['courier_id']),
                                         work_start=validated_data['working_hours'][:5],
                                         work_end=validated_data['working_hours'][6:])
        return wh

    # TODO refactor this
    def to_internal_value(self, data):
        if isinstance(data, str):
            if not time_interval_re.match(data):
                raise ValidationError({data: WRONG_TIME_FORMAT_MESSAGE})
            if data[:5] >= data[6:]:
                raise ValidationError({data: WRONG_TIME_INTERVAL_ORDER})
        elif isinstance(data, dict):
            if not time_interval_re.match(data['working_hours']):
                raise ValidationError({data['working_hours']: WRONG_TIME_FORMAT_MESSAGE})
            if data['working_hours'][:5] >= data['working_hours'][6:]:
                raise ValidationError({data['working_hours']: WRONG_TIME_INTERVAL_ORDER})
        else:
            raise ValidationError({data: 'Expected a string.'})
        return data


class DeliveryHoursSerializer(ModelSerializer):
    class Meta:
        model = WorkingHours
        fields = "__all__"

    def to_representation(self, instance):
        return str(instance.delivery_start)[:5] + '-' + str(instance.delivery_end)[:5]

    def create(self, validated_data):
        dh = DeliveryHours.objects.create(order_id=Order.objects.get(order_id=validated_data['order_id']),
                                          delivery_start=validated_data['delivery_hours'][:5],
                                          delivery_end=validated_data['delivery_hours'][6:])
        return dh

    # TODO refactor this
    def to_internal_value(self, data):
        if isinstance(data, str):
            if not time_interval_re.match(data):
                raise ValidationError({data: WRONG_TIME_FORMAT_MESSAGE})
            if data[:5] >= data[6:]:
                raise ValidationError({data: WRONG_TIME_INTERVAL_ORDER})
        elif isinstance(data, dict):
            if not time_interval_re.match(data['delivery_hours']):
                raise ValidationError({data['delivery_hours']: WRONG_TIME_FORMAT_MESSAGE})
            if data['delivery_hours'][:5] >= data['delivery_hours'][6:]:
                raise ValidationError({data['delivery_hours']: WRONG_TIME_INTERVAL_ORDER})
        else:
            raise ValidationError({data: 'Expected a string.'})
        return data


class CourierSerializer(ModelSerializer):
    class Meta:
        model = Courier
        fields = ('courier_id', 'courier_type', 'regions', 'working_hours',)

    regions = CourierRegionsSerializer(many=True)
    working_hours = WorkingHoursSerializer(many=True)

    @staticmethod
    def save_regions(validated_data):
        for region in validated_data['regions']:
            new_region = CourierRegionsSerializer(data={'courier_id': validated_data['courier_id'],
                                                        'region': region})
            if not new_region.is_valid():
                raise ValidationError(new_region.errors)
            new_region.save()

    @staticmethod
    def save_hours(validated_data):
        for wh in validated_data['working_hours']:
            new_wh = WorkingHoursSerializer(data={'courier_id': validated_data['courier_id'],
                                                  'working_hours': wh})
            if not new_wh.is_valid():
                raise ValidationError(new_wh.errors)
            new_wh.save()

    def create(self, validated_data):
        new_courier = Courier(courier_id=validated_data['courier_id'],
                              courier_type=validated_data['courier_type'])
        new_courier.save()
        self.save_hours(validated_data)
        self.save_regions(validated_data)
        return new_courier

    def update(self, instance, validated_data):
        if 'courier_type' in validated_data.keys():
            instance.courier_type = validated_data['courier_type']
            instance.save()
        if 'working_hours' in validated_data.keys():
            WorkingHours.objects.filter(courier_id=instance.courier_id).delete()
            self.save_hours(validated_data)
        if 'regions' in validated_data.keys():
            CourierRegions.objects.filter(courier_id=instance.courier_id).delete()
            self.save_regions(validated_data)
        regions = CourierRegions.objects.filter(courier_id=instance).values_list('region', flat=True)
        capacity = CourierType.objects.get(courier_type=instance.courier_type.courier_type).capacity
        orders_to_deliver = Order.objects.filter(courier_id=instance, complete_time__isnull=True).order_by('-weight')
        partial_delivery = Order.objects.filter(courier_id=instance,
                                                complete_time__isnull=False,
                                                delivery_complete=False)
        working_hours = WorkingHours.objects.filter(courier_id=instance)
        for order in orders_to_deliver:
            delivery_hours = DeliveryHours.objects.filter(order_id=order)
            if not (order.region in regions and work_delivery_intersect(working_hours, delivery_hours)):
                order.courier_id = None
                order.assign_time = None
                order.courier_type = None
                order.delivery_complete = None
                order.save()
                orders_to_deliver = orders_to_deliver.exclude(order_id=order.order_id)
        total_weight = sum(orders_to_deliver.values_list('weight', flat=True))
        order_ids_to_remove = []
        while total_weight > capacity and orders_to_deliver.exists():
            total_weight -= orders_to_deliver[0].weight
            order_ids_to_remove.append(orders_to_deliver[0].order_id)
            orders_to_deliver = orders_to_deliver.exclude(order_id=orders_to_deliver[0].order_id)
        Order.objects.filter(order_id__in=order_ids_to_remove).update(courier_id=None,
                                                                      assign_time=None,
                                                                      courier_type=None,
                                                                      delivery_complete=None)
        if not orders_to_deliver.exists() and partial_delivery.exists():
            instance.earnings = F('earnings') + 500 * partial_delivery[0].courier_type.earnings_coef
            instance.save()
            partial_delivery.update(delivery_complete=True)
        return instance

    def validate_regions(self, value):
        if len(value) == 0:
            raise ValidationError('List should not be empty.')
        return value

    def validate_working_hours(self, value):
        if len(value) == 0:
            raise ValidationError('List should not be empty.')
        return value

    def run_validation(self, data=empty):
        if data is not empty:
            unknown = set(data) - set(self.fields)
            if unknown:
                errors = ["Unknown field: {}".format(f) for f in unknown]
                raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: errors})
        return super(CourierSerializer, self).run_validation(data)


class OrderSerializer(ModelSerializer):
    class Meta:
        model = Order
        fields = ('order_id', 'weight', 'region', 'delivery_hours',)

    delivery_hours = DeliveryHoursSerializer(many=True)

    @staticmethod
    def save_hours(validated_data):
        for dh in validated_data['delivery_hours']:
            new_dh = DeliveryHoursSerializer(data={'order_id': validated_data['order_id'],
                                                   'delivery_hours': dh})
            if not new_dh.is_valid():
                raise ValidationError(new_dh.errors)
            new_dh.save()

    def create(self, validated_data):
        new_order = Order(order_id=validated_data['order_id'],
                          weight=validated_data['weight'],
                          region=validated_data['region'])
        new_order.save()
        self.save_hours(validated_data)
        return new_order

    def validate_delivery_hours(self, value):
        if len(value) == 0:
            raise ValidationError('List should not be empty.')
        return value

    def run_validation(self, data=empty):
        if data is not empty:
            unknown = set(data) - set(self.fields)
            if unknown:
                errors = ["Unknown field: {}".format(f) for f in unknown]
                raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: errors})
        return super(OrderSerializer, self).run_validation(data)


class OrderAssignSerializer(ModelSerializer):
    class Meta:
        model = Order
        fields = ('courier_id',)

    def create(self, validated_data):
        courier_obj = validated_data['courier_id']
        assigned_orders = Order.objects.filter(courier_id=courier_obj, complete_time__isnull=True)
        if assigned_orders.exists():
            response = {'orders': [{'id': order.order_id} for order in assigned_orders],
                        'assign_time': assigned_orders[0].assign_time}
            return response
        regions = CourierRegions.objects.filter(courier_id=courier_obj).values_list('region', flat=True)
        capacity = courier_obj.courier_type.capacity  # TODO check this
        orders = Order.objects.filter(weight__lte=capacity, region__in=regions, courier_id__isnull=True)
        current_time = datetime.now(timezone.utc)
        orders_to_assign = []
        working_hours = WorkingHours.objects.filter(courier_id=courier_obj)
        total_weight = 0
        for order in orders:
            if total_weight + order.weight > capacity:
                break
            delivery_hours = DeliveryHours.objects.filter(order_id=order)
            if work_delivery_intersect(working_hours, delivery_hours):
                orders_to_assign.append(order)
                total_weight += order.weight
                order.courier_id = courier_obj
                order.assign_time = current_time
                order.courier_type = courier_obj.courier_type
                order.delivery_complete = False
                order.save()
        response = {'orders': [{'id': order.order_id} for order in orders_to_assign]}
        if orders_to_assign:
            response['assign_time'] = current_time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-4]+'Z'
        return response

    def validate(self, attrs):
        unknown = set(self.initial_data) - set(self.fields)
        if unknown:
            raise ValidationError("Unknown field(s): {}".format(", ".join(unknown)))
        return attrs


class OrderCompleteSerializer(ModelSerializer):
    class Meta:
        model = Order
        fields = ('courier_id', 'order_id', 'complete_time')
        extra_kwargs = {'order_id': {'validators': []},
                        'courier_id': {'required': True},
                        'complete_time': {'required': True}}

    def create(self, validated_data):
        order_obj = Order.objects.get(order_id=validated_data['order_id'])
        order_obj.complete_time = validated_data['complete_time']
        order_obj.save()

        if not Order.objects.filter(courier_id=order_obj.courier_id, complete_time__isnull=True).exists():
            order_obj.courier_id.earnings = F('earnings') + 500 * order_obj.courier_type.earnings_coef
            order_obj.courier_id.save()
            Order.objects.filter(assign_time=order_obj.assign_time).update(delivery_complete=True)

        response = {'order_id': validated_data['order_id']}
        return response

    # TODO validate complete_time > assign_time
    def validate_order_id(self, value):
        if not Order.objects.filter(order_id=value):
            raise ValidationError(f'Order with id {value} does not exist.')
        order_obj = Order.objects.get(order_id=value)
        if order_obj.assign_time is None:
            raise ValidationError(f'Order with id {value} was not assigned to any courier.')
        if order_obj.complete_time is not None:
            raise ValidationError(f'Order with id {value} has already been completed.')
        return value

    def validate(self, attrs):
        order_obj = Order.objects.get(order_id=attrs['order_id'])
        if order_obj.courier_id.courier_id != attrs['courier_id'].courier_id:
            raise ValidationError(f'Order with id {order_obj.order_id} is assigned to another courier.')
        unknown = set(self.initial_data) - set(self.fields)
        if unknown:
            raise ValidationError("Unknown field(s): {}".format(", ".join(unknown)))
        return attrs
