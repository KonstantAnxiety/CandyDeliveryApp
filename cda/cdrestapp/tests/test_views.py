import json
from rest_framework import status
from django.test import TestCase, Client
from django.urls import reverse
from ..models import Courier, Order, CourierType
from ..serializers import CourierSerializer, OrderSerializer, CourierTypeSerializer
from .test_requests_contents import valid_couriers, invalid_couriers, \
    valid_courier_patch, valid_orders, invalid_orders, invalid_assign, \
    valid_complete, invalid_courier_patch, invalid_complete, valid_courier_type, \
    invalid_courier_type, valid_assign_one, valid_assign_two

client = Client()


class GetPostCourierTypesTest(TestCase):
    """Class with courier types tests."""

    fixtures = ['initial_data']

    def test_get_all_courier_types(self):
        response = client.get(reverse('courier-types-list'))
        courier_types = CourierType.objects.all()
        serializer = CourierTypeSerializer(courier_types, many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_post_valid_courier_type(self):
        response = client.post(
            path=reverse('courier-types-list'),
            data=valid_courier_type,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_post_invalid_courier_type(self):
        response = client.post(
            path=reverse('courier-types-list'),
            data=invalid_courier_type,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class GetPostPatchCouriersTest(TestCase):
    """Class with couriers tests."""

    fixtures = ['test_data']

    def test_get_all_couriers(self):
        response = client.get(reverse('couriers-list'))
        couriers = Courier.objects.all()
        serializer = CourierSerializer(couriers, many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_get_valid_courier_details_no_rating(self):
        response = client.get(reverse('courier-detail', kwargs={'pk': 2}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            list(json.loads(response.content).keys()),
            ['courier_id', 'courier_type', 'regions', 'working_hours', 'earnings']
        )

    def test_get_valid_courier_details_with_rating(self):
        response = client.get(reverse('courier-detail', kwargs={'pk': 1}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            list(json.loads(response.content).keys()),
            ['courier_id', 'courier_type', 'regions', 'working_hours', 'rating', 'earnings']
        )

    def test_get_invalid_courier_details(self):
        response = client.get(reverse('courier-detail', kwargs={'pk': 0}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.content, b'{"error": "Courier not found"}')

    def test_post_valid_couriers(self):
        response = client.post(
            path=reverse('couriers-list'),
            data=valid_couriers,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(list(json.loads(response.content).keys()), ['couriers'])

    def test_post_invalid_couriers(self):
        response = client.post(
            path=reverse('couriers-list'),
            data=invalid_couriers,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(list(json.loads(response.content).keys()), ['validation_error'])

    def test_patch_courier_valid(self):
        response = client.patch(
            path=reverse('courier-detail', kwargs={'pk': 1}),
            data=valid_courier_patch,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            list(json.loads(response.content).keys()),
            ['courier_id', 'courier_type', 'regions', 'working_hours']
        )

    def test_patch_courier_invalid_404(self):
        response = client.patch(
            path=reverse('courier-detail', kwargs={'pk': 637}),
            data=valid_courier_patch,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_courier_invalid_400(self):
        response = client.patch(
            path=reverse('courier-detail', kwargs={'pk': 1}),
            data=invalid_courier_patch,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(list(json.loads(response.content).keys()), ['validation_error'])


class GetPostOrdersTest(TestCase):
    """Class with orders tests."""

    def test_post_valid_orders(self):
        response = client.post(
            path=reverse('orders-list'),
            data=valid_orders,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(list(json.loads(response.content).keys()), ['orders'])

    def test_get_all_orders(self):
        response = client.get(reverse('orders-list'))
        orders = Order.objects.all()
        serializer = OrderSerializer(orders, many=True)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_invalid_orders(self):
        response = client.post(
            path=reverse('orders-list'),
            data=invalid_orders,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(list(json.loads(response.content).keys()), ['validation_error'])


class AssignOrderTest(TestCase):
    """Class with order assign tests."""

    fixtures = ['test_data']

    def test_assign_valid_no_new_orders(self):
        response = client.post(
            path=reverse('order-assign'),
            data=valid_assign_one,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(list(json.loads(response.content).keys()), ['orders', 'assign_time'])

    def test_assign_valid_new_orders(self):
        response = client.post(
            path=reverse('order-assign'),
            data=valid_assign_two,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(list(json.loads(response.content).keys()), ['orders', 'assign_time'])

    def test_assign_invalid(self):
        response = client.post(
            path=reverse('order-assign'),
            data=invalid_assign,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(list(json.loads(response.content).keys()), ['validation_error'])


class CompleteOrderTest(TestCase):
    """Class with order complete tests."""

    fixtures = ['test_data']

    def test_complete_valid(self):
        response_complete = client.post(
            path=reverse('order-complete'),
            data=valid_complete,
            content_type='application/json'
        )
        self.assertEqual(response_complete.status_code, status.HTTP_200_OK)
        self.assertEqual(list(json.loads(response_complete.content).keys()), ['order_id'])

    def test_complete_invalid(self):
        response = client.post(
            path=reverse('order-complete'),
            data=invalid_complete,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(list(json.loads(response.content).keys()), ['validation_error'])
