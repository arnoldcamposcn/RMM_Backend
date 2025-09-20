# app/magazine/pagination.py
from rest_framework.pagination import PageNumberPagination

class WeeklyEditionPagination(PageNumberPagination):
    page_size = 5                 # 5 por página
    page_size_query_param = "page_size"
    max_page_size = 20
