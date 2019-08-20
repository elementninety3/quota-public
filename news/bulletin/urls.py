from django.urls import path
from django.conf.urls import url

from . import views

urlpatterns = [
    path('', views.index, name='landing'),
    path('latest', views.newindex, name='index'),
    path('alerts', views.topicview, name='topicview'),
    path('preferences/widgets', views.widgetprefs, name='widgetprefs'),
    path('preferences', views.preferences, name='preferences'),
    path('preferences/alerts', views.topicprefs, name='topicprefs'),
    path('preferences/alerts/<int:topic_id>', views.topicedit, name='topicedit'),
    path('preferences/alerts/delete/<int:topic_id>', views.topicdelete, name='topicdelete'),
    path('preferences/email', views.emailprefs, name='emailprefs'),
    path('preferences/sources', views.sourceprefs, name='sourceprefs'),
    path('catorder', views.catorder, name='catorder'),
    path('setaddress', views.setaddress, name='setaddress'),
    path('donate', views.donate, name='donate'),
    path('thankyou', views.thankyou, name='thankyou'),
    path('faq', views.about, name='about'),
    path('contact', views.feedback, name='feedback'),
    path('emailtest', views.emailtest, name='emailtest'),
    path('setup/1', views.setup1, name='setup1'),
    path('setup/2', views.setup2, name='setup2'),
    path('setup/3', views.setup3, name='setup3'),
    path('setup/finish', views.setup_complete, name='setupcomplete'),
]