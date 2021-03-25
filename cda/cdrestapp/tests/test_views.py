import json
from rest_framework import status
from django.test import TestCase, Client
from django.urls import reverse
from ..models import Courier, CourierType, Order, WorkingHours
from ..serializers import CourierSerializer, OrderSerializer
from .data_for_tests import valid_couriers, invalid_couriers, \
    valid_courier_patch, valid_orders, invalid_orders, valid_assign, invalid_assign, valid_complete


# initialize the APIClient app
client = Client()


class GetPostPatchCouriersTest(TestCase):
    def setUp(self):
        ct1 = CourierType.objects.create(courier_type="foot", capacity=10, earnings_coef=2)
        ct2 = CourierType.objects.create(courier_type="bike", capacity=15, earnings_coef=5)
        ct3 = CourierType.objects.create(courier_type="car", capacity=50, earnings_coef=9)
        Courier.objects.create(courier_id=1, courier_type=ct1)
        Courier.objects.create(courier_id=2, courier_type=ct2)
        Courier.objects.create(courier_id=3, courier_type=ct3)

    def test_get_all_couriers(self):
        response = client.get(reverse('couriers-list'))
        couriers = Courier.objects.all()
        serializer = CourierSerializer(couriers, many=True)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_valid_couriers(self):
        response = client.post(path=reverse('couriers-list'),
                               data=valid_couriers,
                               content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_post_invalid_couriers(self):
        response = client.post(path=reverse('couriers-list'),
                               data=invalid_couriers,
                               content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_courier_valid(self):
        response = client.patch(path=reverse('courier-detail', kwargs={'pk': 1}),
                                data=valid_courier_patch,
                                content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class GetPostOrdersTest(TestCase):
    def test_post_valid_orders(self):
        response = client.post(path=reverse('orders-list'),
                               data=valid_orders,
                               content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

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


class AssignOrderTest(TestCase):
    def setUp(self):
        CourierType.objects.create(courier_type="foot", capacity=10, earnings_coef=2)
        CourierType.objects.create(courier_type="bike", capacity=15, earnings_coef=5)
        CourierType.objects.create(courier_type="car", capacity=50, earnings_coef=9)
        client.post(path=reverse('couriers-list'),
                    data=valid_couriers,
                    content_type='application/json')
        client.post(path=reverse('orders-list'),
                    data=valid_orders,
                    content_type='application/json')

    def test_assign_valid(self):
        response = client.post(path=reverse('order-assign'),
                               data=valid_assign,
                               content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_assign_invalid(self):
        response = client.post(path=reverse('order-assign'),
                               data=invalid_assign,
                               content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CompleteOrderTest(TestCase):
    def setUp(self):
        CourierType.objects.create(courier_type="foot", capacity=10, earnings_coef=2)
        CourierType.objects.create(courier_type="bike", capacity=15, earnings_coef=5)
        CourierType.objects.create(courier_type="car", capacity=50, earnings_coef=9)
        client.post(path=reverse('couriers-list'),
                    data=valid_couriers,
                    content_type='application/json')
        client.post(path=reverse('orders-list'),
                    data=valid_orders,
                    content_type='application/json')

    def test_complete_valid(self):
        response_assign = client.post(path=reverse('order-assign'),
                                      data=valid_assign,
                                      content_type='application/json')
        assigned_orders = json.loads(response_assign.content)['orders']
        print(assigned_orders)
        response_complete = client.post(path=reverse('order-complete'),
                                        data=valid_complete,
                                        content_type='application/json')
        print(response_complete.content)
        self.assertEqual(response_complete.status_code, status.HTTP_200_OK)

    # def test_assign_invalid(self):
    #     response = client.post(path=reverse('order-assign'),
    #                            data=invalid_assign,
    #                            content_type='application/json')
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
