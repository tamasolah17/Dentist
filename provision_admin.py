"""Create a login for an already configured clinic.
Usage: python provision_admin.py <clinic_id> <email>
The password is prompted securely; do not pass it on the command line.
"""
import getpass
from clinics import DB_PATH, get_clinic
from clinic_admin import create_clinic_admin

clinic_id = input("Clinic ID: ").strip()
email = input("Admin e-mail: ").strip()
get_clinic(clinic_id)  # Fail if this clinic has not been configured yet.
password = getpass.getpass("Jelszó (minimum 12 karakter): ")
create_clinic_admin(DB_PATH, clinic_id, email, password)
print("Admin hozzáférés létrehozva.")
