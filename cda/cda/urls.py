"""cda URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
	https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
	1. Add an import:  from my_app import views
	2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
	1. Add an import:  from other_app.views import Home
	2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
	1. Import the include() function: from django.urls import include, path
	2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path
from cdrestapp import views

# TODO names ?
urlpatterns = [
	path('admin/', admin.site.urls),
	path(r'courier-type', views.CourierTypeAPIView.as_view(), name='courier-types-list'),  # TODO fix this
	path(r'couriers', views.CourierAPIView.as_view(), name='couriers-list'),
	re_path(r'^couriers/(?P<pk>\d+)$', views.CourierDetailAPIView.as_view(), name='courier-detail'),
	path('orders', views.OrderAPIView.as_view(), name='orders-list'),
	path(r'regions', views.CourierRegionsAPIView.as_view(), name='courier-regions-list'),
	path(r'orders/assign', views.OrderAssignAPIView.as_view(), name='order-assign'),
	path(r'orders/complete', views.OrderCompleteAPIView.as_view(), name='order-complete'),
]
