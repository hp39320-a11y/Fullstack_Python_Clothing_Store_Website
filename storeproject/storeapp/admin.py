from django.contrib import admin
from .models import *
# Register your models here.


@admin.register(Cateogry)
class CateogryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    readonly_fields = ('created_at',)
    search_fields = ('name',)
    ordering = ('name',)

@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'created_at')
    readonly_fields = ('created_at',)
    list_filter = ('category',)
    search_fields = ('name', 'category__name')
    ordering = ('category', 'name')
    

@admin.register(Products)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'subcategory', 'price', 'stock', 'created_at')
    list_editable = ('price', 'stock')
    readonly_fields = ('created_at',)
    fields = ('name', 'category', 'subcategory', 'price', 'stock', 'image', 'description', 'sizes')
    search_fields = ('name', 'category__name', 'subcategory__name')
    list_filter = ('category', 'subcategory', 'created_at')
    list_per_page = 20



@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id','user','total_amount','payment_method','status','created_at')
    readonly_fields = ('created_at',)

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status == "Cancelled":
            return ('status','created_at')
        return self.readonly_fields
    list_filter = ('status','created_at') 

@admin.register(OrderItem)
class OrderTtemAdmin(admin.ModelAdmin):
    list_display=('id','product','quantity','price','created_at',)
    readonly_fields=('created_at',)

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display=('name','email','message',)
    readonly_fields=('created_at',)

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount', 'active', 'valid_from', 'valid_to']

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'full_name', 'phone', 'address_line', 'city', 'state','pincode']
    readonly_fields = ('created_at',)
    


