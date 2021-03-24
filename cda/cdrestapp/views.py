import json
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from rest_framework import generics
from .models import CourierType, CourierRegions, Courier, Order
from .serializers import CourierTypeSerializer, CourierRegionsSerializer, \
                         OrderSerializer, CourierSerializer, OrderAssignSerializer, OrderCompleteSerializer

from django.views.decorators.http import require_http_methods


@require_http_methods(["GET"])
def my_view(request):
    a = json.loads(request.body)
    if a['password'] == 'b253bfa1cf9e70873ff40d783346835bf8592a20':
        return HttpResponse('#', status=200)
    return HttpResponse('*', status=200)
    # return HttpResponse(request, status=200)


class CourierTypeAPIView(generics.ListCreateAPIView):
    # TODO remove this ???
    queryset = CourierType.objects.all()
    serializer_class = CourierTypeSerializer

    def post(self, request, *args, **kwargs):
        # TODO check if courier_type is in CHOICES
        post_data = request.data
        valid = True
        invalid_ids = []
        for index, item in enumerate(post_data):
            if not (item['capacity'].isdigit() and 1e-2 <= float(item['capacity']) <= 50):
                invalid_ids.append(index)
                valid = False
        if not valid:
            return JsonResponse(status=400, data=invalid_ids)
        for item in post_data:
            new_item = CourierType(courier_type=item['courier_type'],
                                   capacity=item['capacity'],
                                   earnings_coef=item['earnings_coef'])
            new_item.save()
        return HttpResponse(json.dumps(post_data), content_type='application/json')


class CourierRegionsAPIView(generics.ListCreateAPIView):
    queryset = CourierRegions.objects.all()
    serializer_class = CourierRegionsSerializer


class CourierAPIView(generics.ListCreateAPIView):
    queryset = Courier.objects.all()
    serializer_class = CourierSerializer

    def post(self, request, *args, **kwargs):
        # TODO check if there is data in the request ?
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


class CourierDetailAPIView(generics.UpdateAPIView):
    queryset = Courier.objects.all()
    serializer_class = CourierSerializer

    def get(self, request, *args, **kwargs):
        pk = kwargs['pk']
        if not Courier.objects.filter(courier_id=pk):
            return HttpResponseBadRequest(content='Courier not found')
        courier = CourierSerializer(instance=Courier.objects.get(courier_id=pk)).data
        return JsonResponse(courier)

    def partial_update(self, request, *args, **kwargs):
        # TODO reassign orders according to new working_hours
        pk = kwargs['pk']
        patch_data = request.data
        patch_data['courier_id'] = pk
        if not Courier.objects.filter(courier_id=pk):
            return HttpResponseBadRequest(content='Courier not found')
        courier = Courier.objects.get(courier_id=pk)
        validation = CourierSerializer(data=patch_data, partial=True, instance=courier)
        if validation.is_valid():
            validation.update(courier, validation.validated_data)
            return self.get(self, pk=pk)
        return JsonResponse({'validation_error': {'couriers': validation.errors}}, status=400)


class OrderAPIView(generics.ListCreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def post(self, request, *args, **kwargs):
        # TODO check if there is data in the request ?
        validation = OrderSerializer(data=request.data['data'], many=True)
        if validation.is_valid():
            validation.save()
            return JsonResponse(data={'orders': [{'id': i['order_id']} for i in validation.validated_data]},
                                status=201)
        validation_errors = [i for i in validation.errors if i]
        errors = []
        for index, error in enumerate(validation.errors):
            # print(index, error)
            if error:
                new_error = error
                new_error['id'] = validation.initial_data[index]['order_id']
                if 'delivery_hours' in error.keys():
                    new_error['delivery_hours'] = [i for i in new_error['delivery_hours'] if i]
                errors.append(new_error)
        return JsonResponse({'validation_error': {'orders': validation_errors}}, status=400)


class OrderAssignAPIView(generics.CreateAPIView):
    serializer_class = OrderAssignSerializer

    # def get(self, request, *args, **kwargs):
    #     return HttpResponse('nice')

    def post(self, request, *args, **kwargs):
        validation = OrderAssignSerializer(data=request.data)
        if validation.is_valid():
            assigned_orders = validation.save()
            return JsonResponse(assigned_orders, status=200)
        return JsonResponse({'validation_errors': validation.errors}, status=400)


class OrderCompleteAPIView(generics.CreateAPIView):
    serializer_class = OrderCompleteSerializer

    # def get(self, request, *args, **kwargs):
    #     return HttpResponse('nice')

    def post(self, request, *args, **kwargs):
        validation = OrderCompleteSerializer(data=request.data)
        if validation.is_valid():
            assigned_orders = validation.save()
            return JsonResponse(assigned_orders, status=200)
        return JsonResponse({'validation_errors': validation.errors}, status=400)
