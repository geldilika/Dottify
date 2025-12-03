from datetime import date

from django.test import TestCase
from django.contrib.auth.models import User, Group
from django.urls import reverse

from .models import Album, Song, Playlist, DottifyUser, Rating, Comment


class ViewAndAuthTests(TestCase):
    def setUp(self):
        self.artist_group = Group.objects.create(name="Artist")
        self.admin_group = Group.objects.create(name="DottifyAdmin")

        self.normal_user = User.objects.create_user(
            username="normal",
            email="normal@user.com",
            password="password",
        )
        self.normal_profile = DottifyUser.objects.create(
            user=self.normal_user,
            display_name="NormalUser",
        )

        self.artist_user = User.objects.create_user(
            username="artist",
            email="artist@user.com",
            password="password",
        )
        self.artist_user.groups.add(self.artist_group)
        self.artist_profile = DottifyUser.objects.create(
            user=self.artist_user,
            display_name="ArtistUser",
        )

        self.other_artist_user = User.objects.create_user(
            username="otherArtist",
            email="otherArtist@user.com",
            password="password",
        )
        self.other_artist_user.groups.add(self.artist_group)
        self.other_artist_profile = DottifyUser.objects.create(
            user=self.other_artist_user,
            display_name="OtherArtistUser",
        )

        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@user.com",
            password="password",
        )
        self.admin_user.groups.add(self.admin_group)
        self.admin_profile = DottifyUser.objects.create(
            user=self.admin_user,
            display_name="AdminUser",
        )

        self.artist_album = Album.objects.create(
            title="Album",
            artist_name="Artist",
            artist_account=self.artist_profile,
            release_date=date.today(),
            retail_price="5.00",
        )
        self.other_album = Album.objects.create(
            title="Other Album",
            artist_name="Other Name",
            artist_account=self.other_artist_profile,
            release_date=date.today(),
            retail_price="6.00",
        )

        self.artist_song = Song.objects.create(
            title="Song",
            album=self.artist_album,
            length=120,
        )
        self.other_song = Song.objects.create(
            title="Other Song",
            album=self.other_album,
            length=150,
        )

        self.public_playlist = Playlist.objects.create(
            name="Public",
            owner=self.artist_profile,
            visibility=2,
        )
        self.public_playlist.songs.add(self.artist_song)

        self.private_playlist = Playlist.objects.create(
            name="Private",
            owner=self.normal_profile,
            visibility=0,
        )
        self.private_playlist.songs.add(self.artist_song)

        Rating.objects.create(album=self.artist_album, stars="4.0")
        Rating.objects.create(album=self.artist_album, stars="2.0")
        Comment.objects.create(
            comment_text="Test",
            album=self.artist_album,
            user=self.normal_profile,
        )

    def test_home_for_normal_user_only_shows_their_playlists(self):
        self.client.login(username="normal", password="password")
        response = self.client.get(reverse("home"))
        self.client.logout()

        self.assertEqual(response.status_code, 200)

        albums = response.context.get("albums")
        songs = response.context.get("songs")
        playlists = response.context.get("playlists")

        self.assertIsNone(albums)
        self.assertIsNone(songs)

        names = []
        for p in playlists:
            names.append(p.name)

        self.assertIn("Private", names)
        self.assertNotIn("Public", names)

    def test_home_for_artist_only_shows_their_albums(self):
        self.client.login(username="artist", password="password")
        response = self.client.get(reverse("home"))
        self.client.logout()

        self.assertEqual(response.status_code, 200)

        albums = response.context.get("albums")
        playlists = response.context.get("playlists")
        songs = response.context.get("songs")

        self.assertIsNone(playlists)
        self.assertIsNone(songs)

        titles = []
        for a in albums:
            titles.append(a.title)

        self.assertIn("Album", titles)
        self.assertNotIn("Other Album", titles)

    def test_home_for_admin_shows_all_albums_playlists_and_songs(self):
        self.client.login(username="admin", password="password")
        response = self.client.get(reverse("home"))
        self.client.logout()

        self.assertEqual(response.status_code, 200)

        albums = response.context.get("albums")
        playlists = response.context.get("playlists")
        songs = response.context.get("songs")

        self.assertEqual(albums.count(), Album.objects.count())
        self.assertEqual(playlists.count(), Playlist.objects.count())
        self.assertEqual(songs.count(), Song.objects.count())


    def test_album_search_returns_only_matching_titles_for_logged_in_user(self):
        Album.objects.create(
            title="Testing Q",
            artist_name="Artist",
            release_date=date.today(),
            retail_price="3.00",
        )

        self.client.login(username="normal", password="password")
        response = self.client.get(reverse("album_search") + "?q=Testing")
        self.client.logout()

        self.assertEqual(response.status_code, 200)
        albums = response.context.get("albums")

        titles = []
        for a in albums:
            titles.append(a.title)

        self.assertIn("Testing Q", titles)
        self.assertNotIn("Album", titles)
        self.assertNotIn("Other Album", titles)

    def test_album_create_for_normal_user_returns_403(self):
        self.client.login(username="normal", password="password")
        response = self.client.get(reverse("album_create"))
        self.client.logout()

        self.assertEqual(response.status_code, 403)

    def test_artist_creating_album_means_artist_account_equal_dottify_user(self):
        self.client.login(username="artist", password="password")
        response = self.client.post(
            reverse("album_create"),
            data={
                "cover_image": "",
                "title": "New Album",
                "artist_name": "Name",
                "retail_price": "7.50",
                "format": "",
                "release_date": "2025-01-01",
            },
        )
        self.client.logout()

        self.assertEqual(response.status_code, 302)
        created = Album.objects.get(title="New Album")
        self.assertEqual(created.artist_account, self.artist_profile)

    def test_song_create_for_normal_user_returns_403(self):
        self.client.login(username="normal", password="password")
        response = self.client.get(reverse("song_create"))
        self.client.logout()

        self.assertEqual(response.status_code, 403)

    def test_artist_cannot_add_song_to_album_they_do_not_own(self):
        self.client.login(username="artist", password="password")
        response = self.client.post(
            reverse("song_create"),
            data={
                "title": "Invalid",
                "length": 100,
                "album": self.other_album.pk,
            },
        )
        self.client.logout()

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Song.objects.filter(title="Invalid").exists())

    def test_artist_can_add_song_to_own_album(self):
        self.client.login(username="artist", password="password")
        response = self.client.post(
            reverse("song_create"),
            data={
                "title": "New Song",
                "length": 130,
                "album": self.artist_album.pk,
            },
        )
        self.client.logout()

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Song.objects.filter(title="New Song").exists())

    def test_artist_cannot_edit_song_for_album_they_do_not_own(self):
        self.client.login(username="artist", password="password")
        response = self.client.get(
            reverse("song_edit", kwargs={"pk": self.other_song.pk})
        )
        self.client.logout()

        self.assertEqual(response.status_code, 403)

    def test_admin_can_add_song_to_any_album(self):
        self.client.login(username="admin", password="password")
        response = self.client.post(
            reverse("song_create"),
            data={
                "title": "Admin Song",
                "length": 200,
                "album": self.other_album.pk,
            },
        )
        self.client.logout()

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Song.objects.filter(title="Admin Song").exists())

    def test_album_edit_artist_cannot_edit_album_they_do_not_own(self):
        self.client.login(username="artist", password="password")
        response = self.client.get(
            reverse("album_edit", kwargs={"pk": self.other_album.pk})
        )
        self.client.logout()

        self.assertEqual(response.status_code, 403)

    def test_album_edit_artist_can_edit_own_album(self):
        self.client.login(username="artist", password="password")
        response = self.client.post(
            reverse("album_edit", kwargs={"pk": self.artist_album.pk}),
            data={
                "cover_image": "",
                "title": "Album Edited",
                "artist_name": "Artist",
                "retail_price": "5.50",
                "format": "",
                "release_date": "2025-01-01",
            },
        )
        self.client.logout()

        self.assertEqual(response.status_code, 302)
        edited = Album.objects.get(pk=self.artist_album.pk)
        self.assertEqual(edited.title, "Album Edited")

    def test_album_edit_admin_can_edit_any_album(self):
        self.client.login(username="admin", password="password")
        response = self.client.post(
            reverse("album_edit", kwargs={"pk": self.other_album.pk}),
            data={
                "cover_image": "",
                "title": "Admin Edited",
                "artist_name": "Other Name",
                "retail_price": "9.99",
                "format": "",
                "release_date": "2025-01-01",
            },
        )
        self.client.logout()

        self.assertEqual(response.status_code, 302)
        edited = Album.objects.get(pk=self.other_album.pk)
        self.assertEqual(edited.title, "Admin Edited")

    def test_album_delete_normal_user_forbidden(self):
        self.client.login(username="normal", password="password")
        response = self.client.get(
            reverse("album_delete", kwargs={"pk": self.artist_album.pk})
        )
        self.client.logout()

        self.assertEqual(response.status_code, 403)

    def test_album_delete_artist_can_delete_own_album(self):
        self.client.login(username="artist", password="password")
        response = self.client.post(
            reverse("album_delete", kwargs={"pk": self.artist_album.pk})
        )
        self.client.logout()

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Album.objects.filter(pk=self.artist_album.pk).exists())

    def test_album_delete_admin_can_delete_any_album(self):
        self.client.login(username="admin", password="password")
        response = self.client.post(
            reverse("album_delete", kwargs={"pk": self.other_album.pk})
        )
        self.client.logout()

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Album.objects.filter(pk=self.other_album.pk).exists())


    def test_normal_user_can_not_delete(self):
        self.client.login(username="normal", password="password")
        response = self.client.get(
            reverse("song_delete", kwargs={"pk": self.artist_song.pk})
        )
        self.client.logout()

        self.assertEqual(response.status_code, 403)

    def test_song_delete_artist_can_delete_own_song(self):
        self.client.login(username="artist", password="password")
        response = self.client.post(
            reverse("song_delete", kwargs={"pk": self.artist_song.pk})
        )
        self.client.logout()

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Song.objects.filter(pk=self.artist_song.pk).exists())

    def test_song_delete_admin_can_delete_any_song(self):
        self.client.login(username="admin", password="password")
        response = self.client.post(
            reverse("song_delete", kwargs={"pk": self.other_song.pk})
        )
        self.client.logout()

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Song.objects.filter(pk=self.other_song.pk).exists())


    def test_album_detail_shows_songs_comments_rating_and_cover_image(self):
        url = reverse("album_detail", kwargs={"pk": self.artist_album.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        album = response.context.get("album")
        songs = response.context.get("songs")
        comments = response.context.get("comments")
        avg_all = response.context.get("average_alltime_str")
        avg_recent = response.context.get("average_recent_str")

        self.assertIsNotNone(album)
        self.assertTrue(album.cover_image.name.endswith("no_cover.jpg"))

        self.assertIsNotNone(songs)
        titles = []
        for s in songs:
            titles.append(s.title)
        self.assertIn("Song", titles)

        self.assertIsNotNone(comments)
        texts = []
        for c in comments:
            texts.append(c.comment_text)
        self.assertIn("Test", texts)

        self.assertEqual(avg_all, "3.0")
        self.assertEqual(avg_recent, "3.0")

    def test_user_detail_shows_display_name_playlists_and_songs(self):
        url = reverse(
            "user_detail",
            kwargs={
                "pk": self.artist_profile.pk,
                "display_slug": self.artist_profile.display_name.lower(),
            },
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        profile = response.context.get("profile")
        playlists = response.context.get("playlists")

        self.assertIsNotNone(profile)
        self.assertEqual(profile.display_name, "ArtistUser")

        self.assertIsNotNone(playlists)
        names = []
        for p in playlists:
            names.append(p.name)
        self.assertIn("Public", names)

        public = None
        for p in playlists:
            if p.name == "Public":
                public = p
                break

        self.assertIsNotNone(public)
        self.assertGreater(public.songs.count(), 0)
    