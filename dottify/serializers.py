# Write your API serialisers here.

from rest_framework import serializers
from .models import Album, Song, Playlist

class AlbumSerializer(serializers.ModelSerializer):
    song_set = serializers.SerializerMethodField(read_only = True)

    class Meta:
        model = Album
        fields = [
            "id", "title", "artist_name", "retail_price", "format", "release_date", "slug", "cover_image", "song_set"
        ]
    
    def get_song_set(self, obj):
        titles = []
        for s in obj.songs.all():
            titles.append(s.title)
        return titles

class SongSerializer(serializers.ModelSerializer):
    class Meta:
        model = Song
        fields = [
            "id", "title", "length", "album"
        ]

class PlaylistSerializer(serializers.ModelSerializer):
    owner = serializers.CharField(source = "owner.display_name", read_only = True)
    songs = serializers.HyperlinkedRelatedField(many = True, read_only = True, view_name = "song-detail")

    class Meta:
        model = Playlist
        fields = [
            "id", "name", "created_at", "visibility", "owner", "songs"
        ]

