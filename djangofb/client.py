#!/usr/bin/env python
#
# Copyright 2010 Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""A Facebook stream client written against the Facebook Graph API."""

import facebook

from django.conf import settings
from django.http import HttpResponseBadRequest, HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response, redirect

from models import FacebookUser


class ClientAPI(object):
    def __init__(self, FACEBOOK_APP_ID, FACEBOOK_APP_SECRET):
        """
        The xxxHandler classes in the AppEngine example are something like
        class-based views in Django. But it's difficult to do class-based views
        in a thread-safe way, so it's cleaner and simpler just to instantiate
        this helper class from within regular views.
        """
        self.__FACEBOOK_APP_ID = FACEBOOK_APP_ID
        self.__FACEBOOK_APP_SECRET = FACEBOOK_APP_SECRET
        self.__current_user = None
        self.__is_a_new_user = False
        pass
    

    def get_current_user(self, request):
        """Provides access to the active Facebook user in self.current_user
        The property is lazy-loaded on first access, using the cookie saved
        by the Facebook JavaScript SDK to determine the user ID of the active
        user. See http://developers.facebook.com/docs/authentication/ for
        more information.
        """
        """The active user, or None if the user has not logged in."""
        
        cookie = facebook.get_user_from_cookie(
            request.COOKIES, self.__FACEBOOK_APP_ID, self.__FACEBOOK_APP_SECRET)
        if cookie:
            # Store a local instance of the user data so we don't need
            # a round-trip to Facebook on every request
            self.__is_a_new_user = False
            try:
                user = FacebookUser.objects.get(uid=cookie["uid"], aid=self.__FACEBOOK_APP_ID)
            except FacebookUser.DoesNotExist:
                graph = facebook.GraphAPI(cookie["access_token"])
                profile = graph.get_object("me")
                user = FacebookUser(uid=str(profile["id"]), 
                                    aid=self.__FACEBOOK_APP_ID,
                                    profile_url=profile["link"],
                                    access_token=cookie["access_token"])
                user.save()
                self.__is_a_new_user = True
            else:
                # Update the access token!
                graph = facebook.GraphAPI(cookie["access_token"])
                if user.access_token != cookie["access_token"]:
                    user.access_token = cookie["access_token"]
                    user.save()
            self.__current_user = user
            
        return self.__current_user
    
    def is_a_new_user(self):
        return self.__is_a_new_user
    
    
    def is_user_logged_in(self):
        return self.__current_user is not None
    

    def redirect_to_log(self, action_login):
        """
        This function redirect to a Javascript page. It allows to login or logout 
        the user.
        """
        
        if action_login:
            action = "auth.login"
        else:
            action = "auth.logout"
        
        html = """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
  </head>
  <body>
    <div id="fb-root"></div>
    <script>
     window.fbAsyncInit = function() {
        FB.init({appId: '"""+self.__FACEBOOK_APP_ID+"""', status: true, cookie: true, xfbml: true});
        FB.Event.subscribe('"""+action+"""', function(response) {
          window.location.reload();
        });
     };
     (function() {
       var e = document.createElement('script');
       e.type = 'text/javascript';
       e.src = document.location.protocol + '//connect.facebook.net/en_US/all.js';
       e.async = true;
       document.getElementById('fb-root').appendChild(e);
     }());
    </script>
  </body>
</html>
        """
        return HttpResponse(html)
        
        