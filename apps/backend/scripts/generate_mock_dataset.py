import csv
import random
import os
from faker import Faker
from datetime import datetime, timedelta

def generate_dataset(num_records=50000, output_path="apps/backend/data/mock_aadhaar_dataset.csv"):
    fake = Faker('en_IN')
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    print(f"Generating {num_records} mock Aadhaar records...")
    
    with open(output_path, mode='w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'aadhaar_number', 'name', 'dob', 'gender', 
            'care_of', 'address', 'phone_number', 'photo_url'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for i in range(num_records):
            # Aadhaar is 12 digits
            aadhaar_number = f"{random.randint(1000, 9999)}{random.randint(1000, 9999)}{random.randint(1000, 9999)}"
            gender = random.choice(['M', 'F'])
            
            # Generate DOB (adults)
            start_date = datetime.now() - timedelta(days=365 * 65)
            end_date = datetime.now() - timedelta(days=365 * 18)
            dob_date = fake.date_between(start_date=start_date, end_date=end_date)
            dob = dob_date.strftime("%d-%m-%Y")
            
            name = fake.name_male() if gender == 'M' else fake.name_female()
            care_of = fake.name_male() # usually Father or Husband
            
            address = fake.address().replace('\n', ', ')
            phone_number = fake.phone_number()
            photo_url = f"https://mock-kyc-bucket.s3.ap-south-1.amazonaws.com/photos/{aadhaar_number}.jpg"
            
            row = {
                'aadhaar_number': aadhaar_number,
                'name': name,
                'dob': dob,
                'gender': gender,
                'care_of': care_of,
                'address': address,
                'phone_number': phone_number,
                'photo_url': photo_url
            }
            writer.writerow(row)
            
            if (i+1) % 10000 == 0:
                print(f"[{i+1}/{num_records}] records generated.")
                
    print(f"Dataset generation complete! Saved to {output_path}")

if __name__ == "__main__":
    generate_dataset()
