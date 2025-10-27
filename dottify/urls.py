
# Write your URL patterns here.

from django.contrib import admin
from django.urls import path, include
from rest_framework_nested import routers 

# Write your URL patterns here.

from .api_views import AlbumViewSet, SongViewSet, PlaylistViewSet, NestedSongViewSet, StatisticsAPIView

router = routers.DefaultRouter()
router.register(r'albums', AlbumViewSet)
router.register(r'songs', SongViewSet)
router.register(r'playlists', PlaylistViewSet)

album_router = routers.NestedSimpleRouter(router, r'albums', lookup='album')
album_router.register(r'songs', NestedSongViewSet, basename='album_songs')

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/', include(album_router.urls)),
    path('api/statistics/', StatisticsAPIView.as_view(), name = 'statistics')
]

