#!/usr/bin/env python3
"""
Test script to verify authentication functionality
"""

from app import app, db, User, bcrypt
from flask import session

def test_auth():
    """Test authentication functionality"""
    with app.app_context():
        print("🧪 Testing Authentication")
        print("=" * 50)

        # Test user creation
        print("\n1. Testing user creation...")
        try:
            # Clear existing users for testing
            User.query.delete()
            db.session.commit()

            # Create test user
            password_hash = bcrypt.generate_password_hash('test123').decode('utf-8')
            test_user = User(
                username='testuser',
                email='test@example.com',
                password_hash=password_hash
            )
            db.session.add(test_user)
            db.session.commit()
            print("✅ User created successfully")

            # Test password verification
            print("\n2. Testing password verification...")
            user = User.query.filter_by(username='testuser').first()
            if user and bcrypt.check_password_hash(user.password_hash, 'test123'):
                print("✅ Password verification works")
            else:
                print("❌ Password verification failed")

            # Test login simulation
            print("\n3. Testing login simulation...")
            with app.test_client() as client:
                # Test login with correct credentials
                response = client.post('/login', json={
                    'username': 'testuser',
                    'password': 'test123'
                })
                print(f"Login response status: {response.status_code}")
                print(f"Login response data: {response.get_json()}")

                # Test login with wrong password
                response = client.post('/login', json={
                    'username': 'testuser',
                    'password': 'wrongpass'
                })
                print(f"Wrong password response status: {response.status_code}")
                print(f"Wrong password response data: {response.get_json()}")

        except Exception as e:
            print(f"❌ Error during testing: {e}")
            import traceback
            traceback.print_exc()

        print("\n✅ Authentication test completed!")

if __name__ == "__main__":
    test_auth()
