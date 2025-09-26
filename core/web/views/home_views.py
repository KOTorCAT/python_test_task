from django.shortcuts import render
from django.views.generic import TemplateView

class SimpleHomeView(TemplateView):
    template_name = 'home.html'
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            from django.shortcuts import redirect
            return redirect('simple_profile')
        return render(request, self.template_name)