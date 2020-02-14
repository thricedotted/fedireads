''' models for storing different kinds of Activities '''
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from model_utils.managers import InheritanceManager

from fedireads.utils.fields import JSONField

class Activity(models.Model):
    ''' basic fields for storing activities '''
    uuid = models.CharField(max_length=255, unique=True)
    user = models.ForeignKey('User', on_delete=models.PROTECT)
    content = JSONField(max_length=5000)
    # the activitypub activity type (Create, Add, Follow, ...)
    activity_type = models.CharField(max_length=255)
    # custom types internal to fedireads (Review, Shelve, ...)
    fedireads_type = models.CharField(max_length=255, blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    objects = InheritanceManager()


class ShelveActivity(Activity):
    ''' someone put a book on a shelf '''
    book = models.ForeignKey('Book', on_delete=models.PROTECT)
    shelf = models.ForeignKey('Shelf', on_delete=models.PROTECT)

    def save(self, *args, **kwargs):
        if not self.activity_type:
            self.activity_type = 'Add'
        self.fedireads_type = 'Shelve'
        super().save(*args, **kwargs)


class FollowActivity(Activity):
    ''' record follow requests sent out '''
    followed = models.ForeignKey(
        'User',
        related_name='followed',
        on_delete=models.PROTECT
    )

    def save(self, *args, **kwargs):
        self.activity_type = 'Follow'
        super().save(*args, **kwargs)


class Review(Activity):
    ''' a book review '''
    book = models.ForeignKey('Book', on_delete=models.PROTECT)
    name = models.CharField(max_length=255)
    rating = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(5)])
    review_content = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        self.activity_type = 'Article'
        self.fedireads_type = 'Review'
        super().save(*args, **kwargs)


class Note(Activity):
    ''' reply to a review, etc '''
    def save(self, *args, **kwargs):
        self.activity_type = 'Note'
        super().save(*args, **kwargs)


