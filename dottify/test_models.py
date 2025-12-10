from datetime import date, timedelta
from django.utils import timezone
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from .models import Album, Song, Playlist, Comment, Rating, DottifyUser


class AlbumModelTests(TestCase):
    def test_release_days_can_not_be_more_than_6_months_in_the_future(self):
        a = Album(
            title="Future OK",
            artist_name="Artist",
            release_date=timezone.now().date() + timedelta(days=180),
            retail_price="5.00",
        )
        a.full_clean()
        a.save()

        a_invalid = Album(
            title="181 days in the future",
            artist_name="Artist",
            release_date=timezone.now().date() + timedelta(days=181),
            retail_price="5.00",
        )
        self.assertRaises(ValidationError, a_invalid.full_clean)

    def test_retail_price_within_0_and_less_than_1000(self):
        a = Album(
            title="Max Price",
            artist_name="Artist",
            release_date=timezone.now().date(),
            retail_price="999.99",
        )
        a.full_clean()
        a.save()

        a_negative = Album(
            title="Negative Price",
            artist_name="Artist",
            release_date=timezone.now().date(),
            retail_price="-1",
        )
        self.assertRaises(ValidationError, a_negative.full_clean)

        a_overMax = Album(
            title="Over 999.99",
            artist_name="Artist",
            release_date=timezone.now().date(),
            retail_price="1000.00",
        )
        self.assertRaises(ValidationError, a_overMax.full_clean)

    def test_slug_is_set_from_title(self):
        a = Album.objects.create(
            title="Test Slug Album",
            artist_name="Artist",
            release_date=timezone.now().date(),
            retail_price="5.00",
        )
        assert a.slug == "test-slug-album"

    def test_title_artist_format_must_be_unique(self):
        Album.objects.create(
            title="Test Unique",
            artist_name="Artist",
            format="SNGL",
            release_date=timezone.now().date(),
            retail_price="5.00",
        )
        duplicate = Album(
            title="Test Unique",
            artist_name="Artist",
            format="SNGL",
            release_date=timezone.now().date(),
            retail_price="6.00",
        )
        self.assertRaises(IntegrityError, duplicate.save)


class SongModelTests(TestCase):
    def setUp(self):
        self.album = Album.objects.create(
            title="Album",
            artist_name="Artist",
            release_date=timezone.now().date(),
            retail_price="5.00",
        )

    def test_song_length_must_be_at_least_10_seconds(self):
        s = Song(title="Song", album=self.album, length=10)
        s.full_clean()
        s.save()

        s_less = Song(title="Too Short", album=self.album, length=9)
        self.assertRaises(ValidationError, s_less.full_clean)

    def test_song_position_is_incremented_per_album(self):
        s1 = Song.objects.create(title="Track 1", album=self.album, length=20)
        s2 = Song.objects.create(title="Track 2", album=self.album, length=30)
        s3 = Song.objects.create(title="Track 3", album=self.album, length=40)

        assert s1.position == 1
        assert s2.position == 2
        assert s3.position == 3

    def test_song_title_is_unique_in_album(self):
        Song.objects.create(title="Unique Song", album=self.album, length=20)
        duplicate = Song(title="Unique Song", album=self.album, length=30)
        self.assertRaises(IntegrityError, duplicate.save)


class DottifyUserTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            "Geldi", "gl00610@surrey.ac.uk", "password"
        )
        self.profile = DottifyUser.objects.create(
            user=self.user,
            display_name="gl00610",
        )

    def test_dottify_user_links_to_django_user_and_display_name(self):
        assert self.profile.user.username == "Geldi"
        assert self.profile.display_name == "gl00610"


class PlaylistModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            "Geldi", "gl00610@surrey.ac.uk", "password"
        )
        self.profile = DottifyUser.objects.create(
            user=self.user,
            display_name="gl00610",
        )
        self.album = Album.objects.create(
            title="Album",
            artist_name="Artist",
            release_date=date(2025, 1, 1),
            retail_price="5.00",
        )
        self.song = Song.objects.create(
            title="Test",
            album=self.album,
            length=281,
        )

    def test_playlist_owner_visibility_created_at_and_songs(self):
        p = Playlist(name="Test", owner=self.profile)
        p.full_clean()
        p.save()

        assert p.owner == self.profile

        assert p.visibility == 0

        assert p.created_at is not None

        p.songs.add(self.song)
        assert p.songs.count() == 1
        assert self.song in p.songs.all()


class RatingModelTests(TestCase):
    def setUp(self):
        self.album = Album.objects.create(
            title="Album",
            artist_name="Artist",
            release_date=timezone.now().date(),
            retail_price="5.00",
        )

    def test_valid_rating_example(self):
        r = Rating(album=self.album, stars=Decimal("2.5"))
        r.full_clean()
        r.save()
        assert Rating.objects.count() == 1

    def test_rating_must_be_in_range_and_half_point_steps(self):
        r1 = Rating(album=self.album, stars=Decimal("5.5"))
        self.assertRaises(ValidationError, r1.full_clean)

        r2 = Rating(album=self.album, stars=Decimal("3.3"))
        self.assertRaises(ValidationError, r2.full_clean)


class CommentModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            "Geldi", "gl00610@surrey.ac.uk", "password"
        )
        self.profile = DottifyUser.objects.create(
            user=self.user,
            display_name="gl00610",
        )
        self.album = Album.objects.create(
            title="Album",
            artist_name="Artist",
            release_date=timezone.now().date(),
            retail_price="5.00",
        )

    def test_comment_links_to_album_and_dottify_user(self):
        c = Comment.objects.create(
            comment_text="Test",
            album=self.album,
            user=self.profile,
        )
        assert c.album == self.album
        assert c.user == self.profile
        assert c.comment_text == "Test"
