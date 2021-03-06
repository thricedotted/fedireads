''' application views/pages '''
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Q
from django.http import HttpResponseNotFound
from django.shortcuts import redirect
from django.template.response import TemplateResponse
import re

from fedireads import forms, models, openlibrary, outgoing, incoming
from fedireads.settings import DOMAIN


@login_required
def home(request):
    ''' user's homepage with activity feed '''
    # user's shelves for display
    reading = models.Shelf.objects.get(
        user=request.user,
        shelf_type='reading'
    )
    to_read = models.Shelf.objects.get(
        user=request.user,
        shelf_type='to-read'
    )

    # allows us to check if a user has shelved a book
    user_books = models.Book.objects.filter(shelves__user=request.user).all()

    # books new to the instance, for discovery
    recent_books = models.Book.objects.order_by(
        '-added_date'
    )[:5]

    # status updates for your follow network
    following = models.User.objects.filter(
        Q(followers=request.user) | Q(id=request.user.id)
    )
    # TODO: handle post privacy
    activities = models.Activity.objects.filter(
        user__in=following,

    ).select_subclasses().order_by(
        '-created_date'
    )[:10]

    data = {
        'user': request.user,
        'reading': reading,
        'to_read': to_read,
        'recent_books': recent_books,
        'user_books': user_books,
        'activities': activities,
    }
    return TemplateResponse(request, 'feed.html', data)


def user_login(request):
    ''' authentication '''
    # send user to the login page
    if request.method == 'GET':
        form = forms.LoginForm()
        return TemplateResponse(request, 'login.html', {'login_form': form})

    # authenticate user
    form = forms.LoginForm(request.POST)
    if not form.is_valid():
        return TemplateResponse(request, 'login.html', {'login_form': form})

    username = form.data['username']
    username = '%s@%s' % (username, DOMAIN)
    password = form.data['password']
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        return redirect(request.GET.get('next', '/'))
    return TemplateResponse(request, 'login.html', {'login_form': form})


@login_required
def user_logout(request):
    ''' done with this place! outa here! '''
    logout(request)
    return redirect('/')


def register(request):
    ''' join the server '''
    if request.method == 'GET':
        form = forms.RegisterForm()
        return TemplateResponse(
            request,
            'register.html',
            {'register_form': form}
        )

    form = forms.RegisterForm(request.POST)
    if not form.is_valid():
        return redirect('/register/')

    username = form.data['username']
    email = form.data['email']
    password = form.data['password']

    user = models.User.objects.create_user(username, email, password)
    login(request, user)
    return redirect('/')


def user_profile(request, username):
    ''' profile page for a user '''
    content = request.headers.get('Accept')
    # TODO: this should probably be the full content type? maybe?
    if 'json' in content:
        # we have a json request
        return incoming.get_actor(request, username)

    # otherwise we're at a UI view
    try:
        user = models.User.objects.get(localname=username)
    except models.User.DoesNotExist:
        try:
            user = models.User.objects.get(username=username)
        except models.User.DoesNotExist:
            return HttpResponseNotFound()

    # TODO: change display with privacy and authentication considerations
    shelves = models.Shelf.objects.filter(user=user)
    ratings = {r.book.id: r.rating for r in \
            models.Review.objects.filter(user=user, book__shelves__user=user)}

    data = {
        'user': user,
        'shelves': shelves,
        'ratings': ratings,
        'is_self': request.user.id == user.id,
    }
    return TemplateResponse(request, 'user.html', data)


@login_required
def user_profile_edit(request, username):
    ''' profile page for a user '''
    try:
        user = models.User.objects.get(localname=username)
    except models.User.DoesNotExist:
        return HttpResponseNotFound()

    form = forms.EditUserForm(instance=request.user)
    data = {
        'form': form,
        'user': user,
    }
    return TemplateResponse(request, 'edit_user.html', data)


# TODO: there oughta be clear naming between endpoints and pages
@login_required
def edit_profile(request):
    ''' les get fancy with images '''
    if not request.method == 'POST':
        return redirect('/user/%s' % request.user.localname)

    form = forms.EditUserForm(request.POST, request.FILES)
    if not form.is_valid():
        return redirect('/')

    request.user.name = form.data['name']
    if 'avatar' in form.files:
        request.user.avatar = form.files['avatar']
    request.user.summary = form.data['summary']
    request.user.save()
    return redirect('/user/%s' % request.user.localname)


@login_required
def book_page(request, book_identifier):
    ''' info about a book '''
    book = openlibrary.get_or_create_book(book_identifier)
    # TODO: again, post privacy?
    reviews = models.Review.objects.filter(book=book)
    rating = reviews.aggregate(Avg('rating'))
    review_form = forms.ReviewForm()
    data = {
        'book': book,
        'reviews': reviews,
        'rating': rating['rating__avg'],
        'review_form': review_form,
    }
    return TemplateResponse(request, 'book.html', data)


@login_required
def author_page(request, author_identifier):
    ''' landing page for an author '''
    try:
        author = models.Author.objects.get(openlibrary_key=author_identifier)
    except ValueError:
        return HttpResponseNotFound()

    books = models.Book.objects.filter(authors=author)
    data = {
        'author': author,
        'books': books,
    }
    return TemplateResponse(request, 'author.html', data)


@login_required
def shelve(request, shelf_id, book_id, reshelve=True):
    ''' put a book on a user's shelf '''
    book = models.Book.objects.get(id=book_id)
    desired_shelf = models.Shelf.objects.get(identifier=shelf_id)
    if reshelve:
        try:
            current_shelf = models.Shelf.objects.get(
                user=request.user,
                book=book
            )
            outgoing.handle_unshelve(request.user, book, current_shelf)
        except models.Shelf.DoesNotExist:
            pass
    outgoing.handle_shelve(request.user, book, desired_shelf)
    return redirect('/')


@login_required
def review(request):
    ''' create a book review note '''
    form = forms.ReviewForm(request.POST)
    # TODO: better failure behavior
    if not form.is_valid():
        return redirect('/')
    book_identifier = request.POST.get('book')
    book = openlibrary.get_or_create_book(book_identifier)

    # TODO: validation, htmlification
    name = form.data.get('name')
    content = form.data.get('review_content')
    rating = form.data.get('rating')

    outgoing.handle_review(request.user, book, name, content, rating)
    return redirect('/book/%s' % book_identifier)


@login_required
def follow(request):
    ''' follow another user, here or abroad '''
    to_follow = request.POST.get('user')
    # should this be an actor rather than an id? idk
    to_follow = models.User.objects.get(id=to_follow)

    outgoing.handle_outgoing_follow(request.user, to_follow)
    return redirect('/user/%s' % to_follow.username)


@login_required
def unfollow(request):
    ''' unfollow a user '''
    # TODO: this is not an implementation!!
    followed = request.POST.get('user')
    followed = models.User.objects.get(id=followed)
    followed.followers.remove(request.user)
    return redirect('/user/%s' % followed.username)


@login_required
def search(request):
    ''' that search bar up top '''
    query = request.GET.get('q')
    if re.match(r'\w+@\w+.\w+', query):
        # if something looks like a username, search with webfinger
        results = [outgoing.handle_account_search(query)]
        template = 'user_results.html'
    else:
        # just send the question over to openlibrary for book search
        results = openlibrary.book_search(query)
        template = 'book_results.html'

    return TemplateResponse(request, template, {'results': results})

