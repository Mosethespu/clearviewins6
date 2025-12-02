"""
Seed the database with default premium rates for all insurance companies.
Run this script after creating insurance companies.
"""
from app import app, db
from models import InsuranceCompany, PremiumRate

def seed_premium_rates():
	"""Seed default premium rates for all insurance companies"""
	with app.app_context():
		# Get all active insurance companies
		companies = InsuranceCompany.query.filter_by(is_active=True).all()
		
		if not companies:
			print("❌ No insurance companies found in database.")
			print("Please create insurance companies first.")
			return
		
		print(f"✓ Found {len(companies)} insurance companies")
		
		# Default rate configurations for each cover type
		rate_configs = {
			'Comprehensive': {
				'comprehensive_min_rate': 4.0,
				'comprehensive_max_rate': 7.0,
				'comprehensive_default_rate': 5.5,
				'tpo_flat_rate': 0.0,
				'tpft_base_rate': 0.0,
				'tpft_percentage': 0.0,
				'psv_taxi_rate': 0.0,
				'psv_matatu_14_rate': 0.0,
				'psv_matatu_25_rate': 0.0,
				'psv_bus_rate': 0.0
			},
			'Third-Party Only': {
				'comprehensive_min_rate': 0.0,
				'comprehensive_max_rate': 0.0,
				'comprehensive_default_rate': 0.0,
				'tpo_flat_rate': 8000.0,  # KES 8,000
				'tpft_base_rate': 0.0,
				'tpft_percentage': 0.0,
				'psv_taxi_rate': 0.0,
				'psv_matatu_14_rate': 0.0,
				'psv_matatu_25_rate': 0.0,
				'psv_bus_rate': 0.0
			},
			'Third-Party Fire & Theft': {
				'comprehensive_min_rate': 0.0,
				'comprehensive_max_rate': 0.0,
				'comprehensive_default_rate': 0.0,
				'tpo_flat_rate': 0.0,
				'tpft_base_rate': 8000.0,  # Base TPO rate
				'tpft_percentage': 1.5,  # Additional 1.5% of vehicle value
				'psv_taxi_rate': 0.0,
				'psv_matatu_14_rate': 0.0,
				'psv_matatu_25_rate': 0.0,
				'psv_bus_rate': 0.0
			},
			'PSV': {
				'comprehensive_min_rate': 0.0,
				'comprehensive_max_rate': 0.0,
				'comprehensive_default_rate': 0.0,
				'tpo_flat_rate': 0.0,
				'tpft_base_rate': 0.0,
				'tpft_percentage': 0.0,
				'psv_taxi_rate': 25000.0,  # KES 25,000 for taxis
				'psv_matatu_14_rate': 70000.0,  # KES 70,000 for 14-seater matatus
				'psv_matatu_25_rate': 95000.0,  # KES 95,000 for 25-seater matatus
				'psv_bus_rate': 135000.0  # KES 135,000 for buses
			}
		}
		
		# Counter for rates created
		rates_created = 0
		rates_skipped = 0
		
		for company in companies:
			print(f"\n📋 Processing: {company.name}")
			
			for cover_type, config in rate_configs.items():
				# Check if rate already exists
				existing_rate = PremiumRate.query.filter_by(
					insurance_company_id=company.id,
					cover_type=cover_type
				).first()
				
				if existing_rate:
					print(f"  ⏭  Skipped {cover_type} (already exists)")
					rates_skipped += 1
					continue
				
				# Create new rate
				new_rate = PremiumRate(
					insurance_company_id=company.id,
					cover_type=cover_type,
					comprehensive_min_rate=config['comprehensive_min_rate'],
					comprehensive_max_rate=config['comprehensive_max_rate'],
					comprehensive_default_rate=config['comprehensive_default_rate'],
					tpo_flat_rate=config['tpo_flat_rate'],
					tpft_base_rate=config['tpft_base_rate'],
					tpft_percentage=config['tpft_percentage'],
					psv_taxi_rate=config['psv_taxi_rate'],
					psv_matatu_14_rate=config['psv_matatu_14_rate'],
					psv_matatu_25_rate=config['psv_matatu_25_rate'],
					psv_bus_rate=config['psv_bus_rate'],
					is_active=True
				)
				
				db.session.add(new_rate)
				rates_created += 1
				print(f"  ✓ Created {cover_type}")
		
		# Commit all changes
		try:
			db.session.commit()
			print(f"\n✅ Successfully seeded premium rates!")
			print(f"   Created: {rates_created} rates")
			print(f"   Skipped: {rates_skipped} rates (already existed)")
		except Exception as e:
			db.session.rollback()
			print(f"\n❌ Error seeding rates: {str(e)}")

if __name__ == '__main__':
	seed_premium_rates()
