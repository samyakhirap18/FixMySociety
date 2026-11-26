from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, ComplaintViewSet, DashboardView, SocietyViewSet, WorkerViewSet
router = DefaultRouter()
router.register('societies', SocietyViewSet, basename='society')
router.register('categories', CategoryViewSet, basename='category')
router.register('complaints', ComplaintViewSet, basename='complaint')
router.register('workers', WorkerViewSet, basename='worker')
urlpatterns = [path('', include(router.urls)), path('dashboard/', DashboardView.as_view(), name='dashboard')]
