# Use this file for your API viewsets only
# E.g., from rest_framework import ...

from rest_framework import viewsets
from .serializers import AlbumSerializer, SongSerializer, PlaylistSerializer
from .models import Album, Song, Playlist, DottifyUser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Avg

# Create your views here.


class AlbumViewSet(viewsets.ModelViewSet):
    queryset = Album.objects.all()
    serializer_class = AlbumSerializer


class SongViewSet(viewsets.ModelViewSet):
    queryset = Song.objects.all()
    serializer_class = SongSerializer


class PlaylistViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PlaylistSerializer

    def get_queryset(self):
        return Playlist.objects.filter(visibility=2)


class NestedSongViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SongSerializer

    def get_queryset(self):
        album_id = self.kwargs['album_pk']
        return Song.objects.filter(album_id=album_id)


class StatisticsAPIView(APIView):

    def get(self, request, format=None):
        agg = Song.objects.aggregate(avg_len=Avg("length"))
        average_len = agg["avg_len"] or 0
        return Response({
            "user_count": DottifyUser.objects.count(),
            "album_count": Album.objects.count(),
            "playlist_count": Playlist.objects.filter(visibility=2).count(),
            "song_length_average": average_len})
