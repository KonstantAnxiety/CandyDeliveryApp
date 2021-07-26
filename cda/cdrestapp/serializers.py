from datetime import datetime, timezone
from rest_framework.serializers import ValidationError, ModelSerializer
from rest_framework.fields import empty
from rest_framework.settings import api_settings
from django.db.models import F
from .models import CourierType, CourierRegions, Courier, \
    Order, WorkingHours, DeliveryHours
from .functions import time_interval_re, WRONG_TIME_FORMAT_MESSAGE,\
    WRONG_TIME_INTERVAL_ORDER, work_delivery_intersect


class CourierTypeSerializer(ModelSerializer):
    """Serializer class for CourierType model."""

    class Meta:
        model = CourierType
        fields = '__all__'

    def to_representation(self, instance):
        """Return courier_type field as a representation."""

        return instance.courier_type


class CourierRegionsSerializer(ModelSerializer):
    """Serializer class for CourierRegions model."""

    class Meta:
        model = CourierRegions
        fields = '__all__'

    def to_representation(self, instance):
        """Return region field as a representation."""

        return instance.region

    def create(self, validated_data):
        """Save a new instance to the database."""

        region = CourierRegions.objects.create(
            courier_id=validated_data['courier_obj'],  # Courier.objects.get(courier_id=validated_data['courier_id']),
            region=validated_data['region']
        )
        return region

    # TODO refactor this
    def to_internal_value(self, data):
        """Validate data."""

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
    """Serializer class for WorkingHours model."""

    class Meta:
        model = WorkingHours
        fields = '__all__'

    def to_representation(self, instance):
        """Return a string like HH:MM-HH:MM as a representation."""

        return str(instance.work_start)[:5] + '-' + str(instance.work_end)[:5]

    def create(self, validated_data):
        """Save a new instance to the database."""

        w_h = WorkingHours.objects.create(
            courier_id=validated_data['courier_obj'],  # Courier.objects.get(courier_id=validated_data['courier_id']),
            work_start=validated_data['working_hours'][:5],
            work_end=validated_data['working_hours'][6:]
        )
        return w_h

    # TODO refactor this
    def to_internal_value(self, data):
        """Validate data."""

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
    """Serializer class for DeliveryHours model."""

    class Meta:
        model = WorkingHours
        fields = '__all__'

    def to_representation(self, instance):
        """Return a string like HH:MM-HH:MM as a representation."""

        return str(instance.delivery_start)[:5] + '-' + str(instance.delivery_end)[:5]

    def create(self, validated_data):
        """Save a new instance to the database."""

        d_h = DeliveryHours.objects.create(
            order_id=Order.objects.get(order_id=validated_data['order_id']),
            delivery_start=validated_data['delivery_hours'][:5],
            delivery_end=validated_data['delivery_hours'][6:]
        )
        return d_h

    # TODO refactor this
    def to_internal_value(self, data):
        """Validate data."""

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
    """Serializer class for Courier model."""

    class Meta:
        model = Courier
        fields = ('courier_id', 'courier_type', 'regions', 'working_hours',)

    regions = CourierRegionsSerializer(many=True)
    working_hours = WorkingHoursSerializer(many=True)

    @staticmethod
    def save_regions(validated_data):
        """Save new CourierRegion instances to the database."""

        for region in validated_data['regions']:
            new_region = CourierRegionsSerializer(data={
                'courier_id': validated_data['courier_id'],
                'courier_obj': validated_data['courier_obj'],
                'region': region
            })
            if not new_region.is_valid():
                raise ValidationError(new_region.errors)
            new_region.save()

    @staticmethod
    def save_hours(validated_data):
        """Save new WorkingHours instances to the database."""

        for w_h in validated_data['working_hours']:
            new_w_h = WorkingHoursSerializer(data={
                'courier_id': validated_data['courier_id'],
                'courier_obj': validated_data['courier_obj'],
                'working_hours': w_h
            })
            if not new_w_h.is_valid():
                raise ValidationError(new_w_h.errors)
            new_w_h.save()

    def create(self, validated_data):
        """Save a new instance to the database."""

        new_courier = Courier(
            courier_id=validated_data['courier_id'],
            courier_type=validated_data['courier_type']
        )
        new_courier.save()
        validated_data['courier_obj'] = new_courier
        self.save_hours(validated_data)
        self.save_regions(validated_data)
        return new_courier

    def update(self, instance, validated_data):
        """Update an existing instance and save."""

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
        partial_delivery = Order.objects.filter(
            courier_id=instance,
            complete_time__isnull=False,
            delivery_complete=False
        )
        # yeah I know this looks abysmal why do you ask
        working_hours = WorkingHours.objects.filter(courier_id=instance)
        # remove orders that do not suit working hours
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
        # remove too heavy orders
        while total_weight > capacity and orders_to_deliver.exists():
            total_weight -= orders_to_deliver[0].weight
            order_ids_to_remove.append(orders_to_deliver[0].order_id)
            orders_to_deliver = orders_to_deliver.exclude(order_id=orders_to_deliver[0].order_id)
        Order.objects.filter(order_id__in=order_ids_to_remove).update(
            courier_id=None,
            assign_time=None,
            courier_type=None,
            delivery_complete=None
        )
        # add earnings if current delivery is over
        # and he managed to complete any orders from it
        if not orders_to_deliver.exists() and partial_delivery.exists():
            instance.earnings = F('earnings') + 500 * partial_delivery[0].courier_type.earnings_coef
            instance.save()
            partial_delivery.update(delivery_complete=True)
        return instance

    def validate_regions(self, value):
        """
        Raises ValidationError if the given list of regions
        is empty, the list otherwise.
        """

        if len(value) == 0:
            raise ValidationError('List should not be empty.')
        return value

    def validate_working_hours(self, value):
        """
        Raises ValidationError if the given list of working hours
        is empty, the list otherwise.
        """

        if len(value) == 0:
            raise ValidationError('List should not be empty.')
        return value

    def run_validation(self, data=empty):
        """
        Raises ValidationError if the request body
        contains unexpected fields.
        """

        # no idea why there is no such built in feature in DRF
        if data is not empty:
            unknown = set(data) - set(self.fields)
            if unknown:
                errors = ['Unknown field: {}'.format(f) for f in unknown]
                raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: errors})
        return super().run_validation(data)


