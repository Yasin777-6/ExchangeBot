from django.http import JsonResponse, HttpResponse

def home(request):
    """Home page / health check"""
    return JsonResponse({
        'status': 'ok',
        'message': 'Minecraft Marketplace Bot API',
        'endpoints': {
            'admin': '/admin/',
            'webhook': '/bot/webhook/',
            'set_webhook': '/bot/set-webhook/',
            'webhook_info': '/bot/webhook-info/',
            'delete_webhook': '/bot/delete-webhook/'
        }
    })

def health(request):
    """Health check for Railway"""
    return HttpResponse('OK', status=200)
