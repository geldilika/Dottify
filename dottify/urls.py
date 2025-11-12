
# Write your URL patterns here.

from django.contrib import admin
from django.urls import path, include
from rest_framework_nested import routers 

# Write your URL patterns here.

from .api_views import AlbumViewSet, SongViewSet, PlaylistViewSet, NestedSongViewSet, StatisticsAPIView
from .views import home, album_search, album_detail, AlbumCreateView, AlbumUpdateView, AlbumDeleteView, SongDetailView, SongCreateView, SongUpdateView, SongDeleteView, UserRedirectView, UserDetailView


router = routers.DefaultRouter()
router.register(r'albums', AlbumViewSet)
router.register(r'songs', SongViewSet)
router.register(r'playlists', PlaylistViewSet)

album_router = routers.NestedSimpleRouter(router, r'albums', lookup='album')
album_router.register(r'songs', NestedSongViewSet, basename='album_songs')

urlpatterns = [
        path("", home, name="home"),

        path("albums/search/", album_search, name="album_search"),
        path("albums/new/",               AlbumCreateView.as_view(), name="album_create"),
        path("albums/<int:pk>/",          album_detail,              name="album_detail"),
        path("albums/<int:pk>/<slug:slug>/", album_detail,           name="album_detail_slug"),
        path("albums/<int:pk>/edit/",     AlbumUpdateView.as_view(), name="album_edit"),
        path("albums/<int:pk>/delete/",   AlbumDeleteView.as_view(), name="album_delete"),

        path("songs/new/",            SongCreateView.as_view(), name="song_create"),
        path("songs/<int:pk>/",       SongDetailView.as_view(), name="song_detail"),
        path("songs/<int:pk>/edit/",  SongUpdateView.as_view(), name="song_edit"),
        path("songs/<int:pk>/delete/",SongDeleteView.as_view(), name="song_delete"),

        path("users/<int:pk>/",                        UserRedirectView.as_view(), name="user_redirect"),
        path("users/<int:pk>/<slug:display_slug>/",    UserDetailView.as_view(),   name="user_detail"),

        path("api/", include(router.urls)),
        path("api/", include(album_router.urls)),
        path("api/statistics/", StatisticsAPIView.as_view(), name="statistics"),
]

