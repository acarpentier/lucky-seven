from django.test import TestCase
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models import Affiliate, Click


class AffiliateModelTest(TestCase):
    """Test cases for the Affiliate model"""
    
    def setUp(self):
        """Set up test data"""
        self.affiliate_data = {
            'encoded_value': '32L4XJL',
            'payout_target': Decimal('1000.00'),
            'conversion_ratio_target': Decimal('0.0250'),
            'conversion_ratio_deviance': Decimal('0.0050'),
            'daily_revenue_deviance': Decimal('0.0100'),
            'geos': ['US', 'UK', 'DE'],
            'sub1_type_generate': 'lambda: str(random.randint(100000, 999999))',
            'sub2_type_generate': 'lambda: "".join(random.choices(string.ascii_lowercase + string.digits, k=32))'
        }
    
    def test_affiliate_creation(self):
        """Test creating an affiliate with valid data"""
        affiliate = Affiliate.objects.create(**self.affiliate_data)
        
        self.assertEqual(affiliate.encoded_value, '32L4XJL')
        self.assertEqual(affiliate.payout_target, Decimal('1000.00'))
        self.assertEqual(affiliate.conversion_ratio_target, Decimal('0.0250'))
        self.assertEqual(affiliate.conversion_ratio_deviance, Decimal('0.0050'))
        self.assertEqual(affiliate.daily_revenue_deviance, Decimal('0.0100'))
        self.assertEqual(affiliate.geos, ['US', 'UK', 'DE'])
        self.assertIsNotNone(affiliate.created_at)
        self.assertIsNotNone(affiliate.updated_at)
    
    def test_affiliate_str_representation(self):
        """Test the string representation of affiliate"""
        affiliate = Affiliate.objects.create(**self.affiliate_data)
        expected = f"Affiliate {affiliate.encoded_value}"
        self.assertEqual(str(affiliate), expected)
    
    def test_encoded_value_unique(self):
        """Test that encoded_value must be unique"""
        Affiliate.objects.create(**self.affiliate_data)
        
        with self.assertRaises(Exception):  # IntegrityError
            Affiliate.objects.create(**self.affiliate_data)
    
    def test_geos_must_be_list(self):
        """Test that geos field must be a list"""
        invalid_data = self.affiliate_data.copy()
        invalid_data['geos'] = "not_a_list"
        
        affiliate = Affiliate(**invalid_data)
        with self.assertRaises(ValidationError):
            affiliate.full_clean()
    
    def test_sub1_lambda_validation(self):
        """Test that sub1_type_generate lambda is validated"""
        invalid_data = self.affiliate_data.copy()
        invalid_data['sub1_type_generate'] = 'invalid_lambda_syntax'
        
        affiliate = Affiliate(**invalid_data)
        with self.assertRaises(ValidationError):
            affiliate.full_clean()
    
    def test_sub2_lambda_validation(self):
        """Test that sub2_type_generate lambda is validated"""
        invalid_data = self.affiliate_data.copy()
        invalid_data['sub2_type_generate'] = 'invalid_lambda_syntax'
        
        affiliate = Affiliate(**invalid_data)
        with self.assertRaises(ValidationError):
            affiliate.full_clean()
    
    def test_sub1_lambda_must_return_string(self):
        """Test that sub1 lambda must return a string"""
        invalid_data = self.affiliate_data.copy()
        invalid_data['sub1_type_generate'] = 'lambda: 123'  # Returns int, not string
        
        affiliate = Affiliate(**invalid_data)
        with self.assertRaises(ValidationError):
            affiliate.full_clean()
    
    def test_sub2_lambda_must_return_string(self):
        """Test that sub2 lambda must return a string"""
        invalid_data = self.affiliate_data.copy()
        invalid_data['sub2_type_generate'] = 'lambda: 123'  # Returns int, not string
        
        affiliate = Affiliate(**invalid_data)
        with self.assertRaises(ValidationError):
            affiliate.full_clean()
    
    def test_generate_sub1(self):
        """Test the generate_sub1 method"""
        affiliate = Affiliate.objects.create(**self.affiliate_data)
        result = affiliate.generate_sub1()
        
        self.assertIsInstance(result, str)
        self.assertTrue(result.isdigit())
        self.assertEqual(len(result), 6)  # Should be 6 digits based on lambda
    
    def test_generate_sub2(self):
        """Test the generate_sub2 method"""
        affiliate = Affiliate.objects.create(**self.affiliate_data)
        result = affiliate.generate_sub2()
        
        self.assertIsInstance(result, str)
        self.assertEqual(len(result), 32)  # Should be 32 characters based on lambda
    
    def test_updated_at_changes_on_save(self):
        """Test that updated_at changes when model is saved"""
        affiliate = Affiliate.objects.create(**self.affiliate_data)
        original_updated_at = affiliate.updated_at
        
        # Wait a small amount and save again
        import time
        time.sleep(0.001)
        affiliate.payout_target = Decimal('2000.00')
        affiliate.save()
        
        self.assertGreater(affiliate.updated_at, original_updated_at)
    
    def test_decimal_field_precision(self):
        """Test decimal field precision"""
        affiliate = Affiliate.objects.create(**self.affiliate_data)
        
        # Test that decimal precision is maintained
        affiliate.conversion_ratio_target = Decimal('0.1234')
        affiliate.save()
        
        affiliate.refresh_from_db()
        self.assertEqual(affiliate.conversion_ratio_target, Decimal('0.1234'))


