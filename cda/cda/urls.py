from django.contrib import admin
from django.urls import path, re_path
from cdrestapp import views

urlpatterns = [
	path('admin/', admin.site.urls),
	re_path(r'^couriers/(?P<pk>\d+)$', views.CourierDetailAPIView.as_view(), name='courier-detail'),
	re_path(r'^orders/complete', views.OrderCompleteAPIView.as_view(), name='order-complete'),
	re_path(r'^couriers', views.CourierAPIView.as_view(), name='couriers-list'),
	re_path(r'^orders/assign', views.OrderAssignAPIView.as_view(), name='order-assign'),
	re_path(r'^orders', views.OrderAPIView.as_view(), name='orders-list'),
	re_path(r'^courier-types', views.CourierTypeAPIView.as_view(), name='courier-types-list'),
]
