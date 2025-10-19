from django.shortcuts import render

# Create your views here.
from rest_framework import generics, permissions, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from .models import Product, Category
from .serializers import ProductSerializer, ProductCreateSerializer, CategorySerializer
from .filters import ProductFilter
from .permissions import IsOwnerOrReadOnly, IsAdminOrReadOnly

class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']

class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]

class ProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'category__name', 'description']
    ordering_fields = ['name', 'price', 'created_date', 'stock_quantity']
    
    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).select_related('category', 'created_by')
        
        # Filter by category name if provided
        category_name = self.request.query_params.get('category_name')
        if category_name:
            queryset = queryset.filter(category__name__icontains=category_name)
        
        # Filter by stock availability
        stock_available = self.request.query_params.get('stock_available')
        if stock_available and stock_available.lower() == 'true':
            queryset = queryset.filter(stock_quantity__gt=0)
        
        return queryset

class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]

class ProductCreateView(generics.CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class ProductUpdateView(generics.RetrieveUpdateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductCreateSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_serializer_class(self):
        if self.request.method == 'PUT' or self.request.method == 'PATCH':
            return ProductCreateSerializer
        return ProductSerializer

class ProductDeleteView(generics.DestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def product_search(request):
    """
    Custom search endpoint for products
    """
    query = request.query_params.get('q', '')
    category = request.query_params.get('category', '')
    
    products = Product.objects.filter(is_active=True)
    
    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )
    
    if category:
        products = products.filter(category__name__icontains=category)
    
    # Apply additional filters
    min_price = request.query_params.get('min_price')
    max_price = request.query_params.get('max_price')
    in_stock = request.query_params.get('in_stock')
    
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
    if in_stock and in_stock.lower() == 'true':
        products = products.filter(stock_quantity__gt=0)
    
    # Pagination
    page = request.query_params.get('page', 1)
    page_size = request.query_params.get('page_size', 20)
    
    try:
        page = int(page)
        page_size = int(page_size)
    except ValueError:
        page = 1
        page_size = 20
    
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    
    total_count = products.count()
    products_page = products[start_index:end_index]
    
    serializer = ProductSerializer(products_page, many=True)
    
    return Response({
        'count': total_count,
        'next': f"{request.build_absolute_uri()}?page={page + 1}&page_size={page_size}" if end_index < total_count else None,
        'previous': f"{request.build_absolute_uri()}?page={page - 1}&page_size={page_size}" if start_index > 0 else None,
        'results': serializer.data
    })

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def reduce_stock(request, pk):
    """
    Endpoint to reduce stock quantity (for order placement)
    """
    try:
        product = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
    
    quantity = request.data.get('quantity')
    if not quantity or not isinstance(quantity, int) or quantity <= 0:
        return Response({'error': 'Valid quantity is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    if product.reduce_stock(quantity):
        return Response({
            'message': f'Stock reduced by {quantity}',
            'remaining_stock': product.stock_quantity
        })
    else:
        return Response({
            'error': 'Insufficient stock',
            'available_stock': product.stock_quantity
        }, status=status.HTTP_400_BAD_REQUEST)