import json
from rest_framework import status
from django.test import TestCase, Client
from django.urls import reverse
from ..models import Courier, CourierType, Order, WorkingHours, CourierRegions
from ..serializers import CourierSerializer, OrderSerializer
from .data_for_tests import valid_couriers, invalid_couriers, \
    valid_courier_patch, valid_orders, invalid_orders, valid_assign, invalid_assign, valid_complete


client = Client()


class GetPostPatchCouriersTest(TestCase):
    fixtures = ['initial_data', 'test_data']

    def test_get_all_couriers(self):
        response = client.get(reverse('couriers-list'))
        couriers = Courier.objects.all()
        serializer = CourierSerializer(couriers, many=True)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_valid_courier_details(self):
        response = client.get(reverse('courier-detail', kwargs={'pk': 1}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(all(item in list(json.loads(response.content).keys()) for item in
                         ['courier_id', 'courier_type', 'regions', 'working_hours', 'earnings']), True)

    def test_get_invalid_courier_details(self):
        response = client.get(reverse('courier-detail', kwargs={'pk': 0}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.content, b'{"error": "Courier not found"}')

    def test_post_valid_couriers(self):
        response = client.post(path=reverse('couriers-list'),
                               data=valid_couriers,
                               content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(list(json.loads(response.content).keys()), ['couriers'])

    def test_post_invalid_couriers(self):
        response = client.post(path=reverse('couriers-list'),
                               data=invalid_couriers,
                               content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(list(json.loads(response.content).keys()), ['validation_error'])

    def test_patch_courier_valid(self):
        response = client.patch(path=reverse('courier-detail', kwargs={'pk': 1}),
                                data=valid_courier_patch,
                                content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(list(json.loads(response.content).keys()),
                         ['courier_id', 'courier_type', 'regions', 'working_hours'])


class GetPostOrdersTest(TestCase):
    def test_post_valid_orders(self):
        response = client.post(path=reverse('orders-list'),
                               data=valid_orders,
                               content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(list(json.loads(response.content).keys()), ['orders'])

    def test_get_all_orders(self):
        response = client.get(reverse('orders-list'))
        orders = Order.objects.all()
        serializer = OrderSerializer(orders, many=True)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_invalid_orders(self):
        response = client.post(path=reverse('orders-list'),
                               data=invalid_orders,
                               content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(list(json.loads(response.content).keys()), ['validation_error'])


class AssignOrderTest(TestCase):
    fixtures = ['initial_data', 'test_data']

    def test_assign_valid(self):
        response = client.post(path=reverse('order-assign'),
                               data=valid_assign,
                               content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(list(json.loads(response.content).keys()), ['orders', 'assign_time'])

    def test_assign_invalid(self):
        response = client.post(path=reverse('order-assign'),
                               data=invalid_assign,
                               content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(list(json.loads(response.content).keys()), ['validation_error'])


class CompleteOrderTest(TestCase):
    fixtures = ['initial_data', 'test_data']

    def test_complete_valid(self):
        response_complete = client.post(path=reverse('order-complete'),
                                        data=valid_complete,
                                        content_type='application/json')
        self.assertEqual(response_complete.status_code, status.HTTP_200_OK)
        self.assertEqual(list(json.loads(response_complete.content).keys()), ['order_id'])

    def test_assign_invalid(self):
        response = client.post(path=reverse('order-assign'),
                               data=invalid_assign,
                               content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(list(json.loads(response.content).keys()), ['validation_error'])
