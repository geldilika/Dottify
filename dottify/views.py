from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, UpdateView, DeleteView, DetailView
from django.http import HttpResponseForbidden
from django.urls import reverse_lazy

from .forms import AlbumForm, SongForm
from .models import Album, Song, Playlist, DottifyUser

# Create your views here.

def is_admin(user):
    return user.is_authenticated and user.groups.filter(name="DottifyAdmin").exists()

def is_artist(user):
    return user.is_authenticated and user.groups.filter(name="Artist").exists()


def home(request):
    user = request.user

    albums = Album.objects.all()
    playlists = Playlist.objects.filter(visibility=2)
    songs = None

    if user.is_authenticated:
        playlists = Playlist.objects.filter(owner__user = user)

        if user.groups.filter(name="Artist").exists():
            albums = Album.objects.filter(artist_account__user = user)

        if is_admin(user):
            albums = Album.objects.all()
            playlists = Playlist.objects.all()
            songs = Song.objects.all()
    
    return render(request, "home.html", {
        "albums": albums, "playlists": playlists, "songs": songs,
    })

@login_required
def album_search(request):
    q = request.GET.get("q", "")
    if q == "":
        albums = Album.objects.all()
    else:
        albums = Album.objects.filter(title__icontains=q)
    
    return render(request, "album_search.html", {"albums": albums, "q":q})

class AlbumCreateView(LoginRequiredMixin, CreateView):
    model = Album
    form_class = AlbumForm
    template_name = "dottify/album_form.html"

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if not(is_artist(user) or is_admin(user)):
            return HttpResponseForbidden("You must be an artist or DottifyAdmin")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = self.request.user
        if is_artist(user):
            profile = DottifyUser.objects.filter(user = user).first()
            if not profile:
                return HttpResponseForbidden("Artist profile missing.")
            form.instance.artist_account = profile
        return super().form_valid(form)
    
    def get_success_url(self):
        return super().get_success_url()

def album_details(request, pk, slug=None):
    album = get_object_or_404(Album, pk=pk)
    songs = album.songs.all()
    return render(request, "album_detail.html", {"album": album, "songs": songs})

class AlbumUpdateView(LoginRequiredMixin, UpdateView):
    model = Album
    form_class = AlbumForm
    template_name = "album_form.html"

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if not(is_artist(user) or is_admin(user)):
            return HttpResponseForbidden("You must be an artist or DottifyAdmin")
        self.object = self.get_object()
        if is_artist(user) and not is_admin(user):
            if not self.object.artist_account or self.object.artist_account.user_id != user.id:
                return HttpResponseForbidden("You dont own the album")
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return super().get_success_url()

class AlbumDeleteView(DeleteView, LoginRequiredMixin):
    model = Album
    template_name = "album_delete.html"
    success_url = reverse_lazy("home")

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object
        user = self.request.user
        if is_admin(user):
            return super().dispatch(request, *args, **kwargs)
        if is_artist(user):
            if self.object.artist_account and self.object.artist_account.user_id == user.id:
                return super().dispatch(request, *args, **kwargs)
        return HttpResponseForbidden("You cant delete this album")
    
class SongCreateView(LoginRequiredMixin, CreateView):
    model = Song
    form_class = SongForm
    template_name = "song_form.html"

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if not(is_artist(user) or is_admin(user)):
            return HttpResponseForbidden("You must be an artist or DottifyAdmin")
        return super().dispatch(request, *args, **kwargs)    

    def form_valid(self, form):
        user = self.request.user
        if is_artist(user):
            profile = DottifyUser.objects.filter(user = user).first()
            if not profile:
                return HttpResponseForbidden("Artist profile missing.")
            
            album = form.instance.album
            if not album or album.artist_account_id != profile.id:
                return HttpResponseForbidden("You can only add songs to your own album")
        return super().form_valid(form)
    
    def get_success_url(self):
        return super().get_success_url()
    
class SongDetailView(DetailView):
    model = Song
    template_name = "song_detail.html"

class SongUpdateView(LoginRequiredMixin, UpdateView):
    model = Song
    form_class = SongForm
    template_name = "song_form.html"

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if not(is_artist(user) or is_admin(user)):
            return HttpResponseForbidden("You must be an artist or DottifyAdmin")
        self.object = self.get_object()
        if is_artist(user) and not is_admin(user):
            if not self.object.artist_account or self.object.artist_account.user_id != user.id:
                return HttpResponseForbidden("You are not allowed to edit this song")
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        user = self.request.user
        if is_artist(user) and not is_admin(user):
            album = form.instance.album
            if not album or album.artist_account.user_id != user.id:
                return HttpResponseForbidden("You can only move songs within your own albums.")
        return super().form_valid(form)
    
    def get_success_url(self):
        return super().get_success_url()
    
class SongDeleteView(LoginRequiredMixin, DeleteView):
    model = Song
    template_name = "song_delete.html"
    success_url= reverse_lazy("home")
    album_id = None

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object
        user = self.request.user
        self.album_id = self.object.album_id

        if is_admin(user):
            return super().dispatch(request, *args, **kwargs)
        if is_artist(user):
            owner = self.object.album.artist_account
            if owner and owner.user_id == user.id:
                return super().dispatch(request, *args, **kwargs)
        return HttpResponseForbidden("You cant delete this Song")

 