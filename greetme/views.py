#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.http import HttpResponse, HttpResponseRedirect

from django.utils.translation import ugettext as _
from django.shortcuts import redirect, render_to_response


# Against CSRF
from django.core.context_processors import csrf
from django.views.decorators.csrf import csrf_exempt


import urllib, urllib2
import datetime
from djangofb.facebook import Facebook, GraphAPI, GraphAPIError

from greetme.models import Greeting, DefaultLanguage, Language, ExcludedFriend
from greetme.forms import GreetForm, DefaultLanguageForm
from djangofb.models import FacebookUser

from django.template import loader
from django.http import HttpResponse

from django.template import RequestContext

from django.conf import settings






FACEBOOK_APP=settings.FACEBOOK_APPS['greetme']
REDIRECT_URI=settings.REDIRECT_URI


@csrf_exempt
def authentication(view):
    """
    It manages the follow url:
    https://graph.facebook.com/oauth/authorize?
    client_id=111466298916050&
    scope=publish_stream,offline_access,friends_birthday&
    redirect_uri=http://localhost
    """
    def out_view(*args, **kwargs):
        request = args[0]
        
        #facebook = request.session.get('facebook', None)
        #if not facebook:
        facebook = Facebook(FACEBOOK_APP['ID'], FACEBOOK_APP['SECRET'])
        # initial facebook request comes in as a POST with a signed_request
        if u'signed_request' in request.POST:
            facebook.load_signed_request(request.POST.get('signed_request', None))
            # we reset the method to GET because a request from facebook with a
            # signed_request uses POST for security reasons, despite it
            # actually being a GET. in webapp causes loss of request.POST data.
            request.method = u'GET'
            request.session['facebook'] = facebook.user_cookie
            #self.set_cookie('u', facebook.user_cookie, datetime.timedelta(minutes=1440))
        elif 'facebook' in request.session:
            facebook.load_signed_request(request.session.get('facebook', None))
        
        
        # try to load or create a user object
        user = None
        
        asr = facebook.signed_request
        #assert False
        
        if facebook.user_id:
            user = get_user_from_token(facebook.user_id, facebook.access_token)
            
        if user is not None:
            return view(user, *args, **kwargs)
        else:
            return render(user, request, "welcome.html")
        
                       
    return out_view


def render(user, request, template_name, dictionary={}):
    """
    Returns a HttpResponse whose content is filled with the result of calling
    django.template.loader.render_to_string() with the passed arguments.
    """

    d = {'FACEBOOK_APP':FACEBOOK_APP['ID']}

    if user:
        d['user_id'] = user.uid
    else:
        d['user_id'] = None
        
    d['canvas_url'] = FACEBOOK_APP['URL']
    
    d.update(csrf(request))
    d.update(dictionary)
    
    response = render_to_response(template_name, d, context_instance=RequestContext(request))
    
    response[u'P3P'] = u'CP=HONK'  # iframe cookies in IE
    #response['P3P:CP'] = 'IDC DSP COR ADM DEVi TAIi PSA PSD IVAi IVDi CONi HIS OUR IND CNT'
    
    return response



def get_user_from_token(uid, access_token):
    """
    Get the user and if it doesn't exist create it into db.
    Store a local instance of the user data so we don't need
    a round-trip to Facebook on every request
    """
    try:
        user = FacebookUser.objects.get(uid=uid, aid=FACEBOOK_APP['ID'])
    except FacebookUser.DoesNotExist:
        try:
            graph = GraphAPI(access_token)
            profile = graph.get_object("me")
            user = FacebookUser(uid=str(profile["id"]),
                                aid=FACEBOOK_APP['ID'],
                                profile_url=profile["link"],
                                access_token=access_token,
                                username=str(profile["username"]))
            user.save()
            # We have to create some default greeting senteces for him
            # and an default language too
            def_greets = Greeting.objects.filter(default=True)
            for def_g in def_greets:
                def_g.users.add(user)
            
    
            try:
                l = Language.objects.get(id='en')
            except Language.DoesNotExist:
                l = Language(id='en', name='English')
                l.save()
            opt = DefaultLanguage(user=user, lang=l)
            opt.save()
        except GraphAPIError:
            return None
        
    else:
        # Update the access token!
        if access_token and user.access_token != access_token:
            user.access_token = access_token
            user.save()

    return user



