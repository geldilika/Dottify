# Any form helpers should go in this file.
from django import forms
from .models import Album, Song


class AlbumForm(forms.ModelForm):
    class Meta:
        model = Album
        fields = [
            "cover_image", "title", "artist_name",
            "retail_price", "format", "release_date"
        ]


class SongForm(forms.ModelForm):
    class Meta:
        model = Song
        fields = [
            "title", "length", "album"]
