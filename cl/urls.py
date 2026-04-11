from django.urls import path, include
from django.contrib import admin
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from accounts.views import UserViewSet

# ============= Router Configuration =============
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')

# ============= Swagger/OpenAPI Schema Configuration =============
schema_view = get_schema_view(
    openapi.Info(
        title="Email Verification API",
        default_version='v1',
        description="""
        # Email Verification System API Documentation
        
        ## Features:
        - User Registration with Email Verification
        - JWT Authentication
        - Resend Verification Code
        - Change Password
        - User Profile Management
        
        ## How to use:
        1. Register a new user using `/api/users/` endpoint
        2. Check email for verification code
        3. Verify email using `/api/users/verify-email/`
        4. Login using `/api/token/` to get JWT token
        5. Use token in Authorization header: `Bearer <your_token>`
        """,
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(
            name="Support Team",
            email="support@example.com",
            url="https://example.com/support"
        ),
        license=openapi.License(
            name="MIT License",
            url="https://opensource.org/licenses/MIT"
        ),
    ),
    public=True,
    permission_classes=[],
)

# ============= URL Patterns =============
urlpatterns = [
    # API endpoints (router views)
    path('', include(router.urls)),
    path('admin/', admin.site.urls),

    
    # ============= Authentication URLs =============
    # JWT Token endpoints
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # ============= API Documentation URLs =============
    # Swagger UI (interactive documentation)
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    
    # ReDoc (alternative documentation)
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # Raw JSON schema
    path('docs.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
]