class ClickModelTest(TestCase):
    """Test cases for the Click model"""
    
    def setUp(self):
        """Set up test data"""
        self.click_data = {
            'affiliate_id': 'AFF001',
            'affiliate_encoded_value': '32L4XJL',
            'ip_address': '192.168.1.1',
            'user_agent': 'Mozilla/5.0 Test Browser',
            'language': 'en-US',
            'sub1': 'test_sub1',
            'sub2': 'test_sub2'
        }
    
    def test_click_creation(self):
        """Test creating a click with valid data"""
        click = Click.objects.create(**self.click_data)
        
        self.assertEqual(click.affiliate_id, 'AFF001')
        self.assertEqual(click.affiliate_encoded_value, '32L4XJL')
        self.assertEqual(click.ip_address, '192.168.1.1')
        self.assertFalse(click.to_process)
        self.assertFalse(click.is_processed)
        self.assertFalse(click.to_convert)
        self.assertFalse(click.is_converted)
    
    def test_click_str_representation(self):
        """Test the string representation of click"""
        click = Click.objects.create(**self.click_data)
        expected = f"Click {click.id} - {click.affiliate_id}"
        self.assertEqual(str(click), expected)
    
    def test_ip_address_unique(self):
        """Test that ip_address must be unique"""
        Click.objects.create(**self.click_data)
        
        duplicate_data = self.click_data.copy()
        duplicate_data['affiliate_id'] = 'AFF002'
        
        with self.assertRaises(Exception):  # IntegrityError
            Click.objects.create(**duplicate_data)
    
    def test_updated_at_changes_on_save(self):
        """Test that updated_at changes when model is saved"""
        click = Click.objects.create(**self.click_data)
        original_updated_at = click.updated_at
        
        # Wait a small amount and save again
        import time
        time.sleep(0.001)
        click.to_process = True
        click.save()
        
        self.assertGreater(click.updated_at, original_updated_at)


class ModelIntegrationTest(TestCase):
    """Integration tests for models working together"""
    
    def test_affiliate_and_click_relationship(self):
        """Test that affiliate and click models can work together"""
        # Create affiliate
        affiliate = Affiliate.objects.create(
            encoded_value='32L4XJL',
            payout_target=Decimal('1000.00'),
            conversion_ratio_target=Decimal('0.0250'),
            conversion_ratio_deviance=Decimal('0.0050'),
            daily_revenue_deviance=Decimal('0.0100'),
            geos=['US', 'UK'],
            sub1_type_generate='lambda: str(random.randint(100000, 999999))',
            sub2_type_generate='lambda: "".join(random.choices(string.ascii_lowercase + string.digits, k=32))'
        )
        
        # Create click with affiliate data
        click = Click.objects.create(
            affiliate_id='AFF001',
            affiliate_encoded_value=affiliate.encoded_value,
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0 Test Browser',
            language='en-US',
            sub1=affiliate.generate_sub1(),
            sub2=affiliate.generate_sub2()
        )
        
        self.assertEqual(click.affiliate_encoded_value, affiliate.encoded_value)
        self.assertIsNotNone(click.sub1)
        self.assertIsNotNone(click.sub2)
        self.assertEqual(len(click.sub1), 6)  # Based on sub1 lambda
        self.assertEqual(len(click.sub2), 32)  # Based on sub2 lambda
