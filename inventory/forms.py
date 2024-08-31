# forms.py
from django import forms
from django.db import transaction
from .models import Checkout, Inventory, CheckedOutBy


class CheckoutForm(forms.ModelForm):
    checked_out_by = forms.ModelChoiceField(queryset=CheckedOutBy.objects.all(), empty_label=None)
    inventory_item = forms.ModelChoiceField(queryset=Inventory.objects.all(), empty_label=None)

    class Meta:
        model = Checkout
        fields = ['inventory_item', 'checked_out_by', 'quantity']

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        inventory_item = self.cleaned_data.get('inventory_item')

        # Access the related Inventory item
        inventory = Inventory.objects.filter(id=inventory_item.id).first()

        if not inventory:
            raise forms.ValidationError('Invalid inventory item.')

        if quantity > inventory.quantity:
            raise forms.ValidationError('Not enough inventory available at the specified location and level.')

        return quantity

    def save(self, commit=True):
        # Get cleaned data
        cleaned_data = self.cleaned_data
        inventory_item = cleaned_data.get('inventory_item')
        quantity = cleaned_data.get('quantity')
        checked_out_by = cleaned_data.get('checked_out_by')

        # Update the inventory and save the checkout
        with transaction.atomic():
            # Lock the inventory item
            inventory = Inventory.objects.select_for_update().get(id=inventory_item.id)

            if quantity > inventory.quantity:
                raise forms.ValidationError('Not enough inventory available at the specified location and level.')

            # Update inventory quantity
            inventory.quantity -= quantity
            inventory.save()

            # Save the checkout
            checkout = super().save(commit=False)
            checkout.checked_out_by = checked_out_by
            if commit:
                checkout.save()

        return checkout
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply the select2 class to the product field
        self.fields['inventory_item'].widget.attrs.update({'class': 'select2'})
        self.fields['checked_out_by'].widget.attrs.update({'class': 'select2'})


class ProductForm(forms.ModelForm):
    CABINET_CHOICES = [
        ('XCAB1', 'XCAB 1 – Sprays'),
        ('XCAB2', 'XCAB 2 – Sprays'),
        ('XCAB3', 'XCAB 3 – Sprays'),
        ('XCAB4', 'XCAB 4 – Sprays'),
        ('XCAB5', 'XCAB 5 – Tools/bits'),
        ('XCAB6', 'XCAB 6 – Bondo/Cleaning sprays'),
        ('XCAB7', 'XCAB 7 – Sandpaper'),
        ('XCAB8', 'XCAB 8 – Gloves/Masking tape'),
        ('XCAB9', 'XCAB 9 – Fillsticks/markers/small touch up'),
        ('QIS', 'QIS – Total Packaging/Atlantic Purchases'),
        ('Fastenal', 'Fastenal Purchases'),
    ]

    LEVEL_CHOICES = [
        ('LEVEL1', 'Level 1'),
        ('LEVEL2', 'Level 2'),
        ('LEVEL3', 'Level 3'),
        ('LEVEL4', 'Level 4'),
        ('LEVEL5', 'Level 5'),
        ('LEVEL6', 'Level 6'),
    ]

    stock_location = forms.ChoiceField(choices=CABINET_CHOICES)
    stock_loc_level = forms.ChoiceField(choices=LEVEL_CHOICES)

    class Meta:
        model = Inventory
        fields = ['distribution_center', 'product', 'quantity', 'stock_location', 'stock_loc_level']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply the select2 class to the product field
        self.fields['product'].widget.attrs.update({'class': 'select2'})

        # You can also apply select2 to other fields if needed
        self.fields['stock_location'].widget.attrs.update({'class': 'select2'})
        self.fields['stock_loc_level'].widget.attrs.update({'class': 'select2'})

class FilteredCheckoutForm(forms.Form):
    checked_out_by = forms.ModelChoiceField(
        queryset=CheckedOutBy.objects.all(),
        required=False,  # Allows for no selection
        empty_label="Select Name",
        widget=forms.Select(attrs={'class': 'form-control select2'}),  # Explicitly set widget
        label="Filter by Name"  # Label for the dropdown
    )