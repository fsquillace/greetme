#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError

from djangofb.models import FacebookUser
from greetme.models import Greeting, DefaultLanguage, Language, ExcludedFriend
from djangofb import facebook
import random, datetime

from django.conf import settings

import threading
import time


FACEBOOK_APP=settings.FACEBOOK_APPS['greetme']
REDIRECT_URI=settings.REDIRECT_URI

from Queue import Queue
from threading import Thread

class Worker(Thread):
    """Thread executing tasks from a given tasks queue"""
    def __init__(self, tasks):
        Thread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.start()
    
    def run(self):
        while True:
            func, args, kargs = self.tasks.get()
            try: func(*args, **kargs)
            except Exception, e: print e
            self.tasks.task_done()

class ThreadPool:
    """Pool of threads consuming tasks from a queue"""
    def __init__(self, num_threads):
        self.tasks = Queue(num_threads)
        for _ in range(num_threads): Worker(self.tasks)

    def add_task(self, func, *args, **kargs):
        """Add a task to the queue"""
        self.tasks.put((func, args, kargs))

    def wait_completion(self):
        """Wait for completion of all the tasks in the queue"""
        self.tasks.join()

class Command(BaseCommand):

    help = 'It allows to find out birthday\'s friends and make advertisement'

    def handle(self, *args, **options):
        l_user = FacebookUser.objects.filter(aid=FACEBOOK_APP['ID'])
        # In order to avoid the segmantation fault, the num of thread must be less or igual 
        # of the num of tasks
        if len(l_user)<=20:
            thread_num = len(l_user)
        else:
            thread_num = 20
        pool = ThreadPool(thread_num)
        for user_fb in l_user:
            pool.add_task(self.cron, user_fb)
            
        pool.wait_completion()
        
        
        
    def cron(self,  user_fb):
        acc_t = user_fb.access_token
        attempt = 0
        # Try three times to access with the FB API
        while(attempt<3):
            try:
                graph = facebook.GraphAPI(acc_t)
                # Get friend list
                friends = graph.get_connections("me","friends",fields='id,first_name,last_name,gender,birthday,locale')['data']
                break
            except Exception, inst:
                self.stderr.write(str(inst)+'\n')
                attempt += 1
                #self.stderr.write('N° of attempts: '+str(attempt)+'\n')
                time.sleep(3)
        
        if attempt==3:
            self.stderr.write('Error: we can\'t access to the facebook API with the user '+user_fb.uid+'. He\'ll be deleted.\n')
            #user_fb.delete()
            return
        
        
        self.find_birthday(user_fb, graph, friends)
        self.do_advertisement(user_fb, graph, friends)
        pass

    
    
    def find_birthday(self, user_fb, graph, friends):

        self.stdout.write('Looks for birthdays in '+str(user_fb.uid)+'\'s friends...\n')
        
        day_today = int(datetime.date.strftime(datetime.date.today() ,"%d"))
        month_today = int(datetime.date.strftime(datetime.date.today() ,"%m"))
        
        ex_friends_id = [ef.friend_id for ef in ExcludedFriend.objects.filter(user=user_fb)]

        for friend in friends:
            try:
                id_friend = str(friend['id'])
                if id_friend in ex_friends_id:
                    self.stdout.write('Warn! User: '+str(user_fb.uid)+' -->Friend: '+str(friend['id'])+\
                                      ': The friend was excluded by the user.\n')
                    continue
            except KeyError:
                # We can do nothing!
                self.stderr.write('Error! User: '+str(user_fb.uid)+' -->Friend: '+str(id_friend)+\
                                  ': No ID field.\n')
                continue
            
        
            try:
                birth_friend = str(friend['birthday'])
            except KeyError:
                # We can do nothing!
                #self.stderr.write('Error! User: '+str(user_fb.uid)+' -->Friend: '+str(id_friend)+\
                                  #': No birthday field.\n')
                continue
            
            try:
                fname_friend = friend['first_name']
                lname_friend = friend['last_name']

            except Exception, e:
                self.stderr.write(str(e)+'\n')
                fname_friend = ''
                lname_friend = ''
                #self.stderr.write('Error! User: '+str(user_fb.uid)+' -->Friend: '+str(id_friend)+\
                                  #': No name or surname fields.\n')
            
            try:
                locale_friend = str(friend['locale'].split('_')[0])

            except Exception, e:
                self.stderr.write(str(e)+'\n')
                locale_friend = 'en'
                #self.stderr.write('Error! User: '+str(user_fb.uid)+' -->Friend: '+str(id_friend)+\
                                      #': No locale field.\n')
                
            try:
                gender_friend = friend['gender']

            except Exception, e:
                gender_friend = ''
                #self.stderr.write('Error! User: '+str(user_fb.uid)+' -->Friend: '+str(id_friend)+\
                                  #': No gender field.\n')
            
            #Checking out...
            day_birth_friend = int(birth_friend.split('/')[1])
            month_birth_friend = int(birth_friend.split('/')[0])
            
            if day_birth_friend == day_today and month_birth_friend == month_today:
                self.do_greeting(user_fb, graph, id_friend, fname_friend, lname_friend, locale_friend, gender_friend)

        pass

    
    def do_greeting(self, user_fb, graph, id_friend, fname_friend, lname_friend, lang_friend, gender_friend):
        # TODO manage the default greeting with no user assigned
        l_greet = Greeting.objects.filter(users=user_fb, lang=lang_friend)
        if gender_friend=='male':
            l_greet = l_greet.exclude(gender='F')
        elif gender_friend=='female':
            l_greet = l_greet.exclude(gender='M')
        else:
            l_greet = l_greet.filter(gender=None)
            
            
        if len(l_greet)==0:
            # Let's try the default lang
            try:
                opt = DefaultLanguage.objects.get(user=user_fb)
                l_greet = Greeting.objects.filter(users=user_fb, lang=opt.lang, gender=None)
            except DefaultLanguage.DoesNotExist:
                l_greet = []
            
            if len(l_greet)==0:
                # So.... Let's try en
                l_greet = Greeting.objects.filter(users=user_fb, lang='en', gender=None)
                if len(l_greet)==0:
                    # Nothing to do
                    #self.stderr.write('Error! User: '+str(user_fb.uid)+' -->Friend: '+str(id_friend)+\
                                      #' has got birthday but we haven\'t a greeting for his language.\n')
                    return
                
        greeting = random.choice(l_greet)
        greet = greeting.greeting.replace('@first_name',fname_friend)
        greet = greet.replace('@last_name',lname_friend)
        
        try:
            graph.put_object(id_friend,"feed",message=greet.encode('utf8')) 
            self.stdout.write('User: '+str(user_fb.uid)+' -->Friend: '+str(id_friend)+' -->Msg: '+greet.encode('utf8')+'\n')
        except Exception, inst:
            self.stderr.write(str(inst)+'\n')
            self.stderr.write('Error! User: '+str(user_fb.uid)+' -->Friend: '+str(id_friend)+\
                                      ' has got birthday but we can\'t send a message on his wall.\n')
    
    def do_advertisement(self, user_fb, graph, friends):
        # Application data
        app = graph.get_object(FACEBOOK_APP['ID'])
        attach = {"name": 'GreetMe',
                  "link": FACEBOOK_APP['URL'],
                  "caption": 'Facebook Birthday Application',
                  "description": app['description'],
                  "picture": 'http://facebookapps.alwaysdata.net/static/images/autobirth.jpg',
                  "icon": 'http://facebookapps.alwaysdata.net/static/images/autobirth.jpg'}
                  #"picture": REDIRECT_URI+'/static/images/autobirth.jpg',
                  #"icon": REDIRECT_URI+'/static/images/autobirth.jpg'}


        # Feed advertisement
        threshold = 10
        rand = random.uniform(0,100)
        if rand < threshold:
            self.stdout.write('Feed advertisement for '+str(user_fb.uid)+'\'s friends...\n')
            
            num_friends = random.randint(1,5)
            sample_friends = random.sample(friends, num_friends)
            for friend in sample_friends:
                
                try:
                    id_friend = friend['id']
                except Exception, e:
                    self.stderr.write(str(e))
                    #self.stderr.write('Error: for the friend '+friend['id']+\
                                     # ' we can\'t post on feed an advertisement.\n')
                    continue

                try:
                    fname_friend = friend['first_name']
                except Exception, e:
                    self.stderr.write(str(e)+'\n')
                    fname_friend = ''
                    self.stderr.write('Error! User: '+str(user_fb.uid)+' -->Friend: '+str(id_friend)+\
                                      ': No name field.\n')
                
                try:
                    locale_friend = str(friend['locale'].split('_')[0])
                except Exception, e:
                    self.stderr.write(str(e)+'\n')
                    locale_friend = 'en'
                    self.stderr.write('Error! User: '+str(user_fb.uid)+' -->Friend: '+str(id_friend)+\
                                      ': No locale field.\n')

                
                if locale_friend=='es':
                    message = u'Mira '+unicode(fname_friend)+u'. Esta aplicación envía en manera automática mensajes de felicitación a tus amigos el día de sus cumpleaños.\n'+\
                            u'Es muy útil. Pruebala!'
                elif locale_friend=='it':
                    message = 'Guarda qua '+fname_friend+'. Questa applicazione invia messaggi di auguri sul muro dei tuoi amici il giorno del loro compleanno.\n'+\
                    'E\' molto utile te la consiglio!'
                else:
                    message = 'Looks '+fname_friend+'. This application makes automatically greetings to your friends for their birthday.\n'+\
                    'It\'s very useful friend. Try it!'                
                    
#                print id_friend, fname_friend, locale_friend, message
                try:
                    graph.put_wall_post(message.encode('utf8'), attach, profile_id=id_friend)
                    self.stdout.write('User: '+str(user_fb.uid)+' -->Friend: '+str(id_friend)+\
                                      ' has got a feed advertisement.\n')
                    pass
                except Exception, e:
                    self.stderr.write(str(e))
                    self.stderr.write('Error! User: '+str(user_fb.uid)+' -->Friend: '+str(id_friend)+\
                                     ' we can\'t post on feed an advertisement.\n')
                