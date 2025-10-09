# app/magazine/pagination.py
from rest_framework.pagination import PageNumberPagination

class BlogPagination(PageNumberPagination):
    page_size = 4                 # 5 por página
    page_size_query_param = "page_size"
    max_page_size = 20
