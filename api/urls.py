from rest_framework.routers import DefaultRouter

from api.views.category import CategoryViewSet

router = DefaultRouter()
urlpatterns = []

router.register(r'categories', CategoryViewSet, basename='category')

urlpatterns += router.urls
