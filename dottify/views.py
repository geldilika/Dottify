from datetime import timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, UpdateView, DeleteView, DetailView
from django.http import HttpResponse, HttpResponseForbidden
from django.urls import reverse, reverse_lazy
from django.utils.text import slugify
from django.utils import timezone

from .forms import AlbumForm, SongForm
from .models import Album, Song, Playlist, DottifyUser, Rating, Comment

# Create your views here.

def is_admin(user):
    return user.is_authenticated and user.groups.filter(name="DottifyAdmin").exists()

def is_artist(user):
    return user.is_authenticated and user.groups.filter(name="Artist").exists()

def home(request):
    user = request.user
    albums = None
    playlists = None
    songs = None

    if not user.is_authenticated:
        albums = Album.objects.all()
        playlists = Playlist.objects.filter(visibility=2)
        return render(request, "home.html", {"albums": albums, "playlists": playlists, "songs": songs})

    if not (is_artist(user) or is_admin(user)):
        playlists = Playlist.objects.filter(owner__user=user)
        return render(request, "home.html", {"albums": albums, "playlists": playlists, "songs": songs})

    if is_artist(user) and not is_admin(user):
        albums = Album.objects.filter(artist_account__user=user)
        return render(request, "home.html", {"albums": albums, "playlists": playlists, "songs": songs})

    if is_admin(user):
        albums = Album.objects.all()
        playlists = Playlist.objects.all()
        songs = Song.objects.all()
        return render(request, "home.html", {"albums": albums, "playlists": playlists, "songs": songs})

    playlists = Playlist.objects.filter(owner__user=user)
    return render(request, "home.html", {"albums": albums, "playlists": playlists, "songs": songs})

def album_search(request):
    if not request.user.is_authenticated:
        return HttpResponse(status = 401)
    q = request.GET.get("q", "").strip()
    if q == "":
        albums = Album.objects.all()
    else:
        albums = Album.objects.filter(title__icontains=q)
    
    return render(request, "album_search.html", {"albums": albums, "q":q})

class AlbumCreateView(LoginRequiredMixin, CreateView):
    model = Album
    form_class = AlbumForm
    template_name = "album_form.html"

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
        return reverse("album_detail", kwargs={"pk": self.object.pk})

def album_detail(request, pk, slug=None):
    album = get_object_or_404(Album, pk=pk)
    songs = album.songs.all()
    comments = Comment.objects.filter(album=album).select_related("user")
    ratings = Rating.objects.filter(album=album)

    total_alltime = 0
    count_alltime = 0
    for r in ratings:
        total_alltime += float(r.stars)
        count_alltime += 1
    
    if count_alltime > 0:
        average_alltime = total_alltime / count_alltime
    else:
        average_alltime = 0
    average_alltime_str = f"{average_alltime:.1f}"

    cutoff = timezone.now() - timedelta(days=30)
    total_recent = 0
    count_recent = 0
    for r in ratings:
        if r.created_at >= cutoff:
            total_recent += float(r.stars)
            count_recent += 1

    if count_recent > 0:
        average_recent = total_recent / count_recent
    else:
        average_recent = 0.0
    average_recent_str = f"{average_recent:.1f}"

    return render(request, "album_detail.html", {"album": album, "songs": songs, "comments": comments,
    "average_alltime_str": average_alltime_str, "average_recent_str": average_recent_str})

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
        return reverse("album_detail", args=[self.object.pk])

class AlbumDeleteView(LoginRequiredMixin, DeleteView):
    model = Album
    template_name = "album_delete.html"
    success_url = reverse_lazy("home")

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
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
        return reverse("song_detail", args = [self.object.pk])
    
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
            album = self.object.album
            if not album or not album.artist_account or album.artist_account.user_id != user.id:
                return HttpResponseForbidden("You are not allowed to edit this song")
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        user = self.request.user
        if is_artist(user) and not is_admin(user):
            album = form.instance.album
            if not album or not album.artist_account or album.artist_account.user_id != user.id:
                return HttpResponseForbidden("You can only move songs within your own albums.")
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse("song_detail", args=[self.object.pk])
    
class SongDeleteView(LoginRequiredMixin, DeleteView):
    model = Song
    template_name = "song_delete.html"
    success_url = reverse_lazy("home")

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        user = self.request.user

        if is_admin(user):
            return super().dispatch(request, *args, **kwargs)
        
        if is_artist(user):
            album = self.object.album
            if album and album.artist_account and album.artist_account.user_id == user.id:
                return super().dispatch(request, *args, **kwargs)
        return HttpResponseForbidden("You cant delete this Song")
    

class UserRedirectView(DetailView):
    model = DottifyUser
    def get(self, request, *args, **kwargs):
        pk = kwargs["pk"]
        profile = get_object_or_404(DottifyUser, pk=pk)
        return redirect("user_detail", pk=pk, display_slug=slugify(profile.display_name))
    
class UserDetailView(DetailView):
    model = DottifyUser
    template_name = "user_detail.html"
    context_object_name = "profile"

    def get_object(self, queryset = None):
        return get_object_or_404(DottifyUser, pk=self.kwargs["pk"])
    
    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        correct = slugify(self.object.display_name)
        if self.kwargs.get("display_slug") != correct:
            return redirect("user_detail", pk=self.object.pk, display_slug=correct)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["playlists"] = Playlist.objects.filter(owner=self.object)
        return ctx