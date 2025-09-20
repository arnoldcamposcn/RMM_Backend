# app/foro/pagination.py
from rest_framework.pagination import PageNumberPagination

class TemasPagination(PageNumberPagination):
    page_size = 8                 # 8 temas por página
    page_size_query_param = "page_size"
    max_page_size = 20