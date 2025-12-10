from rest_framework.test import APITestCase
from rest_framework import status

from django.contrib.auth.models import User
from .models import Album, Song, Playlist, DottifyUser


class APITests(APITestCase):

    def setUp(self):
        self.album = Album.objects.create(
            title="Album",
            format="SNGL",
            artist_name="Artist",
            release_date="2025-01-01",
            retail_price="5.00",
        )
        self.song1 = Song.objects.create(
            title="First Track",
            album=self.album,
            length=120,
        )
        self.song2 = Song.objects.create(
            title="Second Track",
            album=self.album,
            length=240,
        )

        u = User.objects.create_user(
            "Geldi", "gl00610@surrey.ac.uk", "password"
        )
        self.dottify_user = DottifyUser.objects.create(
            user=u,
            display_name="gl00610",
        )

        self.public_playlist = Playlist.objects.create(
            name="Public",
            owner=self.dottify_user,
            visibility=2,
        )
        self.public_playlist.songs.add(self.song1, self.song2)

        self.hidden_playlist = Playlist.objects.create(
            name="Hidden",
            owner=self.dottify_user,
            visibility=0,
        )
        self.hidden_playlist.songs.add(self.song1)

    def test_album_api_hides_artist_account_and_has_song_titles(self):
        url = f"/api/albums/{self.album.id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertNotIn("artist_account", data)

        self.assertIn("song_set", data)
        self.assertEqual(
            sorted(data["song_set"]),
            ["First Track", "Second Track"]
        )

    def test_song_api_does_not_expose_position(self):
        url = f"/api/songs/{self.song1.id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertIn("id", data)
        self.assertIn("title", data)
        self.assertIn("length", data)
        self.assertIn("album", data)

        self.assertNotIn("position", data)

    def test_playlist_list_returns_only_public_playlists(self):
        response = self.client.get("/api/playlists/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        names = []
        for p in data:
            names.append(p["name"])

        self.assertIn("Public", names)
        self.assertNotIn("Hidden", names)

    def test_playlist_owner_is_display_name_and_songs_are_hyperlinks(self):
        url = f"/api/playlists/{self.public_playlist.id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertIn("owner", data)
        self.assertEqual(data["owner"], "gl00610")

        self.assertIn("songs", data)
        self.assertGreater(len(data["songs"]), 0)
        for s in data["songs"]:
            self.assertIsInstance(s, str)
            self.assertTrue(s.startswith("http"))

    def test_album_nested_song_list_is_scoped_to_album(self):
        url = f"/api/albums/{self.album.id}/songs/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        titles = []
        for s in data:
            titles.append(s["title"])

        self.assertIn("First Track", titles)
        self.assertIn("Second Track", titles)

    def test_album_nested_song_detail_404_if_song_not_in_album(self):
        other_album = Album.objects.create(
            title="Other Album",
            artist_name="Other Artist",
            release_date="2025-02-01",
            retail_price="5.00",
        )
        other_song = Song.objects.create(
            title="Other Song",
            album=other_album,
            length=180,
        )

        url = f"/api/albums/{self.album.id}/songs/{other_song.id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_statistics_api_has_expected_keys_and_counts(self):
        response = self.client.get("/api/statistics/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        for key in ["playlist_count", "user_count",
                    "album_count", "song_length_average"]:
            self.assertIn(key, data)

        self.assertEqual(data["playlist_count"], 1)

        self.assertEqual(data["user_count"], DottifyUser.objects.count())
        self.assertEqual(data["album_count"], Album.objects.count())

        self.assertTrue(data["song_length_average"] > 0)
