from django.urls import path
from . import views

app_name = 'hydrology'

urlpatterns = [
    path('', views.ProjectListView.as_view(), name='project_list'),
    path('project/<int:pk>/', views.ProjectDetailView.as_view(), name='project_detail'),
    path('project/create/', views.ProjectCreateView.as_view(), name='project_create'),
    path('project/<int:pk>/edit/', views.ProjectUpdateView.as_view(), name='project_edit'),
    path('project/<int:pk>/compute/', views.project_compute, name='project_compute'),
    path('project/<int:pk>/results/', views.project_results, name='project_results'),
    path('project/<int:pk>/export/<str:format_type>/', views.export_results, name='export_results'),
]