@authentication
def index(user, request):
    greets = Greeting.objects.filter(users=user).order_by('lang')
    languages = Language.objects.all()
    first_name = ''
    try:
        graph = GraphAPI(user.access_token)
        first_name = graph.get_object('me')['first_name']
    except Exception:
        first_name = ''

    c = {'uid':user.uid, 'greets':greets, 'languages':languages, 'first_name':first_name}

    return render(user, request, "index.html", c)


def deauth(request):
    f = open('/home/feel/prova_fb','w')
    f.write("qst e' una prova!")
    f.close()
    
    facebook = request.session.get('facebook', None)
    if not facebook:
        facebook = Facebook(FACEBOOK_APP['ID'], FACEBOOK_APP['SECRET'])

    # initial facebook request comes in as a POST with a signed_request
    if u'signed_request' in request.POST:
        facebook.load_signed_request(request.POST.get('signed_request', None))
        
    # try to load or create a user object
    if facebook.user_id:
        try:
            user = FacebookUser.objects.get(uid=facebook.user_id, aid=FACEBOOK_APP['ID'])
            user.delete()
            if request.session.get('facebook', False):
                del request.session["facebook"]
        except FacebookUser.DoesNotExist:
            pass
    
    #return redirect('/greetme/')


@authentication
def set_default_lang(user, request):
    try:
        graph = GraphAPI(user.access_token)
        # Get friend list
        friends = graph.get_connections("me","friends")['data']
    except Exception:
        return redirect('/greetme/')

    
    if request.method =='POST':
        form = DefaultLanguageForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            o = DefaultLanguage(lang=cd['lang'], user=user)
            o.save()
            included_friends = request.POST.getlist('select')
            excluded_friends = [f for f in friends if included_friends.count(f['id'])==0]
            # Delete the previous settings before
            e = ExcludedFriend.objects.filter(user=user)
            e.delete()
            for sel in excluded_friends:
                e = ExcludedFriend(user=user, friend_id=sel['id'])
                e.save()
            return redirect('/greetme/')
    else:
        try:
            o = DefaultLanguage.objects.get(user=user)
        except DefaultLanguage.DoesNotExist:
            o = DefaultLanguage(user=user)
        form = DefaultLanguageForm( instance=o)
    
        
    ex_friends_id = [ ex.friend_id for ex in ExcludedFriend.objects.filter(user=user)]
    excluded_friends = []
    included_friends = []
    for f in friends:
        if ex_friends_id.count(f['id'])>0:
            excluded_friends.append(f)
        else:
            included_friends.append(f)
    
    return render(user, request, 'options.html', {'form': form,\
                                               'excluded_friends':excluded_friends,\
                                               'included_friends': included_friends})


@authentication
def remove_greets(user, request):
    if request.method=='POST':
        selections = request.POST.getlist('select')
        for sel in selections:
            # TODO Check out the id of the greetings deleted. It's possible that doesn't exists.
            g = Greeting.objects.get(users=user, id=int(sel))
            if g.default:
                g.users.remove(user)
            else:
                g.delete()
        pass
    return redirect('/greetme/')


@authentication
def add_greets(user, request):
    if request.method == 'POST':
        form = GreetForm(user, request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            g = Greeting(lang=cd['lang'],greeting=cd['greeting'], gender=cd['gender'], default=False)
            g.save()
            g.users.add(user)
            return redirect('/greetme/')
    else:
        form = GreetForm(user, initial={'user':user, 'greeting': _('Put here the greeting')})
    return render(user, request, 'add_greets.html', {'user':user, 'form': form})
