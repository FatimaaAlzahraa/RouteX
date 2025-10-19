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
    # طبّعي الرقم حسب نظامك (اختياري): إزالة مسافات/شرطات.. الخ
    return ''.join(ch for ch in (phone or '') if ch.isdigit())

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

        # توليد التوكنات
        refresh = RefreshToken.for_user(user)
        access  = refresh.access_token

        # تحديد الدور من الجداول عندك
        if WarehouseManager.objects.filter(user=user).exists():
            role = 'manager'
        elif Driver.objects.filter(user=user).exists():
            role = 'driver'
        else:
            role = 'driver'  # default لو حبيتي

        return Response({
            'access' : str(access),
            'refresh': str(refresh),
            'role'   : role,
            'user'   : {
                'id'      : user.id,
                'username': user.username,  # هنعرضه في الـ Profile
                'phone'   : user.phone,
            }
        }, status=200)



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

