from django.db import models

# Create your models here.

from django.template.defaultfilters import slugify
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
from django.core.validators import MaxValueValidator, MinValueValidator
from decimal import Decimal
from django.contrib.auth.models import User

def validate_release_date(value):
    today = datetime.now().date()
    if value > today + timedelta(days = 180):
        raise ValidationError("Release days cant be more than 6 months")
    
def validate_rating(value):
    v = Decimal(str(value))
    if (v < Decimal("0.0") or v > Decimal("5.0")):
        raise ValidationError("Starts must be between 0 and 5")
    if (v * 2) % 1 != 0:
        raise ValidationError("Stars must be in increments of 0.5")
    
class Album(models.Model):
    FORMAT_CHOICES = [
        ('SNGL','Single'),
        ('RMST', 'Remaster'),
        ('DLUX', 'Deluxe Edition'),
        ('COMP', 'Compilation'),
        ('LIVE', 'Live Recording'),
    ]
    cover_image = models.ImageField(default = "no_cover.jpg", blank = True, null = True)
    title = models.CharField(max_length = 800)
    artist_name = models.CharField(max_length = 800, blank = False, null = False)
    artist_account = models.ForeignKey("DottifyUser", on_delete = models.SET_NULL, null = True, blank = True)
    retail_price = models.DecimalField(max_digits = 5, decimal_places = 2, validators = [MinValueValidator(Decimal("0.00")), MaxValueValidator(Decimal("999.99"))], blank = False, null = False)
    format = models.CharField(max_length = 4, choices = FORMAT_CHOICES, blank = True, null = True)
    release_date = models.DateField(validators = [validate_release_date])
    slug = models.SlugField(max_length = 800, null = True, blank = True, editable = False)

    def save(self,*args, **kwargs):
        self.slug = slugify(self.title or "")
        return super().save(*args, **kwargs)

    class Meta:
        constraints = [models.UniqueConstraint(fields = ['title', 'artist_name', 'format'], name ='unique_title_artist_format')]

class Song(models.Model):
    title = models.CharField(max_length = 800, null = False, blank = False)
    length = models.PositiveIntegerField(validators = [MinValueValidator(10)])
    position = models.PositiveIntegerField(null = True, blank = True, editable = False)
    album = models.ForeignKey("Album", on_delete=models.CASCADE, related_name="songs")

    class Meta:
        constraints = [models.UniqueConstraint(fields = ["album", "title"], name = "unique_album_title")]

    def save(self, *args, **kwargs):
        if self.pk is None and self.position is None:
            last = (
                self.__class__.objects.filter(album_id = self.album_id).order_by("-position").first()
            )
            if last and last.position:
                self.position = last.position + 1
            else:
                self.position = 1
        return super().save(*args,**kwargs)

class Playlist(models.Model):
    VISIBILITY_CHOICES = [
        (0, "Hidden"),
        (1, "Unlisted"),
        (2, "Public"),
    ]
    name = models.CharField(max_length = 800)
    created_at = models.DateTimeField(auto_now_add= True)
    songs = models.ManyToManyField('Song', blank = True, related_name = 'playlists')
    visibility = models.IntegerField(choices = VISIBILITY_CHOICES, default = 0)
    owner = models.ForeignKey("DottifyUser", on_delete=models.CASCADE)

class DottifyUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    display_name = models.CharField(max_length = 800)

class Rating(models.Model):
    stars = models.DecimalField(max_digits = 2, decimal_places = 1, validators = [MinValueValidator(Decimal("0.0")), MaxValueValidator(Decimal("5.0")), validate_rating])

class Comment(models.Model):
    comment_text = models.CharField(max_length = 800)
