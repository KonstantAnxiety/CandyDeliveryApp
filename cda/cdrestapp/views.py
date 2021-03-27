import json
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from rest_framework import generics
from .models import CourierType, CourierRegions, Courier, Order
from .serializers import CourierTypeSerializer, CourierRegionsSerializer, \
                         OrderSerializer, CourierSerializer, OrderAssignSerializer, OrderCompleteSerializer


class CourierTypeAPIView(generics.ListCreateAPIView):
    queryset = CourierType.objects.all()
    serializer_class = CourierTypeSerializer

    def post(self, request, *args, **kwargs):
        validation = CourierTypeSerializer(data=request.data)
        if validation.is_valid():
            validation.save()
            return JsonResponse(validation.validated_data, status=201)
        return JsonResponse({'validation_error': validation.errors}, status=400)


class CourierRegionsAPIView(generics.ListCreateAPIView):
    queryset = CourierRegions.objects.all()
    serializer_class = CourierRegionsSerializer


class CourierAPIView(generics.ListCreateAPIView):
    queryset = Courier.objects.all()
    serializer_class = CourierSerializer

    def post(self, request, *args, **kwargs):
        if 'data' not in request.data.keys():
            JsonResponse({'validation_error': {'data': 'This field is required.'}}, status=400)
        validation = CourierSerializer(data=request.data['data'], many=True)
        if validation.is_valid():
            validation.save()
            return JsonResponse(data={'couriers': [{'id': i['courier_id']} for i in validation.validated_data]},
                                status=201)
        errors = []
        for index, error in enumerate(validation.errors):
            # print(index, error)
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
    queryset = Courier.objects.all()
    serializer_class = CourierSerializer

    def get(self, request, *args, **kwargs):
        pk = kwargs['pk']
        if not Courier.objects.filter(courier_id=pk):
            return JsonResponse(data={'error': 'Courier not found'}, status=404)
        courier = Courier.objects.get(courier_id=pk)
        courier_detail = CourierSerializer(instance=courier).data
        regions = CourierRegions.objects.filter(courier_id=courier)
        completed_orders = Order.objects.filter(courier_id=courier,
                                                complete_time__isnull=False)
        min_avg_region_time = 60*60
        for region in regions:
            region_orders = [item for item in completed_orders if item.region == region.region]
            num_region_time = len(region_orders)
            if not num_region_time:
                continue
            sum_region_time = 0
            for index, order in enumerate(region_orders):
                if index + 1 < num_region_time:
                    sum_region_time += (order.complete_time - region_orders[index+1]).total_seconds()
                else:
                    sum_region_time += (order.complete_time - order.assign_time).total_seconds()
            avg_region_time = sum_region_time / num_region_time
            if avg_region_time < min_avg_region_time:
                min_avg_region_time = avg_region_time
        if completed_orders:
            courier_detail['rating'] = (60*60 - min_avg_region_time)/60/60 * 5

        courier_detail['earnings'] = 500 * sum([item.courier_type.earnings_coef for item in completed_orders])
        return JsonResponse(data=courier_detail, status=200)

    def partial_update(self, request, *args, **kwargs):
        pk = kwargs['pk']
        patch_data = request.data
        patch_data['courier_id'] = pk
        if not Courier.objects.filter(courier_id=pk):
            return JsonResponse(data={'error': 'Courier not found'}, status=404)
        courier = Courier.objects.get(courier_id=pk)
        validation = CourierSerializer(data=patch_data, partial=True, instance=courier)
        if validation.is_valid():
            validation.update(courier, validation.validated_data)
            return JsonResponse(data=validation.data, status=200)
        return JsonResponse({'validation_error': {'couriers': validation.errors}}, status=400)


class OrderAPIView(generics.ListCreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def post(self, request, *args, **kwargs):
        if 'data' not in request.data.keys():
            JsonResponse({'validation_error': {'data': 'This field is required.'}}, status=400)
        validation = OrderSerializer(data=request.data['data'], many=True)
        if validation.is_valid():
            validation.save()
            return JsonResponse(data={'orders': [{'id': i['order_id']} for i in validation.validated_data]},
                                status=201)
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
    serializer_class = OrderAssignSerializer

    def post(self, request, *args, **kwargs):
        if "courier_id" not in request.data.keys():
            return JsonResponse({'courier_id': 'This field is required.'}, status=400)
        validation = OrderAssignSerializer(data=request.data)
        if validation.is_valid():
            assigned_orders = validation.save()
            return JsonResponse(assigned_orders, status=200)
        return JsonResponse({'validation_error': validation.errors}, status=400)


class OrderCompleteAPIView(generics.CreateAPIView):
    serializer_class = OrderCompleteSerializer

    def post(self, request, *args, **kwargs):
        validation = OrderCompleteSerializer(data=request.data)
        if validation.is_valid():
            assigned_orders = validation.save()
            return JsonResponse(assigned_orders, status=200)
        return JsonResponse({'validation_error': validation.errors}, status=400)
