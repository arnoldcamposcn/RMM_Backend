# app/articles/pagination.py
from rest_framework.pagination import PageNumberPagination

class ArticulosPagination(PageNumberPagination):
    page_size = 6                 # 6 artículos por página
    page_size_query_param = "page_size"
    max_page_size = 20
