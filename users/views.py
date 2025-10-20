# users/views.py
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from shipments.models import WarehouseManager, Driver



User = get_user_model()

def normalize_phone(phone: str) -> str:
    return ''.join(ch for ch in (phone or '') if ch.isdigit())

# login view 
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        phone    = request.data.get('phone')
        password = request.data.get('password')

        if not phone or not password:
            return Response({'detail': 'phone and password are required'}, status=400)

        phone_norm = normalize_phone(phone)

        try:
            user = User.objects.get(phone=phone_norm)
        except User.DoesNotExist:
            return Response({'detail': 'invalid credentials'}, status=401)

        if not user.check_password(password) or not user.is_active:
            return Response({'detail': 'invalid credentials'}, status=401)


        refresh = RefreshToken.for_user(user)
        access  = refresh.access_token

        # role detection
        if WarehouseManager.objects.filter(user=user).exists():
            role = 'manager'
        elif Driver.objects.filter(user=user).exists():
            role = 'driver'
        else:
            role = 'driver'  

        return Response({
            'access' : str(access),
            'refresh': str(refresh),
            'role'   : role,
            'user'   : {
                'id'      : user.id,
                'username': user.username, 
                'phone'   : user.phone,
            }
        }, status=200)



# whois view returning user info and role
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def whois(request):
    user = request.user
    if WarehouseManager.objects.filter(user=user).exists():
        role = 'manager'
    elif Driver.objects.filter(user=user).exists():
        role = 'driver'
    else:
        role = 'driver'
    return Response({
        'id': user.id,
        'username': user.username,
        'phone': user.phone,
        'role': role,
    })

