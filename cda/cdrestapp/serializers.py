from rest_framework.serializers import ValidationError, ModelSerializer
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timezone
from .models import CourierType, CourierRegions, Courier, \
    Order, WorkingHours, DeliveryHours
from .functions import time_interval_re, WRONG_TIME_FORMAT_MESSAGE, WRONG_TIME_INTERVAL_ORDER, work_delivery_intersect
from decimal import Decimal

# TODO docstrings
# TODO tests
# TODO pylint


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
        orders = Order.objects.filter(courier_id=instance, complete_time__isnull=True)
        working_hours = WorkingHours.objects.filter(courier_id=instance)
        # TODO write a funny comment about how awful this section is (⊙_⊙;)
        # TODO create function
        for order in orders:
            delivery_hours = DeliveryHours.objects.filter(order_id=order)
            if not (Decimal.compare(Decimal(capacity), Decimal(order.weight))+1 > 0 and
                    order.region in regions and
                    work_delivery_intersect(working_hours, delivery_hours)):
                order.courier_id = None
                order.assign_time = None
                order.courier_type = None
                order.save()
        return instance

    def validate_regions(self, value):
        if len(value) == 0:
            raise ValidationError('List should not be empty.')
        return value

    def validate_working_hours(self, value):
        if len(value) == 0:
            raise ValidationError('List should not be empty.')
        return value


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


class OrderAssignSerializer(ModelSerializer):
    class Meta:
        model = Order
        fields = ('courier_id',)

    def create(self, validated_data):
        current_time = datetime.now(timezone.utc)
        courier_obj = validated_data['courier_id']
        regions = CourierRegions.objects.filter(courier_id=courier_obj).values_list('region', flat=True)
        weight = CourierType.objects.get(courier_type=courier_obj.courier_type.courier_type).capacity
        # find orders that can be assigned to this courier among all orders and assign them
        orders = Order.objects.filter(Q(weight__lte=weight), Q(region__in=regions),
                                      Q(courier_id__isnull=True) | Q(courier_id=courier_obj),
                                      Q(complete_time__isnull=True))
        nice_orders = []
        working_hours = WorkingHours.objects.filter(courier_id=courier_obj)
        # TODO write a funny comment about how awful this section is (⊙_⊙;)
        # TODO and it repeats as well (⊙_⊙;) (⊙_⊙;)
        for order in orders:
            delivery_hours = DeliveryHours.objects.filter(order_id=order)
            nice = False
            if work_delivery_intersect(working_hours, delivery_hours):
                nice_orders.append(order)
                # TODO F() notation ?
                if order.courier_id is None:
                    order.courier_id = courier_obj
                    order.assign_time = current_time
                    order.courier_type = courier_obj.courier_type
                    order.save()
        response = {'orders': [{'id': order.order_id} for order in nice_orders]}
        if len(nice_orders):
            current_time = nice_orders[0].assign_time
            for order in nice_orders:
                if order.assign_time > current_time:
                    current_time = order.assign_time
            response['assign_time'] = current_time.strftime('%Y-%m-%dT%H:%M:%S:%f')[:-4]+'Z'
        return response


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

        response = {'order_id': validated_data['order_id']}
        return response

    def validate_order_id(self, value):
        if not Order.objects.filter(order_id=value):
            raise ValidationError(f'Order with id {value} does not exist.')
        order_obj = Order.objects.get(order_id=value)
        if order_obj.assign_time is None:
            raise ValidationError(f'Order with id {value} was not assigned to any courier.')
        if order_obj.complete_time is not None:
            raise ValidationError(f'Order with id {value} has already been completed.')
        if not Courier.objects.filter(courier_id=order_obj.courier_id.courier_id):
            raise ValidationError(f'Order with id {value} is assigned to another courier.')
        return value
