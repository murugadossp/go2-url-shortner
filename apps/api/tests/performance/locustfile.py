"""
Performance tests using Locust
"""
from locust import HttpUser, task, between
import random
import string
import json

class URLShortenerUser(HttpUser):
    """Simulate user behavior for URL shortener"""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Setup user session"""
        self.created_links = []
        self.base_domains = ['go2.video', 'go2.reviews', 'go2.tools']
        
        # Get configuration
        response = self.client.get('/api/config/base-domains')
        if response.status_code == 200:
            self.base_domains = response.json()
    
    @task(5)
    def create_short_link(self):
        """Create a short link (most common operation)"""
        test_urls = [
            'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'https://github.com/microsoft/playwright',
            'https://www.google.com/search?q=test',
            'https://stackoverflow.com/questions/12345',
            'https://www.amazon.com/product/12345',
            'https://docs.python.org/3/',
            'https://www.wikipedia.org/wiki/Test',
            'https://news.ycombinator.com/',
        ]
        
        payload = {
            'long_url': random.choice(test_urls),
            'base_domain': random.choice(self.base_domains)
        }
        
        # 20% chance to add custom code
        if random.random() < 0.2:
            payload['custom_code'] = self.generate_random_code()
        
        # 10% chance to add password
        if random.random() < 0.1:
            payload['password'] = 'testpass123'
        
        with self.client.post(
            '/api/links/shorten',
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.created_links.append(data['code'])
                response.success()
            elif response.status_code == 409:
                # Custom code collision is expected
                response.success()
            else:
                response.failure(f"Unexpected status code: {response.status_code}")
    
    @task(3)
    def redirect_link(self):
        """Access a short link (redirect)"""
        if self.created_links:
            code = random.choice(self.created_links)
            with self.client.get(f'/{code}', allow_redirects=False, catch_response=True) as response:
                if response.status_code in [302, 200]:  # 302 for redirect, 200 for password form
                    response.success()
                else:
                    response.failure(f"Unexpected redirect status: {response.status_code}")
        else:
            # Use a known test link
            with self.client.get('/test123', allow_redirects=False, catch_response=True) as response:
                # Any response is fine for performance testing
                response.success()
    
    @task(2)
    def get_analytics(self):
        """Get analytics for a link"""
        if self.created_links:
            code = random.choice(self.created_links)
            with self.client.get(f'/api/stats/{code}', catch_response=True) as response:
                if response.status_code in [200, 404]:  # 404 is fine if no clicks yet
                    response.success()
                else:
                    response.failure(f"Analytics request failed: {response.status_code}")
    
    @task(1)
    def generate_qr_code(self):
        """Generate QR code for a link"""
        if self.created_links:
            code = random.choice(self.created_links)
            with self.client.get(f'/api/qr/{code}', catch_response=True) as response:
                if response.status_code in [200, 302]:  # 200 for generated, 302 for cached
                    response.success()
                else:
                    response.failure(f"QR generation failed: {response.status_code}")
    
    @task(1)
    def get_config(self):
        """Get configuration (cached endpoint)"""
        with self.client.get('/api/config/base-domains', catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Config request failed: {response.status_code}")
    
    def generate_random_code(self):
        """Generate random custom code"""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

class AdminUser(HttpUser):
    """Simulate admin user behavior"""
    
    wait_time = between(2, 5)
    weight = 1  # Lower weight than regular users
    
    def on_start(self):
        """Setup admin session"""
        # In a real test, you'd authenticate as admin
        self.headers = {'Authorization': 'Bearer admin-test-token'}
    
    @task(3)
    def list_all_links(self):
        """Admin: List all links"""
        with self.client.get('/api/admin/links', headers=self.headers, catch_response=True) as response:
            if response.status_code in [200, 401]:  # 401 if auth is enabled
                response.success()
            else:
                response.failure(f"Admin links request failed: {response.status_code}")
    
    @task(2)
    def list_users(self):
        """Admin: List users"""
        with self.client.get('/api/admin/users', headers=self.headers, catch_response=True) as response:
            if response.status_code in [200, 401]:
                response.success()
            else:
                response.failure(f"Admin users request failed: {response.status_code}")
    
    @task(1)
    def get_system_stats(self):
        """Admin: Get system statistics"""
        with self.client.get('/api/admin/stats', headers=self.headers, catch_response=True) as response:
            if response.status_code in [200, 401]:
                response.success()
            else:
                response.failure(f"Admin stats request failed: {response.status_code}")

class HeavyUser(HttpUser):
    """Simulate heavy usage patterns"""
    
    wait_time = between(0.5, 1)  # Faster requests
    weight = 1  # Lower weight
    
    @task(10)
    def rapid_link_creation(self):
        """Create links rapidly"""
        payload = {
            'long_url': f'https://example.com/page/{random.randint(1, 10000)}',
            'base_domain': 'go2.tools'
        }
        
        with self.client.post('/api/links/shorten', json=payload, catch_response=True) as response:
            if response.status_code in [200, 429]:  # 429 for rate limiting
                response.success()
            else:
                response.failure(f"Rapid creation failed: {response.status_code}")
    
    @task(5)
    def concurrent_redirects(self):
        """Test concurrent redirects"""
        code = f'test{random.randint(1, 100)}'
        with self.client.get(f'/{code}', allow_redirects=False, catch_response=True) as response:
            # Any response is fine for load testing
            response.success()

# Custom test scenarios
class StressTestUser(HttpUser):
    """Stress test with edge cases"""
    
    wait_time = between(0.1, 0.5)  # Very fast requests
    weight = 1
    
    @task
    def stress_test_endpoints(self):
        """Stress test various endpoints"""
        endpoints = [
            '/api/config/base-domains',
            '/api/stats/nonexistent',
            '/api/qr/nonexistent',
            '/nonexistent-link',
        ]
        
        endpoint = random.choice(endpoints)
        with self.client.get(endpoint, catch_response=True) as response:
            # Accept any response for stress testing
            response.success()

# Performance test configuration
class WebsiteUser(HttpUser):
    """Test the complete user journey"""
    
    wait_time = between(2, 8)  # Realistic user behavior
    
    def on_start(self):
        """User starts session"""
        # Get initial page (would be frontend in real scenario)
        self.client.get('/api/config/base-domains')
    
    @task
    def complete_user_journey(self):
        """Complete user journey: create -> click -> analytics"""
        
        # Step 1: Create link
        payload = {
            'long_url': 'https://www.example.com/test-page',
            'base_domain': 'go2.tools'
        }
        
        response = self.client.post('/api/links/shorten', json=payload)
        if response.status_code == 200:
            data = response.json()
            code = data['code']
            
            # Step 2: Click the link (simulate user clicking)
            self.client.get(f'/{code}', allow_redirects=False)
            
            # Step 3: View analytics
            self.client.get(f'/api/stats/{code}')
            
            # Step 4: Generate QR code
            self.client.get(f'/api/qr/{code}')

if __name__ == '__main__':
    # Run with: locust -f locustfile.py --host=http://localhost:8000
    pass