from django.shortcuts import render_to_response, get_object_or_404
# Create your views here.


def user_stats(request):
    return render_to_response('user_stats.html', {'options': 'O', 'values': 'v'}, )
