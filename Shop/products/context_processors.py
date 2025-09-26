from .models import Category

def top_categories(request):
    return {
        "top_categories": Category.objects.filter(parent__isnull=True, is_active=True).prefetch_related("children")
    }
