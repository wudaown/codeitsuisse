from django.conf.urls import include, url

from django.contrib import admin
admin.autodiscover()

import hello.views

# Examples:
# url(r'^$', 'gettingstarted.views.home', name='home'),
# url(r'^blog/', include('blog.urls')),

urlpatterns = [
    url(r'^$', hello.views.index, name='index'),
    url(r'^db', hello.views.db, name='db'),
    url(r'^sort', hello.views.sort, name='sort'),
    url(r'^mini-exchange', hello.views.miniexchange, name='mini-exchange'),
    url(r'^interact', hello.views.interact, name='interact'),
    url(r'^horse-racing', hello.views.horseRacing, name='horse-racing'),
    url(r'^heist', hello.views.heist, name='heist'),
    url(r'^releaseSchedule', hello.views.releaseSchedule, name='releaseSchedule'),
    url(r'^trainPlanner', hello.views.trainPlanner, name='trainPlanner'),
    url(r'^calculateemptyarea', hello.views.calculateemptyarea, name='calculateemptyarea'),
    url(r'^stringcompression/(?P<mode>\w+)', hello.views.stringcompression, name='stringcompression'),
    url(r'^admin/', include(admin.site.urls)),
]
