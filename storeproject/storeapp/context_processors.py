from .models import Cart

def cart_count(request):
    """
    Context processor to calculate and provide the total number of items
    in the current authenticated user's shopping cart globally to all templates.
    """
    count = 0
    if request.user.is_authenticated:
        count = Cart.objects.filter(user=request.user).count()
    return {'cart_count': count}