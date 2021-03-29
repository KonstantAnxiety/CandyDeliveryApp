from django.http import JsonResponse
from rest_framework import generics
from rest_framework.settings import api_settings

from .models import CourierType, CourierRegions, Courier, Order
from .serializers import CourierTypeSerializer, CourierRegionsSerializer, \
    OrderAssignSerializer, OrderCompleteSerializer, \
    OrderSerializer, CourierSerializer


class CourierTypeAPIView(generics.ListCreateAPIView):
    """Courier view class (methods: GET, POST)."""

    queryset = CourierType.objects.all()
    serializer_class = CourierTypeSerializer

    def post(self, request, *args, **kwargs):
        """Create new CourierRegion instance."""

        validation = CourierTypeSerializer(data=request.data)
        if validation.is_valid():
            validation.save()
            return JsonResponse(validation.validated_data, status=201)
        return JsonResponse({'validation_error': validation.errors}, status=400)


class CourierRegionsAPIView(generics.ListCreateAPIView):
    """CourierRegions view class."""

    queryset = CourierRegions.objects.all()
    serializer_class = CourierRegionsSerializer


class CourierAPIView(generics.ListCreateAPIView):
    """Courier view class (methods: GET, POST)."""

    queryset = Courier.objects.all()
    serializer_class = CourierSerializer

    def post(self, request, *args, **kwargs):
        """Create new Courier instances and return HTTP_201 or return HTTP_400."""

        if 'data' not in request.data.keys():
            JsonResponse({'validation_error': {'data': 'This field is required.'}}, status=400)
        unknown = set(request.data.keys()) - {'data'}
        if unknown:
            errors = ["Unknown field: {}".format(f) for f in unknown]
            return JsonResponse({'validation_error': {api_settings.NON_FIELD_ERRORS_KEY: errors}}, status=400)
        validation = CourierSerializer(data=request.data['data'], many=True)
        if validation.is_valid():
            validation.save()
            return JsonResponse(
                data={'couriers': [{'id': i['courier_id']} for i in validation.validated_data]},
                status=201
            )
        errors = []
        for index, error in enumerate(validation.errors):
            if error:
                new_error = error
                new_error['id'] = validation.initial_data[index]['courier_id']
                if 'regions' in error.keys():
                    new_error['regions'] = [i for i in new_error['regions'] if i]
                if 'working_hours' in error.keys():
                    new_error['working_hours'] = [i for i in new_error['working_hours'] if i]
                errors.append(new_error)
        return JsonResponse({'validation_error': {'couriers': errors}}, status=400)


class CourierDetailAPIView(generics.RetrieveUpdateAPIView):
    """Courier detail view (methods: GET, PATCH)."""

    queryset = Courier.objects.all()
    serializer_class = CourierSerializer

    def get(self, request, *args, **kwargs):
        """Get courier details (GET /couriers/$courier_id)."""

        pk = kwargs['pk']
        if not Courier.objects.filter(courier_id=pk).exists():
            return JsonResponse(data={'error': 'Courier not found'}, status=404)
        courier = Courier.objects.get(courier_id=pk)
        courier_detail = CourierSerializer(instance=courier).data
        completed_orders = Order.objects.filter(
            courier_id=courier,
            delivery_complete=True
        )
        min_avg_region_time = 60*60
        regions = completed_orders.order_by('region').values_list('region', flat=True).distinct()
        # yeah I know this looks abysmal why do you ask
        for region in regions:
            region_orders = completed_orders.filter(region=region)
            num_region_time = len(region_orders)
            if num_region_time == 0:
                continue
            sum_region_time = 0
            for order in region_orders:
                current_delivery = Order.objects.filter(assign_time=order.assign_time).order_by('-complete_time')
                index_in_delivery = 0
                for index, find_order in enumerate(current_delivery):
                    if find_order.order_id == order.order_id:
                        index_in_delivery = index
                        break
                if index_in_delivery == len(current_delivery) - 1:
                    sum_region_time += (order.complete_time - order.assign_time).total_seconds()
                else:
                    delta = (order.complete_time - current_delivery[index_in_delivery + 1].complete_time)
                    sum_region_time += delta.total_seconds()
            avg_region_time = sum_region_time / num_region_time
            if avg_region_time < min_avg_region_time:
                min_avg_region_time = avg_region_time
        if completed_orders.exists():
            courier_detail['rating'] = round((60*60 - min_avg_region_time)/60/60 * 5, 2)

        courier_detail['earnings'] = courier.earnings
        return JsonResponse(data=courier_detail, status=200)

    def partial_update(self, request, *args, **kwargs):
        """Update courier details (PATCH /couriers/$courier_id)."""

        pk = kwargs['pk']
        patch_data = request.data
        patch_data['courier_id'] = pk
        if not Courier.objects.filter(courier_id=pk).exists():
            return JsonResponse(data={'error': 'Courier not found'}, status=404)
        courier = Courier.objects.get(courier_id=pk)
        validation = CourierSerializer(data=patch_data, partial=True, instance=courier)
        if validation.is_valid():
            validation.update(courier, validation.validated_data)
            return JsonResponse(data=validation.data, status=200)
        return JsonResponse({'validation_error': {'couriers': validation.errors}}, status=400)


class OrderAPIView(generics.ListCreateAPIView):
    """Order view (methods: GET, POST)."""

    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def post(self, request, *args, **kwargs):
        """Create new Order instances and return HTTP_201 or return HTTP_400."""

        if 'data' not in request.data.keys():
            JsonResponse({'validation_error': {'data': 'This field is required.'}}, status=400)
        unknown = set(request.data.keys()) - {'data'}
        if unknown:
            errors = ["Unknown field: {}".format(f) for f in unknown]
            return JsonResponse({'validation_error': {api_settings.NON_FIELD_ERRORS_KEY: errors}}, status=400)
        validation = OrderSerializer(data=request.data['data'], many=True)
        if validation.is_valid():
            validation.save()
            return JsonResponse(
                data={'orders': [{'id': i['order_id']} for i in validation.validated_data]},
                status=201
            )
        validation_errors = [i for i in validation.errors if i]
        errors = []
        for index, error in enumerate(validation.errors):
            if error:
                new_error = error
                new_error['id'] = validation.initial_data[index]['order_id']
                if 'delivery_hours' in error.keys():
                    new_error['delivery_hours'] = [i for i in new_error['delivery_hours'] if i]
                errors.append(new_error)
        return JsonResponse({'validation_error': {'orders': validation_errors}}, status=400)


class OrderAssignAPIView(generics.CreateAPIView):
    """Order assign view (methods: POST)"""

    serializer_class = OrderAssignSerializer

    def post(self, request, *args, **kwargs):
        """Assign orders to given courier and return HTTP_200 or return HTTP_400"""

        if 'courier_id' not in request.data.keys():
            return JsonResponse({'courier_id': 'This field is required.'}, status=400)
        validation = OrderAssignSerializer(data=request.data)
        if validation.is_valid():
            assigned_orders = validation.save()
            return JsonResponse(assigned_orders, status=200)
        return JsonResponse({'validation_error': validation.errors}, status=400)


class OrderCompleteAPIView(generics.CreateAPIView):
    """Order complete view (methods: POST)"""

    serializer_class = OrderCompleteSerializer

    def post(self, request, *args, **kwargs):
        """Mark the given order as completed and return HTTP_200 or return HTTP_400"""

        validation = OrderCompleteSerializer(data=request.data)
        if validation.is_valid():
            assigned_orders = validation.save()
            return JsonResponse(assigned_orders, status=200)
        return JsonResponse({'validation_error': validation.errors}, status=400)
