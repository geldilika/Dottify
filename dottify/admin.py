# dottify/admin.py
from django.contrib import admin
from .models import Album, Song, Playlist, DottifyUser, Rating, Comment


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ("title", "artist_name", "format", "release_date")
    search_fields = ("title", "artist_name")


@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = ("title", "album", "length", "position")
    list_filter = ("album",)


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "visibility", "created_at")
    list_filter = ("visibility",)


@admin.register(DottifyUser)
class DottifyUserAdmin(admin.ModelAdmin):
    list_display = ("display_name", "user")


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ("album", "stars", "created_at")
    list_filter = ("album",)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("album", "user", "comment_text")
    search_fields = ("comment_text",)