class OrderSerializer(ModelSerializer):
    """Serializer class for Order model."""

    class Meta:
        model = Order
        fields = ('order_id', 'weight', 'region', 'delivery_hours',)

    delivery_hours = DeliveryHoursSerializer(many=True)

    @staticmethod
    def save_hours(validated_data):
        """Save new instances of DeliveryHours to the database."""

        for d_h in validated_data['delivery_hours']:
            new_d_h = DeliveryHoursSerializer(data={
                'order_id': validated_data['order_id'],
                'delivery_hours': d_h
            })
            if not new_d_h.is_valid():
                raise ValidationError(new_d_h.errors)
            new_d_h.save()

    def create(self, validated_data):
        """Save a new instance to the database."""

        new_order = Order(
            order_id=validated_data['order_id'],
            weight=validated_data['weight'],
            region=validated_data['region']
        )
        new_order.save()
        self.save_hours(validated_data)
        return new_order

    def validate_delivery_hours(self, value):
        """
        Raises ValidationError if the given list of delivery hours
        is empty, the list otherwise.
        """

        if len(value) == 0:
            raise ValidationError('List should not be empty.')
        return value

    def run_validation(self, data=empty):
        """
        Raises ValidationError if the request body
        contains unexpected fields.
        """

        if data is not empty:
            unknown = set(data) - set(self.fields)
            if unknown:
                errors = ['Unknown field: {}'.format(f) for f in unknown]
                raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: errors})
        return super().run_validation(data)


class OrderAssignSerializer(ModelSerializer):
    """Serializer class for Order model (on POST /orders/assign)."""

    class Meta:
        model = Order
        fields = ('courier_id',)

    def create(self, validated_data):
        """Assign orders to a given courier."""

        courier_obj = validated_data['courier_id']
        assigned_orders = Order.objects.filter(courier_id=courier_obj, complete_time__isnull=True)
        if assigned_orders.exists():  # if current delivery is not over, return uncompleted orders
            response = {
                'orders': [{'id': order.order_id} for order in assigned_orders],
                'assign_time': assigned_orders[0].assign_time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-4] + 'Z'
            }
            return response
        regions = CourierRegions.objects.filter(courier_id=courier_obj).values_list('region', flat=True)
        capacity = courier_obj.courier_type.capacity
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
            response['assign_time'] = current_time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-4] + 'Z'
        return response

    def validate(self, attrs):
        """
        Raises ValidationError if the request body
        contains unexpected fields.
        """

        unknown = set(self.initial_data) - set(self.fields)
        if unknown:
            raise ValidationError('Unknown field(s): {}'.format('', ''.join(unknown)))
        return attrs


class OrderCompleteSerializer(ModelSerializer):
    """Serializer class for Order model (on POST /orders/complete)."""

    class Meta:
        model = Order
        fields = ('courier_id', 'order_id', 'complete_time',)
        extra_kwargs = {
            'order_id': {'validators': []},
            'courier_id': {'required': True},
            'complete_time': {'required': True}
        }

    def create(self, validated_data):
        """
        Mark given order as completed and increases
        related courier's earning if current delivery is over.
        """

        order_obj = Order.objects.get(order_id=validated_data['order_id'])
        order_obj.complete_time = validated_data['complete_time']
        order_obj.save()

        # if current delivery is over, add earnings
        if not Order.objects.filter(courier_id=order_obj.courier_id, complete_time__isnull=True).exists():
            order_obj.courier_id.earnings = F('earnings') + 500 * order_obj.courier_type.earnings_coef
            order_obj.courier_id.save()
            Order.objects.filter(assign_time=order_obj.assign_time).update(delivery_complete=True)

        response = {'order_id': validated_data['order_id']}
        return response

    def validate_order_id(self, value):
        """
        Raises ValidationError if order with given id does not exist,
        is not assigned to any courier or is already completed.
        """

        if not Order.objects.filter(order_id=value).exists():
            raise ValidationError(f'Order with id {value} does not exist.')
        order_obj = Order.objects.get(order_id=value)
        if order_obj.assign_time is None:
            raise ValidationError(f'Order with id {value} was not assigned to any courier.')
        if order_obj.complete_time is not None:
            raise ValidationError(f'Order with id {value} has already been completed.')
        return value

    def validate(self, attrs):
        """Raises ValidationError of the order with the given id is assigned
        to another courier, specified complete_time is greater than order's
        assign_time or there are unexpected fields in the request body.
        """

        errors = {}
        order_obj = Order.objects.get(order_id=attrs['order_id'])
        if order_obj.courier_id.courier_id != attrs['courier_id'].courier_id:
            errors['order_id'] = f'Order with id {order_obj.order_id} is assigned to another courier.'
        unknown = set(self.initial_data) - set(self.fields)
        if unknown:
            errors['Unknown field(s)'] = ''.join(unknown)
        if order_obj.assign_time > attrs['complete_time']:
            errors['complete_time'] = 'complete_time cannot be greater then assign_time.'
        if errors:
            raise ValidationError(errors)
        return attrs
