from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),

    path('tickets/', views.tickets_view, name='tickets'),
    path('tickets/create/', views.create_ticket, name='create_ticket'),
    path('tickets/<int:pk>/update/', views.update_ticket, name='update_ticket'),
    path('tickets/<int:pk>/delete/', views.delete_ticket, name='delete_ticket'),

    path('chat/', views.chat_view, name='chat'),
    path('chat/api/', views.chat_api, name='chat_api'),

    path('kb/', views.kb_view, name='knowledge_base'),
    path('kb/create/', views.kb_create, name='kb_create'),
    path('kb/<int:pk>/delete/', views.kb_delete, name='kb_delete'),

    path('analytics/', views.analytics_view, name='analytics'),
    path('profile/', views.profile_view, name='profile'),
]